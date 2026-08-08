from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.deps import get_current_company_id
from backend.database.database import database

router = APIRouter(prefix="/api/company", tags=["Company"])


class CompanyProfile(BaseModel):
    id: UUID
    name: str
    email: str
    website: str | None = None
    industry: str | None = None
    description: str | None = None


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
