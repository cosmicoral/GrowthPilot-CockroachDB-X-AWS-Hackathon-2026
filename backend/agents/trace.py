"""
Agent Tracing Repository.

Stores and queries agent execution traces for observability.
Uses asyncpg directly to interface with CockroachDB.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from pydantic import BaseModel, Field

from backend.database.database import database, run_in_txn

logger = logging.getLogger(__name__)


class AgentTraceHit(BaseModel):
    """
    Representation of a recorded agent execution trace.
    """
    id: UUID
    company_id: UUID
    agent_name: str
    start_time: datetime
    duration_ms: float
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    memories_retrieved: List[Dict[str, Any]] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


INSERT_TRACE_SQL = """
INSERT INTO agent_traces (
    company_id,
    agent_name,
    start_time,
    duration_ms,
    input,
    output,
    memories_retrieved,
    success,
    error,
    metadata
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
RETURNING id;
"""

SELECT_RECENT_TRACES_SQL = """
SELECT
    id,
    company_id,
    agent_name,
    start_time,
    duration_ms,
    input,
    output,
    memories_retrieved,
    success,
    error,
    metadata,
    created_at
FROM agent_traces
WHERE company_id = $1
AND ($2::STRING IS NULL OR agent_name = $2)
ORDER BY created_at DESC
LIMIT $3;
"""

SELECT_TRACE_BY_ID_SQL = """
SELECT
    id,
    company_id,
    agent_name,
    start_time,
    duration_ms,
    input,
    output,
    memories_retrieved,
    success,
    error,
    metadata,
    created_at
FROM agent_traces
WHERE company_id = $1
AND id = $2;
"""


class TraceRepository:
    """
    Persistence layer for agent traces.
    """

    async def save_trace(
        self,
        *,
        company_id: UUID,
        agent_name: str,
        start_time: datetime,
        duration_ms: float,
        input: Dict[str, Any] | None = None,
        output: Dict[str, Any] | None = None,
        memories_retrieved: List[Dict[str, Any]] | None = None,
        success: bool = True,
        error: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Optional[UUID]:
        """
        Save an agent execution trace. Handles database errors gracefully without throwing.
        """
        try:
            async def transaction(connection: asyncpg.Connection):
                return await connection.fetchval(
                    INSERT_TRACE_SQL,
                    company_id,
                    agent_name,
                    start_time,
                    duration_ms,
                    input or {},
                    output or {},
                    memories_retrieved or [],
                    success,
                    error,
                    metadata or {},
                )

            return await run_in_txn(transaction)
        except Exception as exc:
            logger.warning(
                "Failed to persist agent trace for company %s agent %s: %s",
                company_id,
                agent_name,
                exc,
            )
            return None

    async def get_recent_traces(
        self,
        *,
        company_id: UUID,
        agent_name: str | None = None,
        limit: int = 50,
    ) -> List[AgentTraceHit]:
        """
        Retrieve recent traces for a company.
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")

        async with database.acquire() as connection:
            rows = await connection.fetch(
                SELECT_RECENT_TRACES_SQL,
                company_id,
                agent_name,
                limit,
            )

        return [self._to_agent_trace_hit(row) for row in rows]

    async def get_trace_by_id(
        self,
        *,
        company_id: UUID,
        trace_id: UUID,
    ) -> Optional[AgentTraceHit]:
        """
        Fetch a single trace by ID.
        """
        async with database.acquire() as connection:
            row = await connection.fetchrow(
                SELECT_TRACE_BY_ID_SQL,
                company_id,
                trace_id,
            )

        if not row:
            return None
        return self._to_agent_trace_hit(row)

    @staticmethod
    def _to_agent_trace_hit(row) -> AgentTraceHit:
        data = dict(row)
        return AgentTraceHit(
            id=data["id"],
            company_id=data["company_id"],
            agent_name=data["agent_name"],
            start_time=data["start_time"],
            duration_ms=data["duration_ms"],
            input=data.get("input") or {},
            output=data.get("output") or {},
            memories_retrieved=data.get("memories_retrieved") or [],
            success=data["success"],
            error=data.get("error"),
            metadata=data.get("metadata") or {},
            created_at=data["created_at"],
        )
