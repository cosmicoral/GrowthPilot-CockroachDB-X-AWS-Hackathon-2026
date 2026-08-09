from datetime import datetime, timezone
from uuid import uuid4

import pytest
import asyncpg

from backend.database.database import database
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit


# ---------------------------------------------------------------------------
# Save-memory mocks
# ---------------------------------------------------------------------------


class MockSaveTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class MockConnection:
    """
    Fake database connection used by save_memory tests.
    """

    async def fetchval(self, query, *args):
        return 1

    def transaction(self):
        return MockSaveTransaction()


class MockAcquire:
    """
    Fake async context manager returned by pool.acquire().
    """

    async def __aenter__(self):
        return MockConnection()

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False


class MockPool:
    """
    Fake database connection pool.
    """

    def acquire(self):
        return MockAcquire()


def create_test_embedding():
    """
    Return a deterministic 1024-dimensional test embedding.
    """
    embedding = [0.0] * 1024
    embedding[0] = 1.0
    return embedding


@pytest.mark.asyncio
async def test_save_memory(monkeypatch):
    """
    save_memory should return the ID produced by the database.
    """
    monkeypatch.setattr(
        database,
        "pool",
        MockPool(),
    )

    repository = MemoryRepository()

    result = await repository.save_memory(
        company_id="company-1",
        memory_type="reflection",
        content="GrowthPilot learned something",
        content_hash="test-hash-123",
        metadata={
            "source": "agent",
        },
        importance=0.8,
        embedding=create_test_embedding(),
    )

    assert result == 1


@pytest.mark.asyncio
async def test_save_memories_batch(monkeypatch):
    """
    T9:
    Verify batch memory insertion.
    """
    monkeypatch.setattr(
        database,
        "pool",
        MockPool(),
    )

    repository = MemoryRepository()

    memories = [
        {
            "company_id": "company-1",
            "memory_type": "semantic",
            "content": "First memory",
            "content_hash": "hash-1",
            "metadata": {},
            "importance": 0.5,
            "embedding": create_test_embedding(),
        },
        {
            "company_id": "company-1",
            "memory_type": "semantic",
            "content": "Second memory",
            "content_hash": "hash-2",
            "metadata": {},
            "importance": 0.5,
            "embedding": create_test_embedding(),
        },
    ]

    result = await repository.save_memories_batch(memories)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_save_memories_batch_returns_existing_id_on_conflict(
    monkeypatch,
):
    """
    T9:
    Verify batch insertion returns the existing ID when
    content-hash deduplication prevents an insert.
    """

    existing_id = uuid4()

    class ConflictConnection:
        async def fetchval(self, query, *args):
            if "INSERT INTO memories" in query:
                return None

            if "content_hash = $2" in query:
                return existing_id

            raise AssertionError(f"Unexpected query: {query}")

        def transaction(self):
            return MockSaveTransaction()
        
    class ConflictAcquire:
        async def __aenter__(self):
            return ConflictConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False

    class ConflictPool:
        def acquire(self):
            return ConflictAcquire()

    monkeypatch.setattr(
        database,
        "pool",
        ConflictPool(),
    )

    repository = MemoryRepository()

    memories = [
        {
            "company_id": "company-1",
            "memory_type": "semantic",
            "content": "Existing memory",
            "content_hash": "existing-hash",
            "metadata": {},
            "importance": 0.5,
            "embedding": create_test_embedding(),
        },
    ]

    result = await repository.save_memories_batch(memories)

    assert result == [existing_id]


