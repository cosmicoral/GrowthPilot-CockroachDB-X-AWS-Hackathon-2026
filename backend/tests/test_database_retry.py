import asyncio

import asyncpg
import pytest

from backend.database.database import run_in_txn, with_retry


class SerializationFailure(asyncpg.PostgresError):
    @property
    def sqlstate(self):
        return "40001"


@pytest.mark.asyncio
async def test_with_retry_retries_serialization_failure():
    """
    Verify serialization failures are retried until the operation succeeds.
    """

    attempts = 0

    async def operation():
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            raise SerializationFailure("serialization failure")

        return "success"

    result = await with_retry(
        operation,
        max_attempts = 3,
        base_delay = 0,
    )

    assert result == "success"
    assert attempts == 3

@pytest.mark.asyncio
async def test_with_retry_raises_after_max_attempts():
    """
    Verify serialization failures are raised after max attempts.
    """

    attempts = 0

    async def operation():
        nonlocal attempts
        attempts += 1

        raise SerializationFailure("serialization failure")

    with pytest.raises(SerializationFailure):
        await with_retry(
            operation,
            max_attempts = 3,
            base_delay = 0,
        )

    assert attempts == 3

@pytest.mark.asyncio
async def test_with_retry_does_not_retry_non_serialization_error():
    """
    Verify non-serialization database errors are not retried.
    """

    attempts = 0

    class NonRetryableError(asyncpg.PostgresError):
        @property
        def sqlstate(self):
            return "23505"

    async def operation():
        nonlocal attempts
        attempts += 1

        raise NonRetryableError("unique constraint violation")

    with pytest.raises(NonRetryableError):
        await with_retry(
            operation,
            max_attempts = 5,
            base_delay = 0,
        )

    assert attempts == 1

@pytest.mark.asyncio
async def test_run_in_txn_retries_entire_transaction(monkeypatch):
    """
    Verify run_in_txn retries the transaction after a serialization failure.
    """

    events = []
    attempts = 0

    class MockTransaction:
        async def __aenter__(self):
            events.append("transaction_enter")
            return self

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            events.append(
                "transaction_rollback"
                if exc_type
                else "transaction_commit"
            )
            return False

    class MockConnection:
        def transaction(self):
            return MockTransaction()

    class MockAcquire:
        async def __aenter__(self):
            events.append("connection_acquire")
            return MockConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            events.append("connection_release")
            return False

    class MockPool:
        def acquire(self):
            return MockAcquire()

    monkeypatch.setattr(
        "backend.database.database.database.pool",
        MockPool(),
    )

    async def operation(connection):
        nonlocal attempts

        attempts += 1

        if attempts == 1:
            raise SerializationFailure(
                "serialization failure"
            )

        return "success"

    result = await run_in_txn(
        operation,
        max_attempts = 2,
        base_delay = 0,
    )

    assert result == "success"
    assert attempts == 2

    assert events == [
        "connection_acquire",
        "transaction_enter",
        "transaction_rollback",
        "connection_release",
        "connection_acquire",
        "transaction_enter",
        "transaction_commit",
        "connection_release",
    ]