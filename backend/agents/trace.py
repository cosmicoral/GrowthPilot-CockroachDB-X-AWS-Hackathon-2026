"""
Agent Tracing Repository.

Stores and queries agent execution traces for observability.
Uses asyncpg directly to interface with CockroachDB.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from backend.database.database import (
    database,
    fetch_one,
    fetch_value,
    run_in_txn,
)

logger = logging.getLogger(__name__)

REDACTED_VALUE = "[REDACTED]"
MAX_NESTING_DEPTH = 8
MAX_COLLECTION_ITEMS = 100


def _positive_int_env(name: str, default: int, *, minimum: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError:
        logger.warning("Invalid %s=%r; using %s", name, raw_value, default)
        return default
    if value < minimum:
        logger.warning("%s must be >= %s; using %s", name, minimum, default)
        return default
    return value


TRACE_MAX_PAYLOAD_CHARS = _positive_int_env(
    "TRACE_MAX_PAYLOAD_CHARS",
    20_000,
    minimum=1_000,
)
TRACE_MAX_STRING_CHARS = _positive_int_env(
    "TRACE_MAX_STRING_CHARS",
    8_000,
    minimum=256,
)
TRACE_MAX_MEMORIES = _positive_int_env(
    "TRACE_MAX_MEMORIES",
    20,
    minimum=1,
)
TRACE_MAX_ERROR_CHARS = 2_000

SENSITIVE_KEY_WORDS = {
    "authorization",
    "cookie",
    "password",
    "passwd",
    "secret",
}
SENSITIVE_NORMALIZED_KEYS = {
    "apikey",
    "accesstoken",
    "authtoken",
    "bearertoken",
    "refreshtoken",
    "sessionid",
    "sessiontoken",
    "token",
}


def _is_sensitive_key(key: object) -> bool:
    text = str(key).casefold()
    words = set(filter(None, re.split(r"[^a-z0-9]+", text)))
    normalized = re.sub(r"[^a-z0-9]", "", text)
    return bool(words & SENSITIVE_KEY_WORDS) or normalized in SENSITIVE_NORMALIZED_KEYS


def _sanitize_nested(value: Any, *, depth: int = 0) -> tuple[Any, bool, bool]:
    """Return (safe value, truncated, redacted) for a JSON-compatible value."""
    if depth > MAX_NESTING_DEPTH:
        return "[MAX_DEPTH_REACHED]", True, False

    if isinstance(value, Mapping):
        safe: dict[str, Any] = {}
        truncated = len(value) > MAX_COLLECTION_ITEMS
        redacted = False

        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                break
            key_text = str(key)
            if _is_sensitive_key(key_text):
                safe[key_text] = REDACTED_VALUE
                redacted = True
                continue

            safe_item, item_truncated, item_redacted = _sanitize_nested(
                item,
                depth=depth + 1,
            )
            safe[key_text] = safe_item
            truncated = truncated or item_truncated
            redacted = redacted or item_redacted

        if len(value) > MAX_COLLECTION_ITEMS:
            safe["_truncated_items"] = len(value) - MAX_COLLECTION_ITEMS
        return safe, truncated, redacted

    if isinstance(value, (list, tuple, set)):
        safe_items = []
        truncated = len(value) > MAX_COLLECTION_ITEMS
        redacted = False

        for item in list(value)[:MAX_COLLECTION_ITEMS]:
            safe_item, item_truncated, item_redacted = _sanitize_nested(
                item,
                depth=depth + 1,
            )
            safe_items.append(safe_item)
            truncated = truncated or item_truncated
            redacted = redacted or item_redacted

        if len(value) > MAX_COLLECTION_ITEMS:
            safe_items.append({"_truncated_items": len(value) - MAX_COLLECTION_ITEMS})
        return safe_items, truncated, redacted

    if isinstance(value, str) and len(value) > TRACE_MAX_STRING_CHARS:
        return (
            value[:TRACE_MAX_STRING_CHARS] + "… [truncated]",
            True,
            False,
        )

    return value, False, False


def _prepare_payload(
    value: Any,
    *,
    preserve_list_shape: bool = False,
) -> tuple[Any, bool, bool]:
    encoded = jsonable_encoder(value)
    safe_value, truncated, redacted = _sanitize_nested(encoded)
    serialized = json.dumps(
        safe_value,
        default=str,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    if len(serialized) <= TRACE_MAX_PAYLOAD_CHARS:
        return safe_value, truncated, redacted

    preview_size = max(0, TRACE_MAX_PAYLOAD_CHARS - 160)
    marker = {
        "_truncated": True,
        "original_chars": len(serialized),
        "preview": serialized[:preview_size],
    }
    if preserve_list_shape:
        return [marker], True, redacted
    return marker, True, redacted


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
    output: Any = Field(default_factory=dict)
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
        output: Any = None,
        memories_retrieved: List[Dict[str, Any]] | None = None,
        success: bool = True,
        error: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Optional[UUID]:
        """
        Save a bounded, redacted trace without interrupting the agent on failure.

        run_in_txn already retries CockroachDB serialization conflicts. Other
        failures are logged with a traceback and return None because tracing is
        observability, not part of the agent's primary success path.
        """
        try:
            raw_memories = list(memories_retrieved or [])
            memories_were_limited = len(raw_memories) > TRACE_MAX_MEMORIES
            limited_memories = raw_memories[:TRACE_MAX_MEMORIES]
            if memories_were_limited:
                limited_memories.append(
                    {"_truncated_memories": len(raw_memories) - TRACE_MAX_MEMORIES}
                )

            safe_input, input_truncated, input_redacted = _prepare_payload(input or {})
            safe_output, output_truncated, output_redacted = _prepare_payload(
                output if output is not None else {}
            )
            safe_memories, memories_truncated, memories_redacted = _prepare_payload(
                limited_memories,
                preserve_list_shape=True,
            )
            safe_metadata, metadata_truncated, metadata_redacted = _prepare_payload(
                metadata or {}
            )

            if not isinstance(safe_metadata, dict):
                safe_metadata = {"value": safe_metadata}

            truncated_fields = [
                field
                for field, was_truncated in (
                    ("input", input_truncated),
                    ("output", output_truncated),
                    ("memories_retrieved", memories_truncated or memories_were_limited),
                    ("metadata", metadata_truncated),
                )
                if was_truncated
            ]
            safe_metadata["trace_safety"] = {
                "truncated_fields": truncated_fields,
                "redacted": any(
                    (
                        input_redacted,
                        output_redacted,
                        memories_redacted,
                        metadata_redacted,
                    )
                ),
            }

            async def transaction(connection: asyncpg.Connection):
                return await fetch_value(
                    connection,
                    INSERT_TRACE_SQL,
                    company_id,
                    agent_name,
                    start_time,
                    duration_ms,
                    safe_input,
                    safe_output,
                    safe_memories,
                    success,
                    (
                        error[:TRACE_MAX_ERROR_CHARS] + "… [truncated]"
                        if error and len(error) > TRACE_MAX_ERROR_CHARS
                        else error
                    ),
                    safe_metadata,
                )

            return await run_in_txn(transaction)
        except Exception as exc:
            logger.exception(
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
            row = await fetch_one(
                connection,
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
            output=(
                data.get("output")
                if data.get("output") is not None
                else {}
            ),
            memories_retrieved=data.get("memories_retrieved") or [],
            success=data["success"],
            error=data.get("error"),
            metadata=data.get("metadata") or {},
            created_at=data["created_at"],
        )