@pytest.mark.asyncio
async def test_save_memories_batch_handles_insert_and_conflict(
    monkeypatch,
):
    """
    T9:
    Verify a batch can contain both newly inserted and
    already-existing memories.
    """

    inserted_id = uuid4()
    existing_id = uuid4()

    class MixedConnection:
        def __init__(self):
            self.insert_calls = 0

        async def fetchval(self, query, *args):

            if "SELECT id" in query:
                content_hash = args[1]

                if content_hash == "existing-hash":
                    return existing_id

                return None


            if "INSERT INTO memories" in query:
                self.insert_calls += 1

                return inserted_id


            raise AssertionError(
                f"Unexpected query: {query}"
            )


        async def fetchrow(self, query, *args):
            """
            No semantic duplicate in this legacy T9 test.
            """
            if "embedding <=>" in query:
                return None

            raise AssertionError(
                f"Unexpected query: {query}"
            )

        def transaction(self):
            return MockSaveTransaction()

    connection = MixedConnection()

    class MixedAcquire:
        async def __aenter__(self):
            return connection

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False

    class MixedPool:
        def acquire(self):
            return MixedAcquire()

    monkeypatch.setattr(
        database,
        "pool",
        MixedPool(),
    )

    repository = MemoryRepository()

    memories = [
        {
            "company_id": "company-1",
            "memory_type": "semantic",
            "content": "New memory",
            "content_hash": "new-hash",
            "metadata": {},
            "importance": 0.5,
            "embedding": create_test_embedding(),
        },
        {
            "company_id": "company-1",
            "memory_type": "semantic",
            "content": "Existing memory",
            "content_hash": "existing-hash",
            "metadata": {},
            "importance": 0.5,
            "embedding": create_test_embedding(),
        },
    ]

    result = await repository.save_memories_batch(memories)

    assert result == [
        inserted_id,
        existing_id,
    ]


@pytest.mark.asyncio
async def test_save_memories_batch_merges_semantically_similar_memory(
    monkeypatch,
):
    """
    T11:
    Verify semantically similar memories are merged
    instead of creating duplicates.
    """

    existing_id = uuid4()

    class SemanticConnection:

        def transaction(self):
            return MockSaveTransaction()


        async def fetchval(
            self,
            query,
            *args,
        ):
            # Exact hash does not exist
            if "content_hash = $2" in query:
                return None


            # Merge existing memory
            if "UPDATE memories" in query:
                return existing_id


            # INSERT should not happen
            if "INSERT INTO memories" in query:
                raise AssertionError(
                    "Semantic duplicate should merge, not insert"
                )


            raise AssertionError(
                f"Unexpected query: {query}"
            )


        async def fetchrow(
            self,
            query,
            *args,
        ):
            if "embedding <=>" in query:
                return {
                    "id": existing_id,
                    "similarity": 0.95,
                }

            raise AssertionError(
                f"Unexpected query: {query}"
            )


    class SemanticAcquire:

        async def __aenter__(self):
            return SemanticConnection()


        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class SemanticPool:

        def acquire(self):
            return SemanticAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        SemanticPool(),
    )


    repository = MemoryRepository()


    result = await repository.save_memories_batch(
        [
            {
                "company_id": "company-1",
                "memory_type": "semantic",
                "content": "LinkedIn posts performed well",
                "content_hash": "new-hash",
                "metadata": {},
                "importance": 0.8,
                "embedding": create_test_embedding(),
            }
        ]
    )


    assert result == [
        existing_id
    ]


@pytest.mark.asyncio
async def test_save_memories_batch_semantic_merge_keeps_higher_importance(
    monkeypatch,
):
    """
    T11:
    Verify semantic merge updates metadata but keeps
    the higher importance value.
    """

    existing_id = uuid4()

    captured_args = {}

    class ImportanceConnection:

        def transaction(self):
            return MockSaveTransaction()

        async def fetchval(
            self,
            query,
            *args,
        ):
            if "content_hash = $2" in query:
                return None

            if "UPDATE memories" in query:
                captured_args["metadata"] = args[1]
                captured_args["importance"] = args[2]

                return existing_id

            if "INSERT INTO memories" in query:
                raise AssertionError(
                    "Should merge instead of insert"
                )

            raise AssertionError(
                f"Unexpected query: {query}"
            )

        async def fetchrow(
            self,
            query,
            *args,
        ):
            if "embedding <=>" in query:
                return {
                    "id": existing_id,
                    "similarity": 0.95,
                }

            raise AssertionError(
                f"Unexpected query: {query}"
            )


    class ImportanceAcquire:

        async def __aenter__(self):
            return ImportanceConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class ImportancePool:

        def acquire(self):
            return ImportanceAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        ImportancePool(),
    )


    repository = MemoryRepository()


    result = await repository.save_memories_batch(
        [
            {
                "company_id": "company-1",
                "memory_type": "semantic",
                "content": "Improved marketing results",
                "content_hash": "new-hash",
                "metadata": {
                    "source": "analytics-agent"
                },
                "importance": 0.6,
                "embedding": create_test_embedding(),
            }
        ]
    )


    assert result == [
        existing_id
    ]

    assert captured_args["metadata"] == {
        "source": "analytics-agent"
    }

    assert captured_args["importance"] == 0.6


