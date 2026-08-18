from unittest.mock import AsyncMock

import pytest

from backend.database.database import database, fetch_one, fetch_value


@pytest.mark.asyncio
async def test_fetch_helpers_fully_drain_results():
    connection = AsyncMock()
    connection.fetch.side_effect = [
        [{"id": "row-1"}],
        [[42]],
        [],
    ]

    assert await fetch_one(connection, "SELECT one") == {"id": "row-1"}
    assert await fetch_value(connection, "SELECT value") == 42
    assert await fetch_one(connection, "SELECT none") is None
    connection.fetchrow.assert_not_awaited()
    connection.fetchval.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memories_table_exists():

    try:
        await database.connect()

        async with database.pool.acquire() as connection:

            result = await connection.fetchval(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name = 'memories'
                """
            )

        assert result == 1

    finally:
        await database.disconnect()
