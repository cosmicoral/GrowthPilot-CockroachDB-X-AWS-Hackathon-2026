"""
Database connection manager using asyncpg connection pool.

This module owns database lifecycle:
- create pool
- provide connections
- close pool
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import ssl
from typing import Awaitable, Callable, TypeVar

import asyncpg

from backend.database.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

SERIALIZATION_FAILURE = "40001"


async def fetch_one(
    connection: asyncpg.Connection,
    query: str,
    *args,
):
    """Return one fully drained row without leaving a portal suspended."""

    rows = await connection.fetch(query, *args)
    return rows[0] if rows else None


async def fetch_value(
    connection: asyncpg.Connection,
    query: str,
    *args,
):
    """Return one scalar while fully draining CockroachDB's result portal."""

    row = await fetch_one(connection, query, *args)
    return row[0] if row is not None else None

async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register type codecs and session settings asyncpg/CockroachDB need.

    Runs once per new pooled connection, so every query gets them without
    callers having to serialise by hand.
    """
    # asyncpg hands JSONB back as a raw string by default. Registering
    # json.dumps/loads lets callers pass and receive plain dicts.
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )

    # No multiple_active_portals_enabled here, deliberately.
    #
    # CockroachDB v26.2 rejects a second statement on a connection while an
    # earlier result portal is still open. Enabling that preview setting looks
    # like the fix -- it is what the error message suggests -- but it only
    # swaps one failure for another: with it on, a suspended portal must be a
    # "pausable" portal, and those are restricted to read-only SELECTs with no
    # sub-queries. That rules out INSERT ... RETURNING and every CTE query in
    # backend/memory/repository.py, so the memory write path still fails, just
    # with a less obvious error.
    #
    # The actual fix is to never leave a portal suspended: see fetch_one /
    # fetch_value above, which use fetch()
    # (no row limit, result set drained, portal closed) instead of
    # fetchrow()/fetchval() (row limit 1, portal left open). With those in
    # place no session setting is needed and no preview feature is relied on.


class Database:
    """
    Global database manager.
    """

    def __init__(self):
        self.pool: asyncpg.Pool | None = None


    async def connect(self):
        """
        Create asyncpg connection pool.
        """

        if self.pool is None:

            settings = get_settings()
            ssl_context = ssl.create_default_context()

            self.pool = await asyncpg.create_pool(
                settings.database_url,
                ssl=ssl_context,
                min_size=settings.db_pool_min_size,
                max_size=settings.db_pool_max_size,
                command_timeout=settings.db_command_timeout,
                max_inactive_connection_lifetime=(
                    settings.db_max_inactive_connection_lifetime
                ),
                init=_init_connection,
            )


    async def disconnect(self):
        """
        Close all database connections.
        """

        if self.pool:
            await self.pool.close()
            self.pool = None


    def acquire(self):
        """
        Acquire one connection from pool.
        """

        if self.pool is None:
            raise RuntimeError(
                "Database pool is not initialized"
            )

        return self.pool.acquire()


database = Database()

async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 5,
    base_delay: float = 0.05,
) -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except asyncpg.PostgresError as exc:
            retryable = getattr(exc, "sqlstate", None) == SERIALIZATION_FAILURE

            if not retryable or attempt == max_attempts:
                raise

            # Full jitter: without it, two conflicting transactions back off
            # by the same amount and collide again on the retry.
            delay = random.uniform(0, base_delay * (2 ** (attempt - 1)))

            logger.warning(
                "Transaction serialization failure. Retrying attempt %s/%s after %.3fs",
                attempt,
                max_attempts,
                delay,
            )

            await asyncio.sleep(delay)

    raise AssertionError("unreachable")

async def run_in_txn(
    fn: Callable[[asyncpg.Connection],Awaitable[T]],
    *,
    max_attempts: int = 5,
    base_delay: float = 0.05,
) -> T:
    """Run `fn` inside a transaction, retrying the whole transaction on 40001.

This is what the rest of the codebase should use for writes. Compute
embeddings *before* calling it — retrying a transaction that calls
Bedrock costs money and latency.
    """
    pool = database.pool

    if pool is None: 
        raise RuntimeError("Database Pool is not initialized")

    async def _attempt() -> T:
    # Acquire inside the retry so a connection that just carried an
    # aborted transaction isn't reused.
        async with pool.acquire() as conn:
            async with conn.transaction():
                return await fn(conn)

    return await with_retry(
        _attempt,
        max_attempts=max_attempts,
        base_delay=base_delay,
    )

EMBEDDING_DIMENSION = 1024

def to_vector_literal(embedding: list[float]) ->str:
    """Format an embedding for a VECTOR column.

    asyncpg doesn't know CockroachDB's VECTOR type, so a Python list won't
    bind directly. Pass the result with an explicit cast:

        INSERT INTO memories (embedding) VALUES ($1::VECTOR(1024))
    """

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected embedding dimension {EMBEDDING_DIMENSION}, "
            f"got {len(embedding)}"
        )
    
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"