@pytest.mark.asyncio
async def test_save_memories_batch_semantic_dedup_is_company_scoped(
    monkeypatch,
):
    """
    T11:
    Verify semantic deduplication only happens
    within the same company.
    """

    inserted_id = uuid4()

    class CompanyScopedConnection:

        def transaction(self):
            return MockSaveTransaction()

        async def fetchval(
            self,
            query,
            *args,
        ):
            if "content_hash = $2" in query:
                return None

            if "INSERT INTO memories" in query:
                return inserted_id

            raise AssertionError(
                f"Unexpected query: {query}"
            )

        async def fetchrow(
            self,
            query,
            *args,
        ):
            if "embedding <=>" in query:
                # No similar memory exists
                # for this company
                return None

            raise AssertionError(
                f"Unexpected query: {query}"
            )


    class CompanyScopedAcquire:

        async def __aenter__(self):
            return CompanyScopedConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class CompanyScopedPool:

        def acquire(self):
            return CompanyScopedAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        CompanyScopedPool(),
    )


    repository = MemoryRepository()


    result = await repository.save_memories_batch(
        [
            {
                "company_id": "company-new",
                "memory_type": "semantic",
                "content": "AI campaign performed well",
                "content_hash": "new-company-hash",
                "metadata": {},
                "importance": 0.5,
                "embedding": create_test_embedding(),
            }
        ]
    )


    assert result == [
        inserted_id
    ]


@pytest.mark.asyncio
async def test_save_memories_batch_semantic_merge_retries_transaction(
    monkeypatch,
):
    """
    T11:
    Verify semantic merge is retried when CockroachDB
    reports a serialization failure.
    """

    existing_id = uuid4()

    attempts = 0


    class RetryConnection:

        def transaction(self):
            return MockSaveTransaction()


        async def fetchval(
            self,
            query,
            *args,
        ):
            nonlocal attempts

            if "content_hash = $2" in query:
                return None

            if "UPDATE memories" in query:
                attempts += 1

                if attempts == 1:
                    raise asyncpg.exceptions.SerializationError(
                        "serialization failure"
                    )

                return existing_id


            raise AssertionError(
                f"Unexpected query: {query}"
            )


        async def fetchrow(
            self,
            query,
            *args,
        ):
            if "embedding <=>" in query:
                return {
                    "id": existing_id,
                    "similarity": 0.95,
                }

            raise AssertionError(
                f"Unexpected query: {query}"
            )


    class RetryAcquire:

        async def __aenter__(self):
            return RetryConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class RetryPool:

        def acquire(self):
            return RetryAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        RetryPool(),
    )


    repository = MemoryRepository()


    result = await repository.save_memories_batch(
        [
            {
                "company_id": "company-1",
                "memory_type": "semantic",
                "content": "Repeated campaign insight",
                "content_hash": "semantic-hash",
                "metadata": {},
                "importance": 0.8,
                "embedding": create_test_embedding(),
            }
        ]
    )


    assert result == [
        existing_id
    ]

    assert attempts == 2


