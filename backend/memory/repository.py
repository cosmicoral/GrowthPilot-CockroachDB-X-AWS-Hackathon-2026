"""
Memory repository.

Responsible for storing and retrieving memories.
Uses asyncpg directly because CockroachDB VECTOR
operations require custom SQL.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence, TypedDict
from uuid import UUID

import asyncpg

from backend.database.database import (
    database,
    run_in_txn,
    to_vector_literal,
)
from backend.memory.hash import create_content_hash
from backend.memory.store import (
    MemoryHit,
    MemoryType,
)


EMBEDDING_DIMENSION = 1024

SEMANTIC_SIMILARITY_THRESHOLD = 0.90


class MemoryInput(TypedDict):
    company_id: UUID
    memory_type: MemoryType
    content: str
    content_hash: str
    metadata: dict
    importance: float
    embedding: list[float]


SEARCH_SQL = f"""
WITH candidates AS MATERIALIZED
(
    SELECT
        id,
        company_id,
        content,
        memory_type,
        metadata,
        importance,
        created_at,
        1.0 - (
            embedding <=> $2::VECTOR({EMBEDDING_DIMENSION})
        ) AS similarity
    FROM memories
    WHERE company_id = $1
    ORDER BY embedding <=> $2::VECTOR({EMBEDDING_DIMENSION})
    LIMIT $3
)
SELECT
    id,
    company_id,
    content,
    memory_type,
    metadata,
    importance,
    similarity,
    created_at
FROM candidates
WHERE
(
    $4::STRING[] IS NULL
    OR memory_type = ANY($4::STRING[])
)
AND
(
    $5::TIMESTAMPTZ IS NULL
    OR created_at >= $5
)
ORDER BY
    GREATEST(similarity, 0.0)
    *
    POWER(
        0.5::FLOAT8,
        GREATEST(
            EXTRACT(
                EPOCH FROM (now() - created_at)
            ),
            0.0
        )
        /
        (30.0 * 86400.0)
    )
    *
    GREATEST(importance, 0.01) DESC,
    similarity DESC,
    created_at DESC,
    id ASC
LIMIT $6
"""


INSERT_SQL = f"""
INSERT INTO memories
(
    company_id,
    memory_type,
    content,
    content_hash,
    metadata,
    importance,
    embedding
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7::VECTOR({EMBEDDING_DIMENSION})
)
ON CONFLICT (company_id, content_hash)
DO NOTHING
RETURNING id
"""


SELECT_BY_HASH_SQL = """
SELECT id
FROM memories
WHERE company_id = $1
AND content_hash = $2
"""

FIND_SIMILAR_MEMORY_SQL = f"""
SELECT
    id,
    content,
    metadata,
    importance,
    created_at,
    1.0 - (
        embedding <=> $2::VECTOR({EMBEDDING_DIMENSION})
    ) AS similarity
FROM memories
WHERE company_id = $1
ORDER BY embedding <=> $2::VECTOR({EMBEDDING_DIMENSION})
LIMIT 1
"""


MERGE_MEMORY_SQL = """
UPDATE memories
SET
    metadata = $2,
    importance = GREATEST(importance, $3),
    last_accessed_at = now(),
    access_count = access_count + 1
WHERE id = $1
RETURNING id
"""


RECENT_SQL = """
SELECT
    id,
    company_id,
    content,
    memory_type,
    metadata,
    importance,
    created_at
