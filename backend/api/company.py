from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import get_current_company_id
from backend.database.database import database
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository

router = APIRouter(prefix="/api/company", tags=["Company"])


class CompanyProfile(BaseModel):
    id: UUID
    name: str
    email: str
    website: str | None = None
    industry: str | None = None
    description: str | None = None


class OnboardingRequest(BaseModel):
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    ideal_customer: str = Field(default="", max_length=2000)
    three_month_goal: str = Field(default="", max_length=2000)
    previous_attempts: str = Field(default="", max_length=3000)
    current_channels: str = Field(default="", max_length=1000)


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@router.get("/me", response_model=CompanyProfile)
async def get_my_company(
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Get the profile of the currently authenticated company.
    """
    query = """
    SELECT id, name, email, website, industry, description
    FROM companies
    WHERE id = $1;
    """
    async with database.acquire() as conn:
        row = await conn.fetchrow(query, company_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return CompanyProfile(**dict(row))


@router.post("/onboarding", response_model=CompanyProfile)
async def complete_onboarding(
    request: OnboardingRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """Update the company profile and seed founder context as typed memories."""
    query = """
    UPDATE companies
    SET website = $2, industry = $3, description = $4
    WHERE id = $1
    RETURNING id, name, email, website, industry, description;
    """
    async with database.acquire() as conn:
        row = await conn.fetchrow(
            query,
            company_id,
            _optional_text(request.website),
            _optional_text(request.industry),
            _optional_text(request.description),
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    memory_specs = [
        ("user", "Ideal customer", request.ideal_customer, 0.9),
        ("user", "Three-month goal", request.three_month_goal, 0.9),
        ("episodic", "Previous attempts and outcomes", request.previous_attempts, 0.75),
        ("user", "Current growth channels", request.current_channels, 0.8),
    ]
    repository = MemoryRepository(
        embedding_service=BedrockEmbeddingService(BedrockClient()),
    )

    try:
        for memory_type, label, value, importance in memory_specs:
            if not value.strip():
                continue
            await repository.write(
                company_id=company_id,
                memory_type=memory_type,
                content=f"{label}: {value.strip()}",
                metadata={"source": "founder_onboarding", "field": label},
                importance=importance,
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Company profile was saved, but founder memories could not be embedded. "
                "Retry onboarding after checking Bedrock embedding access."
            ),
        ) from exc

    return CompanyProfile(**dict(row))