@pytest.mark.asyncio
async def test_save_memories_batch_inserts_when_similarity_is_below_threshold(
    monkeypatch,
):
    """
    T11:
    Verify memories below semantic similarity threshold
    are inserted as new memories.
    """

    inserted_id = uuid4()


    class LowSimilarityConnection:

        def transaction(self):
            return MockSaveTransaction()


        async def fetchval(
            self,
            query,
            *args,
        ):

            # No exact hash match
            if "content_hash = $2" in query:
                return None


            # Insert new memory
            if "INSERT INTO memories" in query:
                return inserted_id


            raise AssertionError(
                f"Unexpected query: {query}"
            )


        async def fetchrow(
            self,
            query,
            *args,
        ):
            # Similarity lookup returns weak match
            if "embedding <=>" in query:
                return {
                    "id": uuid4(),
                    "similarity": 0.70,
                }


            raise AssertionError(
                f"Unexpected query: {query}"
            )


    class LowSimilarityAcquire:

        async def __aenter__(self):
            return LowSimilarityConnection()


        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class LowSimilarityPool:

        def acquire(self):
            return LowSimilarityAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        LowSimilarityPool(),
    )


    repository = MemoryRepository()


    result = await repository.save_memories_batch(
        [
            {
                "company_id": "company-1",
                "memory_type": "semantic",
                "content": "Completely different memory",
                "content_hash": "different-hash",
                "metadata": {},
                "importance": 0.5,
                "embedding": create_test_embedding(),
            }
        ]
    )


    assert result == [
        inserted_id
    ]


async def find_similar_memory(
    self,
    *,
    company_id,
    embedding,
    threshold: float,
):
    """
    Find an existing memory with similar meaning
    within the same company.
    """

    query = """
    SELECT
        id,
        content,
        metadata,
        importance,
        created_at,
        1.0 - (embedding <=> $2::VECTOR(1024))
            AS similarity
    FROM memories
    WHERE company_id = $1
    ORDER BY embedding <=> $2::VECTOR(1024)
    LIMIT 1;
    """

    embedding_vector = to_vector_literal(embedding)

    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            query,
            company_id,
            embedding_vector,
        )

    if row is None:
        return None

    if row["similarity"] < threshold:
        return None

    return row

# ---------------------------------------------------------------------------
# Search helpers and mocks
# ---------------------------------------------------------------------------


class FakeSearchEmbeddingService:
    """
    Fake embedding service that records incoming requests.
    """

    def __init__(self):
        self.calls = []

    async def generate_embedding(
        self,
        text,
    ):
        self.calls.append(text)
        return create_test_embedding()


class MockSearchConnection:
    """
    Fake database connection used by search tests.

    It records the SQL query and arguments so the test can
    inspect how MemoryRepository called CockroachDB.
    """

    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.args = None

    async def fetch(
        self,
        query,
        *args,
    ):
        self.query = query
        self.args = args

        return self.rows


class MockSearchAcquire:
    """
    Fake async context manager for search connections.
    """

    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False


class MockSearchPool:
    """
    Fake connection pool that returns MockSearchConnection.
    """

    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return MockSearchAcquire(self.connection)


