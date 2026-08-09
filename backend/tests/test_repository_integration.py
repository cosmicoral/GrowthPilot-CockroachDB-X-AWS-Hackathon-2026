from uuid import uuid4

import pytest

from backend.database.database import database
from backend.memory.hash import create_content_hash
from backend.memory.repository import MemoryRepository


class FixedEmbeddingService:
    """Return a deterministic, non-zero 1024-dimensional embedding."""

    async def generate_embedding(self, text: str) -> list[float]:
        embedding = [0.0] * 1024
        embedding[0] = 1.0
        return embedding


@pytest.mark.integration
@pytest.mark.asyncio
async def test_write_dedup_vector_cast_and_jsonb_round_trip_on_real_cluster():
    """Exercise the production memory write path against CockroachDB."""

    company_id = None
    content = f"T10 real-cluster verification {uuid4()}"
    content_hash = create_content_hash(content)
    metadata = {
        "source": "t10-integration-test",
        "nested": {
            "verified": True,
        },
        "tags": [
            "dedup",
            "vector",
            "jsonb",
        ],
    }

    await database.connect()

    try:
        async with database.pool.acquire() as connection:
            company_id = await connection.fetchval(
                """
                INSERT INTO companies (name)
                VALUES ($1)
                RETURNING id
                """,
                f"T10 integration test {uuid4()}",
            )

        repository = MemoryRepository(
            embedding_service=FixedEmbeddingService(),
        )

        first_id = await repository.write(
            company_id=company_id,
            memory_type="reflection",
            content=content,
            metadata=metadata,
            importance=0.9,
        )

        second_id = await repository.write(
            company_id=company_id,
            memory_type="reflection",
            content=content,
            metadata=metadata,
            importance=0.9,
        )

        async with database.pool.acquire() as connection:
            row_count = await connection.fetchval(
                """
                SELECT count(*)
                FROM memories
                WHERE company_id = $1
                  AND content_hash = $2
                """,
                company_id,
                content_hash,
            )

            stored = await connection.fetchrow(
                """
                SELECT
                    id,
                    metadata,
                    embedding::STRING AS embedding_text
                FROM memories
                WHERE company_id = $1
                  AND content_hash = $2
                """,
                company_id,
                content_hash,
            )

        assert first_id == second_id
        assert row_count == 1
        assert stored is not None
        assert stored["id"] == first_id
        assert stored["metadata"] == metadata
        assert stored["embedding_text"].startswith("[1")
        assert stored["embedding_text"].endswith("]")
    finally:
        if company_id is not None and database.pool is not None:
            async with database.pool.acquire() as connection:
                # memories are removed by the companies foreign-key cascade.
                await connection.execute(
                    "DELETE FROM companies WHERE id = $1",
                    company_id,
                )

        await database.disconnect()
