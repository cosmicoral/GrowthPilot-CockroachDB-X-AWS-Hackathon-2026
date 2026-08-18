from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.agents.analytics_reflection import (
    AnalyticsReflectionAgent,
    AnalyticsReflectionOutput,
)
from backend.agents.context import AgentContext
from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


class AnalyticsRunRequest(BaseModel):
    group_by: Literal["theme", "icp", "messaging_angle"] = "theme"


def _repository() -> MemoryRepository:
    bedrock = BedrockClient()
    return MemoryRepository(
        embedding_service=BedrockEmbeddingService(bedrock),
    )


@router.get("/latest", response_model=MemoryHit | None)
async def get_latest_reflection(
    company_id: UUID = Depends(get_current_company_id),
):
    """Return the newest saved analytics reflection for this company."""
    memories = await _repository().recent(
        company_id=company_id,
        memory_type="reflection",
        limit=50,
    )
    return next(
        (
            memory
            for memory in memories
            if memory.metadata.get("source")
            in {"analytics-reflection-agent", "reflection-agent"}
        ),
        None,
    )


@router.post("/reflection", response_model=AnalyticsReflectionOutput)
async def run_analytics_reflection(
    request: AnalyticsRunRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """Analyze simulated campaign memories and persist a reflection."""
    bedrock = BedrockClient()
    repository = MemoryRepository(
        embedding_service=BedrockEmbeddingService(bedrock),
    )
    agent = AnalyticsReflectionAgent(
        AgentContext(
            company_id=company_id,
            bedrock_client=bedrock,
            memory_repository=repository,
        )
    )
    result = await agent.run(group_by=request.group_by)
    if not result.success or not isinstance(
        result.output,
        AnalyticsReflectionOutput,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Analytics reflection failed: {result.output}",
        )
    return result.output