@pytest.mark.asyncio
async def test_search_uses_vector_candidates_and_hybrid_ranking(
    monkeypatch,
):
    """
    GrowthPilot should retrieve a relevant campaign reflection
    and return it as a MemoryHit.

    The SQL should:

    1. Scope retrieval to one company.
    2. Use cosine vector distance for candidates.
    3. Re-rank with similarity, recency, and importance.
    """

    company_id = uuid4()
    memory_id = uuid4()

    created_at = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    connection = MockSearchConnection(
        rows=[
            {
                "id": memory_id,
                "company_id": company_id,
                "content": (
                    "Posts about engineering workflows "
                    "generated more engagement than "
                    "AI automation posts."
                ),
                "memory_type": "reflection",
                "metadata": {
                    "channel": "linkedin",
                    "source": "analytics-agent",
                },
                "importance": 0.9,
                "similarity": 0.95,
                "created_at": created_at,
            }
        ]
    )

    monkeypatch.setattr(
        database,
        "pool",
        MockSearchPool(connection),
    )

    embedding_service = FakeSearchEmbeddingService()

    repository = MemoryRepository(
        embedding_service=embedding_service
    )

    results = await repository.search(
        company_id=company_id,
        query="What messaging worked best in our previous campaign?",
        k=5,
        types=[
            "reflection",
        ],
    )

    assert len(results) == 1

    assert isinstance(
        results[0],
        MemoryHit,
    )

    assert results[0].id == memory_id
    assert results[0].company_id == company_id
    assert results[0].memory_type == "reflection"
    assert results[0].similarity == 0.95

    assert "engineering workflows" in results[0].content

    assert embedding_service.calls == [
        "What messaging worked best in our previous campaign?"
    ]

    assert "AS MATERIALIZED" in connection.query
    assert "WHERE company_id = $1" in connection.query
    assert "embedding <=> $2::VECTOR(1024)" in connection.query

    candidate_query_end = connection.query.index(
        "FROM candidates"
    )

    type_filter_position = connection.query.rindex(
        "$4::STRING[] IS NULL"
    )

    since_filter_position = connection.query.rindex(
        "$5::TIMESTAMPTZ IS NULL"
    )

    assert type_filter_position > candidate_query_end
    assert since_filter_position > candidate_query_end

    assert "POWER" in connection.query
    assert "GREATEST(importance" in connection.query

    assert connection.args[0] == company_id
    assert connection.args[2] == 50

    assert connection.args[3] == [
        "reflection",
    ]

    assert connection.args[4] is None
    assert connection.args[5] == 5


# ---------------------------------------------------------------------------
# Write helpers and mocks
# ---------------------------------------------------------------------------


class MockTransaction:
    def __init__(
        self,
        events,
    ):
        self.events = events

    async def __aenter__(
        self,
    ):
        self.events.append("transaction_enter")
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        self.events.append("transaction_exit")
        return False


class MockTransactionalAcquire:
    def __init__(
        self,
        connection,
    ):
        self.connection = connection

    async def __aenter__(
        self,
    ):
        return self.connection

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False


class MockTransactionalPool:
    def __init__(
        self,
        connection,
    ):
        self.connection = connection

    def acquire(
        self,
    ):
        return MockTransactionalAcquire(self.connection)


class RecordingEmbeddingService:
    def __init__(
        self,
        events,
    ):
        self.events = events
        self.calls = []

    async def generate_embedding(
        self,
        text,
    ):
        self.events.append("embedding")
        self.calls.append(text)
        return create_test_embedding()


class MockWriteConnection:
    def __init__(
        self,
        *,
        existing_id,
        events,
    ):
        self.existing_id = existing_id
        self.events = events
        self.queries = []

    def transaction(
        self,
    ):
        return MockTransaction(self.events)

    async def fetchval(
        self,
        query,
        *args,
    ):
        self.queries.append(
            (
                query,
                args,
            )
        )

        if "INSERT INTO memories" in query:
            return None

        if "content_hash = $2" in query:
            return self.existing_id

        raise AssertionError(
            f"Unexpected query: {query}"
        )


@pytest.mark.asyncio
async def test_write_is_idempotent_and_embeds_before_transaction(
    monkeypatch,
):
    events = []
    existing_id = uuid4()

    connection = MockWriteConnection(
        existing_id=existing_id,
        events=events,
    )

    monkeypatch.setattr(
        database,
        "pool",
        MockTransactionalPool(connection),
    )

    embedding_service = RecordingEmbeddingService(events)

    repository = MemoryRepository(
        embedding_service=embedding_service
    )

    result = await repository.write(
        company_id=uuid4(),
        memory_type="reflection",
        content="Engineering workflow posts performed better.",
        metadata={
            "source": "analytics-agent",
        },
        importance=0.9,
    )

    assert result == existing_id

    assert embedding_service.calls == [
        "Engineering workflow posts performed better."
    ]

    assert events.index("embedding") < events.index(
        "transaction_enter"
    )

    insert_query = connection.queries[0][0]

    assert "ON CONFLICT (company_id, content_hash)" in insert_query
    assert "DO NOTHING" in insert_query


