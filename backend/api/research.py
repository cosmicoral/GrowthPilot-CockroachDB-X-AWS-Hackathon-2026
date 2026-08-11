import logging
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.deps import get_current_company_id
from backend.agents.context import AgentContext
from backend.agents.market_research import MarketResearchAgent
from backend.database.database import database
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit

router = APIRouter(prefix="/api/research", tags=["Research"])
logger = logging.getLogger(__name__)


class ResearchRunRequest(BaseModel):
    trigger: Literal["onboarding", "manual", "periodic"] = Field(
        default="manual",
        description="Trigger source for the research run",
    )
    custom_research_text: Optional[str] = Field(
        default=None,
        description="Optional external research text override",
    )


class ResearchRunResponse(BaseModel):
    agent_name: str
    success: bool
    output: dict
    metadata: dict = Field(default_factory=dict)


@router.post("/run", response_model=ResearchRunResponse)
async def run_market_research(
    request: ResearchRunRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Trigger the Market Research Agent pipeline for the authenticated company.
    Executes fetch -> structure -> dedup -> embed -> persist.
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

    company_profile = dict(row)

    bedrock_client = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock_client)
    repository = MemoryRepository(embedding_service=embedding_service)

    context = AgentContext(
        company_id=company_id,
        bedrock_client=bedrock_client,
        memory_repository=repository,
    )

    agent = MarketResearchAgent(context)

    result = await agent.run(
        company_profile=company_profile,
        custom_research_text=request.custom_research_text,
        trigger_source=request.trigger,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market research execution failed: {result.output}",
        )

    return ResearchRunResponse(
        agent_name=result.agent_name,
        success=result.success,
        output=result.output if isinstance(result.output, dict) else {"details": str(result.output)},
        metadata=result.metadata,
    )


@router.get("/memories", response_model=list[MemoryHit])
async def get_research_memories(
    limit: int = 20,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Retrieve stored market research memories for the authenticated company.
    """
    embedding_service = BedrockEmbeddingService(BedrockClient())
    repository = MemoryRepository(embedding_service=embedding_service)

    try:
        memories = await repository.recent(
            company_id=company_id,
            memory_type="semantic",
            limit=max(limit * 2, 20),
        )

        research_memories = [
            m for m in memories
            if m.metadata and m.metadata.get("source") == "market_research"
        ]

        return research_memories[:limit]
    except Exception as exc:
        logger.error("Failed to retrieve research memories: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve research memories",
        )
