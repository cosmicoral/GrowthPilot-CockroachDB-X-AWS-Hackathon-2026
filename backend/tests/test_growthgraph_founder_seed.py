"""Regression tests for the T35 GrowthGraph synthetic founder seed."""

import sys
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from scripts import seed_growthgraph_founders as seed


def test_parse_args_rejects_count_outside_supported_range(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["seed_growthgraph_founders.py", "--count", "49"])

    with pytest.raises(SystemExit) as exc_info:
        seed.parse_args()

    assert exc_info.value.code == 2


@pytest.mark.asyncio
async def test_cleanup_always_targets_the_entire_deterministic_cohort(monkeypatch):
    connection = AsyncMock()
    connection.execute.return_value = "DELETE 100"

    async def fake_run_in_txn(operation):
        return await operation(connection)

    monkeypatch.setattr(seed, "run_in_txn", fake_run_in_txn)

    await seed.cleanup()

    connection.execute.assert_awaited_once()
    company_ids = connection.execute.await_args.args[1]
    assert len(company_ids) == seed.MAX_FOUNDER_COUNT
    assert company_ids[0] == seed.derive_company_id(0)
    assert company_ids[-1] == seed.derive_company_id(seed.MAX_FOUNDER_COUNT - 1)


@pytest.mark.asyncio
async def test_seed_founder_groups_all_database_writes_in_one_transaction(monkeypatch):
    founder = seed.generate_founder(0)
    memory_count = len(founder["memories"])
    memory_ids = [uuid4() for _ in range(memory_count)]
    events = []

    repository = AsyncMock()
    repository.get_by_content_hash.side_effect = [None] * memory_count

    async def save_memory(connection, memory):
        events.append("memory_write")
        assert connection is transaction_connection
        return memory_ids.pop(0)

    repository._save_or_merge_memory.side_effect = save_memory

    embedding_service = AsyncMock()

    async def generate_embeddings(contents):
        events.append("embedding")
        return [[0.0] * 1024 for _ in contents]

    embedding_service.generate_embeddings.side_effect = generate_embeddings

    transaction_connection = AsyncMock()
    transaction_connection.execute.return_value = "OK"
    transaction_count = 0

    async def fake_run_in_txn(operation):
        nonlocal transaction_count
        transaction_count += 1
        events.append("transaction_start")
        result = await operation(transaction_connection)
        events.append("transaction_end")
        return result

    monkeypatch.setattr(seed, "run_in_txn", fake_run_in_txn)

    result = await seed.seed_founder(
        founder,
        repository,
        embedding_service,
        seed.datetime.now(seed.timezone.utc),
    )

    assert transaction_count == 1
    assert events[0:2] == ["embedding", "transaction_start"]
    assert events[-1] == "transaction_end"
    assert result == {
        "company_id": founder["company_id"],
        "inserted": memory_count,
        "reused": 0,
    }
    assert repository._save_or_merge_memory.await_count == memory_count

    # One company upsert plus one tenant-scoped timestamp update per memory,
    # all made through the transaction's connection.
    assert transaction_connection.execute.await_count == memory_count + 1
    for call in transaction_connection.execute.await_args_list[1:]:
        assert "WHERE company_id = $1 AND id = $2" in call.args[0]
        assert "SET metadata = $3" in call.args[0]
        assert call.args[1] == founder["company_id"]
        assert isinstance(call.args[3], dict)