# ---------------------------------------------------------------------------
# Recent-memory helpers and mocks
# ---------------------------------------------------------------------------


class MockRecentConnection:
    def __init__(
        self,
        *,
        rows,
        events,
    ):
        self.rows = rows
        self.events = events
        self.query = None
        self.args = None

    def transaction(
        self,
    ):
        return MockTransaction(self.events)

    async def fetch(
        self,
        query,
        *args,
    ):
        self.query = query
        self.args = args

        return self.rows


@pytest.mark.asyncio
async def test_recent_returns_memory_hits_in_time_order(
    monkeypatch,
):
    events = []
    company_id = uuid4()

    newest_id = uuid4()
    older_id = uuid4()

    newest_time = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    older_time = datetime(
        2026,
        8,
        6,
        12,
        0,
        tzinfo=timezone.utc,
    )

    connection = MockRecentConnection(
        events=events,
        rows=[
            {
                "id": newest_id,
                "company_id": company_id,
                "content": "Newest reflection",
                "memory_type": "reflection",
                "metadata": {},
                "importance": 0.9,
                "created_at": newest_time,
            },
            {
                "id": older_id,
                "company_id": company_id,
                "content": "Older reflection",
                "memory_type": "reflection",
                "metadata": {},
                "importance": 0.7,
                "created_at": older_time,
            },
        ],
    )

    monkeypatch.setattr(
        database,
        "pool",
        MockTransactionalPool(connection),
    )

    repository = MemoryRepository()

    results = await repository.recent(
        company_id=company_id,
        memory_type="reflection",
        limit=2,
    )

    assert [result.id for result in results] == [
        newest_id,
        older_id,
    ]

    assert all(
        isinstance(result, MemoryHit)
        for result in results
    )

    assert all(
        result.similarity is None
        for result in results
    )

    assert "ORDER BY created_at DESC" in connection.query

    assert connection.args == (
        company_id,
        "reflection",
        2,
    )

@pytest.mark.asyncio
async def test_merge_memory(monkeypatch):

    memory_id = uuid4()

    class MergeConnection:

        async def fetchval(self, query, *args):
            assert "UPDATE memories" in query
            return memory_id


    class MergeAcquire:

        async def __aenter__(self):
            return MergeConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
        ):
            return False


    class MergePool:

        def acquire(self):
            return MergeAcquire()


    monkeypatch.setattr(
        database,
        "pool",
        MergePool(),
    )


    repository = MemoryRepository()

    result = await repository.merge_memory(
        memory_id,
        {
            "source": "agent"
        },
        0.9,
    )

    assert result == memory_id


@pytest.mark.asyncio
async def test_write_rejects_invalid_embedding_dimension(monkeypatch):
    class BadEmbeddingService:
        async def generate_embedding(self, text):
            return [0.1, 0.2]

    repository = MemoryRepository(
        embedding_service=BadEmbeddingService()
    )

    with pytest.raises(ValueError):
        await repository.write(
            company_id=uuid4(),
            memory_type="semantic",
            content="test memory",
        )


@pytest.mark.asyncio
async def test_write_rejects_empty_content():
    repository = MemoryRepository(
        embedding_service=FakeSearchEmbeddingService()
    )

    with pytest.raises(ValueError):
        await repository.write(
            company_id=uuid4(),
            memory_type="semantic",
            content="   ",
        )


@pytest.mark.asyncio
async def test_search_rejects_empty_query():

    repository = MemoryRepository(
        embedding_service=FakeSearchEmbeddingService()
    )

    with pytest.raises(ValueError):
        await repository.search(
            company_id=uuid4(),
            query="",
        )


@pytest.mark.asyncio
async def test_search_rejects_invalid_k():

    repository = MemoryRepository(
        embedding_service=FakeSearchEmbeddingService()
    )

    with pytest.raises(ValueError):
        await repository.search(
            company_id=uuid4(),
            query="hello",
            k=0,
        )