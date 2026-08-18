from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryType

router = APIRouter(
    prefix="/api/growthgraph",
    tags=["GrowthGraph"],
)


class GrowthGraphInsightsRequest(BaseModel):
    query: str = Field(min_length=1)
    company_ids: list[UUID] = Field(min_length=1)
    k: int = Field(default=20, ge=1, le=100)
    types: Sequence[MemoryType] | None = None


class GrowthGraphInsight(BaseModel):
    memory_type: MemoryType
    content: str
    metadata: dict
    importance: float
    similarity: float | None


class GrowthGraphInsightsResponse(BaseModel):
    company_count: int
    results: list[GrowthGraphInsight]


@router.post(
    "/insights",
    response_model=GrowthGraphInsightsResponse,
)
async def growthgraph_insights(
    request: GrowthGraphInsightsRequest,
    _: UUID = Depends(get_current_company_id),
):
    """
    Retrieve anonymized memory insights across an explicitly
    selected set of companies.
    """

    embedding_service = BedrockEmbeddingService(BedrockClient())
    repository = MemoryRepository(
        embedding_service=embedding_service,
    )

    try:
        results = await repository.search_across_companies(
            company_ids=request.company_ids,
            query=request.query,
            k=request.k,
            types=request.types,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return GrowthGraphInsightsResponse(
        company_count=len(request.company_ids),
        results=[
            GrowthGraphInsight(
                memory_type=memory.memory_type,
                content=memory.content,
                metadata=memory.metadata,
                importance=memory.importance,
                similarity=memory.similarity,
            )
            for memory in results
        ],
    )