FROM memories
WHERE company_id = $1
AND memory_type = $2
ORDER BY created_at DESC
LIMIT $3
"""

class MemoryRepository:
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service

    async def _insert_memory(
        self,
        connection: asyncpg.Connection,
        *,
        company_id,
        memory_type: MemoryType,
        content: str,
        content_hash: str,
        metadata: dict,
        importance: float,
        embedding
    ):
        """
        Insert a memory using database-level deduplication.

        Returns:
            New memory ID or existing memory ID.
        """

        embedding_vector = to_vector_literal(embedding)

        memory_id = await connection.fetchval(
            INSERT_SQL,
            company_id,
            memory_type,
            content,
            content_hash,
            metadata,
            importance,
            embedding_vector
        )

        if memory_id is not None:
            return memory_id

        return await connection.fetchval(
            SELECT_BY_HASH_SQL,
            company_id,
            content_hash
        )


    async def _find_semantic_duplicate(
        self,
        connection: asyncpg.Connection,
        *,
        company_id,
        embedding
    ):
        """
        Find a semantically similar existing memory.
        """

        embedding_vector = to_vector_literal(embedding)

        return await connection.fetchrow(
            FIND_SIMILAR_MEMORY_SQL,
            company_id,
            embedding_vector
        )


    async def _merge_memory(
        self,
        connection: asyncpg.Connection,
        *,
        memory_id,
        metadata,
        importance
    ):
        """
        Update an existing memory with new information.
        """

        return await connection.fetchval(
            MERGE_MEMORY_SQL,
            memory_id,
            metadata,
            importance
        )


    async def _save_or_merge_memory(
        self,
        connection: asyncpg.Connection,
        memory: MemoryInput,
    ):
        """
        Insert a memory or merge it with an existing
        semantically similar memory.
        """

        existing_id = await connection.fetchval(
            SELECT_BY_HASH_SQL,
            memory["company_id"],
            memory["content_hash"]
        )

        if existing_id:
            return existing_id


        similar = await self._find_semantic_duplicate(
            connection,
            company_id = memory["company_id"],
            embedding = memory["embedding"]
        )


        if (
            similar
            and similar["similarity"]
            >= SEMANTIC_SIMILARITY_THRESHOLD
        ):
            return await self._merge_memory(
                connection,
                memory_id = similar["id"],
                metadata = memory["metadata"],
                importance = memory["importance"]
            )


        return await self._insert_memory(
            connection,
            company_id = memory["company_id"],
            memory_type = memory["memory_type"],
            content = memory["content"],
            content_hash = memory["content_hash"],
            metadata = memory["metadata"],
            importance = memory["importance"],
            embedding = memory["embedding"],
        )


    @staticmethod
    def _to_memory_hit(row) -> MemoryHit:
        """
        Convert asyncpg row into MemoryHit model.
        """

        data = dict(row)

        return MemoryHit(
            id = data["id"],
            company_id = data["company_id"],
            content = data["content"],
            memory_type = data["memory_type"],
            metadata = data.get("metadata") or {},
            importance = data["importance"],
            similarity = data.get("similarity"),
            created_at = data["created_at"],
        )

    async def write(
        self,
        *,
        company_id,
        memory_type: MemoryType,
        content: str,
        metadata: dict | None = None,
        importance: float = 0.5,
    ):
        """
        Persist one memory.

        Flow:

        1. Generate embedding outside transaction.
        2. Insert inside CockroachDB transaction.
        3. Use ON CONFLICT for concurrency-safe deduplication.
        """

        if self.embedding_service is None:
            raise RuntimeError("An embedding service is required to write memories")


        if not content.strip():
            raise ValueError("Memory content cannot be empty")


        content_hash = create_content_hash(content)


        # Important:
        # Do not generate embeddings inside run_in_txn().
        # CockroachDB retries transactions on 40001.
        # Retrying Bedrock calls wastes cost and latency.
        embedding = await self.embedding_service.generate_embedding(content)


        if len(embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension "
                f"{EMBEDDING_DIMENSION}, "
                f"received {len(embedding)}"
            )

        memory = {
            "company_id": company_id,
            "memory_type": memory_type,
            "content": content,
            "content_hash": content_hash,
            "metadata": metadata or {},
            "importance": importance,
            "embedding": embedding,
        }

        return await self._save_memory_input(memory)


    async def save_memory(
        self,
        company_id,
        memory_type,
        content,
        content_hash,
        metadata,
        importance,
        embedding,
    ):
        """
        Store one memory.

        Kept for compatibility with existing
        T9 pipeline code.
        """

        memory = {
            "company_id": company_id,
            "memory_type": memory_type,
            "content": content,
            "content_hash": content_hash,
            "metadata": metadata or {},
            "importance": importance,
            "embedding": embedding,
        }

        return await self._save_memory_input(memory)

    async def _save_memory_input(self, memory: MemoryInput):

        # Persist one memory through the transactional merge-or-insert path.

        async def transaction(connection: asyncpg.Connection):
            return await self._save_or_merge_memory(
                connection,
                memory,
            )

        return await run_in_txn(transaction)


    async def save_memories_batch(self, memories: list[MemoryInput]):
        """
        Insert multiple memories in one transaction.

        Handles:

        - exact duplicate hashes
        - semantic duplicates
        - CockroachDB serialization retries
        """

        if not memories:
            return []


        async def transaction(connection: asyncpg.Connection):
            ids = []

            for memory in memories:
                memory_id = await self._save_or_merge_memory(connection, memory)

                ids.append(memory_id)

            return ids


        return await run_in_txn(
            transaction
        )

    async def get_memory(self, memory_id):
        """
        Retrieve a memory by ID.
        """

        query = f"""
        SELECT
            id,
            company_id,
            memory_type,
            content,
            metadata,
            importance,
            embedding
        FROM memories
        WHERE id = $1;
        """


        async with database.pool.acquire() as connection:
            return await connection.fetchrow(query, memory_id)


    async def get_by_content_hash(self, company_id, content_hash):
        """
        Find an existing memory by content hash.
        """

        async with database.pool.acquire() as connection:
            return await connection.fetchval(
                SELECT_BY_HASH_SQL,
                company_id,
                content_hash
            )


    async def find_similar_memory(
        self,
        company_id,
        embedding,
        threshold: float = SEMANTIC_SIMILARITY_THRESHOLD
    ):
        """
        Find a memory with semantic similarity above threshold.
        """

        embedding_vector = to_vector_literal(embedding)

        async with database.pool.acquire() as connection:
            row = await connection.fetchrow(
                FIND_SIMILAR_MEMORY_SQL,
                company_id,
                embedding_vector
            )


        if row is None:
            return None


        if row["similarity"] < threshold:
            return None


        return row


    async def merge_memory(self, memory_id, metadata, importance):
        """
        Merge new information into an existing memory.
        """

        async with database.pool.acquire() as connection:
            return await connection.fetchval(
                MERGE_MEMORY_SQL,
                memory_id,
                metadata,
                importance
            )


    async def search(
        self,
        *,
        company_id,
        query: str,
        k: int = 8,
        types: Sequence[MemoryType] | None = None,
        since: datetime | None = None
    ) -> list[MemoryHit]:
        """
        Two-stage memory retrieval.

        Stage 1:
            CockroachDB vector similarity search.

        Stage 2:
            Hybrid ranking:
                similarity
                recency decay
                importance
        """

        if self.embedding_service is None:
            raise RuntimeError(
                "An embedding service is required for memory search"
            )


        if not query.strip():
            raise ValueError("Search query must not be empty")


        if k <= 0:
            raise ValueError("Search result count must be positive")


        query_embedding = await self.embedding_service.generate_embedding(query)


        if len(query_embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension "
                f"{EMBEDDING_DIMENSION}, "
                f"received {len(query_embedding)}"
            )


        query_vector = to_vector_literal(query_embedding)


        candidate_limit = max(50, k * 10)


        normalized_types = (
            list(types)
            if types
            else None
        )


        async with database.pool.acquire() as connection:
            rows = await connection.fetch(
                SEARCH_SQL,
                company_id,
                query_vector,
                candidate_limit,
                normalized_types,
                since,
                k
            )


        return [
            self._to_memory_hit(row)
            for row in rows
        ]

    async def recent(
        self,
        *,
        company_id,
        memory_type: MemoryType,
        limit: int = 20
    ) -> list[MemoryHit]:
        """
        Return recent memories for a company.

        Uses the company/type/time index instead of
        vector search because this is a chronological query.
        """

        if limit <= 0:
            raise ValueError("Result limit must be positive")


        async def query(connection: asyncpg.Connection):
            return await connection.fetch(
                RECENT_SQL,
                company_id,
                memory_type,
                limit
            )


        rows = await run_in_txn(query)


        return [
            self._to_memory_hit(row)
            for row in rows
        ]


    async def delete_memory(self, memory_id):
        """
        Delete a memory by ID.

        Primarily used for maintenance/testing.
        """

        query = """
        DELETE FROM memories
        WHERE id = $1
        RETURNING id;
        """


        async with database.pool.acquire() as connection:
            return await connection.fetchval(query, memory_id)


    async def count_memories(self, company_id):
        """
        Return number of memories stored for a company.
        """

        query = """
        SELECT COUNT(*)
        FROM memories
        WHERE company_id = $1;
        """


        async with database.pool.acquire() as connection:
            return await connection.fetchval(query, company_id)


    async def touch_memory(self, memory_id):
        """
        Update access metadata.

        Called when a memory is successfully retrieved.
        """

        query = """
        UPDATE memories
        SET
            last_accessed_at = now(),
            access_count = access_count + 1
        WHERE id = $1
        RETURNING id;
        """


        async with database.pool.acquire() as connection:
            return await connection.fetchval(query, memory_id)

    async def update_importance(self, memory_id, importance: float):
        """
        Update memory importance score.
        """

        if not 0.0 <= importance <= 1.0:
            raise ValueError("Importance must be between 0 and 1")


        query = """
        UPDATE memories
        SET importance = $2
        WHERE id = $1
        RETURNING id;
        """


        async with database.pool.acquire() as connection:
            return await connection.fetchval(query, memory_id, importance)


    async def list_by_type(
        self,
        *,
        company_id,
        memory_type: MemoryType,
        limit: int = 50
    ) -> list[MemoryHit]:
        """
        List memories filtered by type.

        Useful for debugging and agent context inspection.
        """

        if limit <= 0:
            raise ValueError("Limit must be positive")


        query = """
        SELECT
            id,
            company_id,
            content,
            memory_type,
            metadata,
            importance,
            created_at
        FROM memories
        WHERE company_id = $1
        AND memory_type = $2
        ORDER BY created_at DESC
        LIMIT $3;
        """


        async with database.pool.acquire() as connection:
            rows = await connection.fetch(
                query,
                company_id,
                memory_type,
                limit
            )


        return [
            self._to_memory_hit(row)
            for row in rows
        ]


    async def health_check(self) -> bool:
        """
        Verify repository database connectivity.
        """

        query = """
        SELECT 1;
        """

        async with database.pool.acquire() as connection:
            result = await connection.fetchval(query)


        return result == 1
    