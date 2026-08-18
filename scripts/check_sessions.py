from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database


async def main() -> None:
    await database.connect()

    try:
        async with database.acquire() as conn:
            columns = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'sessions'
                ORDER BY ordinal_position;
                """
            )

            indexes = await conn.fetch(
                """
                SHOW INDEXES FROM sessions;
                """
            )

            print("COLUMNS:")
            for row in columns:
                print(f"  {row['column_name']}")

            print("\nINDEXES:")
            for row in indexes:
                print(
                    f"  {row['index_name']}"
                )

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())