from datetime import datetime
from typing import Sequence
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit, MemoryType

router = APIRouter(prefix="/api/memory", tags=["Memory"])


class MemorySearchRequest(BaseModel):
    query: str
    k: int = 8
    types: Sequence[MemoryType] | None = None
    since: datetime | None = None


@router.post("/search", response_model=list[MemoryHit])
async def search_memories(
    request: MemorySearchRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Search for memories belonging to the authenticated company.
    """
    embedding_service = BedrockClient()
    repository = MemoryRepository(embedding_service=embedding_service)

    try:
        results = await repository.search(
            company_id=company_id,
            query=request.query,
            k=request.k,
            types=request.types,
            since=request.since,
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
