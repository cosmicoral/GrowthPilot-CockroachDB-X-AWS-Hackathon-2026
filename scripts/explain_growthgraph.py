from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database


async def main() -> None:
    await database.connect()

    try:
        async with database.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id
                FROM companies
                WHERE name LIKE '%—%'
                ORDER BY id
                LIMIT 10
                """
            )

            if len(rows) < 2:
                raise RuntimeError(
                    "Need at least two seeded companies."
                )

            company_ids = [row["id"] for row in rows]

            vector = await conn.fetchval(
                """
                SELECT embedding
                FROM memories
                WHERE company_id = ANY($1::UUID[])
                  AND embedding IS NOT NULL
                LIMIT 1
                """,
                company_ids,
            )

            if vector is None:
                raise RuntimeError(
                    "No T35 embeddings found."
                )

            company_list = ", ".join(
                f"'{company_id}'"
                for company_id in company_ids
            )

            vector_literal = str(vector)

            explain_sql = f"""
            EXPLAIN ANALYZE
            SELECT
                id,
                company_id,
                memory_type,
                importance,
                created_at,
                1.0 - (
                    embedding <=> '{vector_literal}'::VECTOR(1024)
                ) AS similarity
            FROM memories
            WHERE company_id IN ({company_list})
              AND memory_type IN ('reflection', 'episodic')
            ORDER BY embedding <=> '{vector_literal}'::VECTOR(1024)
            LIMIT 100
            """

            print("=" * 80)
            print("T36 CROSS-COMPANY VECTOR QUERY")
            print("EXPLAIN ANALYZE")
            print("=" * 80)

            plan = await conn.fetch(explain_sql)

            for row in plan:
                print(row[0])

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())