from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit

router = APIRouter(
    prefix="/api/growthgraph",
    tags=["GrowthGraph"],
)

# GrowthGraph only searches the deterministic, explicitly allowlisted T35
# cohort. Tenant IDs are derived server-side and are never accepted from the
# request or returned in the response.
GROWTHGRAPH_NAMESPACE = UUID(
    "f2f5f2a0-6b8b-4b8e-9f4b-9d3f6b1c2e40"
)
GROWTHGRAPH_COHORT_SIZE = 75
SEARCH_RESULT_LIMIT = 100
MIN_MATCHED_FOUNDERS = 3
MAX_INSIGHTS = 3

SAFE_THEMES = {
    "product_education": "Product education",
    "founder_story": "Founder story",
    "customer_case_study": "Customer case study",
    "industry_trend": "Industry trend",
    "tactical_howto": "Tactical how-to",
    "pricing_positioning": "Pricing and positioning",
}


def derive_growthgraph_company_id(index: int) -> UUID:
    """Return one deterministic company ID from the T35 cohort."""

    return uuid5(
        GROWTHGRAPH_NAMESPACE,
        f"growthgraph-synthetic-founder-{index}",
    )


GROWTHGRAPH_COMPANY_IDS = tuple(
    derive_growthgraph_company_id(index)
    for index in range(GROWTHGRAPH_COHORT_SIZE)
)


class GrowthGraphInsightsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=500)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Query must not be blank")
        return stripped


class GrowthGraphInsight(BaseModel):
    theme: str
    summary: str
    matched_founders: int
    cohort_size: int
    prevalence: float
    average_similarity: float | None


class GrowthGraphInsightsResponse(BaseModel):
    query: str
    cohort_size: int
    generated_at: datetime
    insight: str | None
    insights: list[GrowthGraphInsight]


def aggregate_insights(
    hits: list[MemoryHit],
) -> list[GrowthGraphInsight]:
    """Convert private per-company rows into disclosure-safe aggregates."""

    theme_scores: dict[str, dict[UUID, float | None]] = {}

    for hit in hits:
        theme = hit.metadata.get("theme")
        if theme not in SAFE_THEMES:
            continue

        company_scores = theme_scores.setdefault(theme, {})
        existing = company_scores.get(hit.company_id)

        if existing is None or (
            hit.similarity is not None
            and hit.similarity > existing
        ):
            company_scores[hit.company_id] = hit.similarity

    candidates: list[GrowthGraphInsight] = []
    for theme, company_scores in theme_scores.items():
        matched_founders = len(company_scores)
        if matched_founders < MIN_MATCHED_FOUNDERS:
            continue

        similarities = [
            score
            for score in company_scores.values()
            if score is not None
        ]
        average_similarity = (
            round(sum(similarities) / len(similarities), 4)
            if similarities
            else None
        )
        label = SAFE_THEMES[theme]
        summary = (
            f"{label} appears in relevant content from "
            f"{matched_founders} of {GROWTHGRAPH_COHORT_SIZE} founders."
        )

        candidates.append(
            GrowthGraphInsight(
                theme=label,
                summary=summary,
                matched_founders=matched_founders,
                cohort_size=GROWTHGRAPH_COHORT_SIZE,
                prevalence=round(
                    matched_founders / GROWTHGRAPH_COHORT_SIZE,
                    4,
                ),
                average_similarity=average_similarity,
            )
        )

    return sorted(
        candidates,
        key=lambda item: (
            -item.matched_founders,
            -(
                item.average_similarity
                if item.average_similarity is not None
                else -1.0
            ),
            item.theme,
        ),
    )[:MAX_INSIGHTS]


@router.post(
    "/insights",
    response_model=GrowthGraphInsightsResponse,
)
async def growthgraph_insights(
    request: GrowthGraphInsightsRequest,
    _: UUID = Depends(get_current_company_id),
):
    """Return aggregate patterns from the allowlisted founder cohort."""

    embedding_service = BedrockEmbeddingService(BedrockClient())
    repository = MemoryRepository(
        embedding_service=embedding_service,
    )

    try:
        hits = await repository.search_across_companies(
            company_ids=GROWTHGRAPH_COMPANY_IDS,
            query=request.query,
            k=SEARCH_RESULT_LIMIT,
            types=("episodic",),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    insights = aggregate_insights(hits)

    return GrowthGraphInsightsResponse(
        query=request.query,
        cohort_size=GROWTHGRAPH_COHORT_SIZE,
        generated_at=datetime.now(timezone.utc),
        insight=insights[0].summary if insights else None,
        insights=insights,
    )
