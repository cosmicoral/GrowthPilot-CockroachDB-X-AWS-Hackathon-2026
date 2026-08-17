import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.agents.trace import AgentTraceHit, TraceRepository
from backend.api.deps import get_current_company_id

router = APIRouter(prefix="/api/traces", tags=["Traces"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[AgentTraceHit])
async def list_agent_traces(
    agent_name: Optional[str] = None,
    limit: int = 50,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Retrieve recent agent execution traces for the authenticated company.
    """
    repository = TraceRepository()
    try:
        traces = await repository.get_recent_traces(
            company_id=company_id,
            agent_name=agent_name,
            limit=limit,
        )
        return traces
    except Exception as exc:
        logger.error("Failed to retrieve agent traces for company %s: %s", company_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent execution traces",
        )


@router.get("/{trace_id}", response_model=AgentTraceHit)
async def get_agent_trace(
    trace_id: UUID,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Retrieve a specific agent trace detail by ID for the authenticated company.
    """
    repository = TraceRepository()
    trace = await repository.get_trace_by_id(
        company_id=company_id,
        trace_id=trace_id,
    )

    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent trace not found",
        )

    return trace
