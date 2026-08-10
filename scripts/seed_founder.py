"""Seed Mosaic Kitchen ranking-evaluation memories into CockroachDB.

Usage:

    .venv/bin/python scripts/seed_founder.py

Remove all seeded data:

    .venv/bin/python scripts/seed_founder.py --cleanup

The script is idempotent:
- it reuses one fixed evaluation company;
- existing memories are found by content hash;
- existing rows are updated instead of duplicated.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID


ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database  # noqa: E402
from backend.llm.client import BedrockClient  # noqa: E402
from backend.memory.embedding import BedrockEmbeddingService  # noqa: E402
from backend.memory.hash import create_content_hash  # noqa: E402
from backend.memory.repository import MemoryRepository  # noqa: E402
from scripts.mosaic_ranking_data import EVAL_MEMORIES  # noqa: E402


COMPANY_ID = UUID("8c760052-7ba2-4caa-b382-42d57cc44579")
COMPANY_NAME = "Mosaic Kitchen — Ranking Evaluation"
COMPANY_WEBSITE = "https://github.com/cosmicoral/Mosaic-Kitchen-AI"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Mosaic Kitchen ranking-evaluation memories.",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the evaluation company and all associated memories.",
    )

    return parser.parse_args()


async def ensure_company() -> None:
    """Create or refresh the fixed Mosaic Kitchen evaluation company."""

    async with database.pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO companies
            (
                id,
                name,
                website,
                industry,
                description
            )
            VALUES
            (
                $1,
                $2,
                $3,
                $4,
                $5
            )
            ON CONFLICT (id)
            DO UPDATE SET
                name = excluded.name,
                website = excluded.website,
                industry = excluded.industry,
                description = excluded.description
            """,
            COMPANY_ID,
            COMPANY_NAME,
            COMPANY_WEBSITE,
            "Consumer AI / FoodTech",
            (
                "AI-powered multicultural meal-planning and grocery "
                "assistant for diverse households in the UK."
            ),
        )


async def cleanup() -> None:
    """Delete the evaluation company and cascade-delete its memories."""

    async with database.pool.acquire() as connection:
        result = await connection.execute(
            """
            DELETE FROM companies
            WHERE id = $1
            """,
            COMPANY_ID,
        )

    print(f"Cleanup completed: {result}")


async def seed_memories() -> None:
    """Generate real Titan embeddings and persist evaluation memories."""

    await ensure_company()

    embedding_service = BedrockEmbeddingService(
        BedrockClient(),
    )

    repository = MemoryRepository(
        embedding_service=embedding_service,
    )

    seed_time = datetime.now(timezone.utc)

    inserted = 0
    reused = 0

    for index, memory in enumerate(EVAL_MEMORIES, start=1):
        content = memory["content"]
        content_hash = create_content_hash(content)

        # Avoid paying for another Bedrock embedding when rerunning
        # the seed script.
        memory_id = await repository.get_by_content_hash(
            COMPANY_ID,
            content_hash,
        )

        if memory_id is None:
            memory_id = await repository.write(
                company_id=COMPANY_ID,
                memory_type=memory["memory_type"],
                content=content,
                metadata={
                    **memory["metadata"],
                    "eval_key": memory["key"],
                    "product": "Mosaic Kitchen",
                },
                importance=memory["importance"],
            )

            inserted += 1
            action = "inserted"
        else:
            reused += 1
            action = "reused"

        # write() intentionally uses the current timestamp. For ranking
        # evaluation we backdate each memory to create controlled recency
        # differences.
        created_at = seed_time - timedelta(
            days=memory["age_days"],
        )

        async with database.pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE memories
                SET
                    memory_type = $2,
                    metadata = $3,
                    importance = $4,
                    created_at = $5
                WHERE id = $1
                """,
                memory_id,
                memory["memory_type"],
                {
                    **memory["metadata"],
                    "eval_key": memory["key"],
                    "product": "Mosaic Kitchen",
                    "age_days": memory["age_days"],
                },
                memory["importance"],
                created_at,
            )

        print(
            f"[{index:02d}/{len(EVAL_MEMORIES)}] "
            f"{action}: {memory['key']}"
        )

    async with database.pool.acquire() as connection:
        stored_count = await connection.fetchval(
            """
            SELECT count(*)
            FROM memories
            WHERE company_id = $1
            """,
            COMPANY_ID,
        )

    print()
    print("Mosaic Kitchen seed completed")
    print(f"Company ID: {COMPANY_ID}")
    print(f"Inserted: {inserted}")
    print(f"Reused: {reused}")
    print(f"Stored memories: {stored_count}")


async def main() -> None:
    args = parse_args()

    await database.connect()

    try:
        if args.cleanup:
            await cleanup()
        else:
            await seed_memories()
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())