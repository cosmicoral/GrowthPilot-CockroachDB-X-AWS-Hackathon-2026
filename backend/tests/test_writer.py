import pytest

from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from backend.memory.chunker import TextChunker
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.hash import create_content_hash
from backend.memory.writer import MemoryWriter
from backend.tests.mocks.repository import MockMemoryRepository
from backend.tests.mocks.bedrock import MockBedrockClient


async def create_writer():

    chunker = TextChunker()

    bedrock_client = MockBedrockClient()

    bedrock_service = BedrockEmbeddingService(bedrock_client = bedrock_client)

    repository = MockMemoryRepository()

    writer = MemoryWriter(
        chunker = chunker,
        embedding_service = bedrock_service,
        repository = repository
    )

    return writer, repository, bedrock_service



async def test_memory_writer_pipeline():
    """
    Verify the complete memory write pipeline:

    Text
      ↓
    Text chunking
      ↓
    Embedding generation
      ↓
    Memory persistence
    """

    writer, repository, _ = await create_writer()

    company_id = uuid4()

    test_memory = """
    A team lead mentioned that she would be away for a personal event this evening.

    GrowthPilot saved the note successfully.
    """

    result = await writer.write(
        company_id = company_id,
        text = test_memory
    )

    assert len(result) > 0



async def test_memory_writer_batch_save():
    """
    T9:
    Verify writer uses repository batch saving.
    """

    writer, repository, _ = await create_writer()

    repository.save_memories_batch = AsyncMock(return_value = [1, 2])

    company_id = uuid4()

    result = await writer.write(
        company_id = company_id,
        text = """
        First memory.
        Second memory.
        """
    )


    repository.save_memories_batch.assert_called_once()


    assert result == [1,2]



async def test_memory_writer_skip_duplicate():
    """
    Verify duplicate memories are not embedded again.
    """

    writer, repository, embedding_service = await create_writer()


    existing_memory = {
        "id": 1,
        "content": "Existing memory"
    }


    repository.get_by_content_hash = AsyncMock(
        return_value = existing_memory['id']
    )


    embedding_service.generate_embeddings = AsyncMock()


    company_id = uuid4()


    result = await writer.write(
        company_id = company_id,
        text = "Existing memory"
    )


    assert result == [
        existing_memory["id"]
    ]


    embedding_service.generate_embeddings.assert_not_called()


async def test_memory_writer_deduplicates_repeated_chunks():
    """
    Verify repeated chunks within the same write are embedded only once.
    """

    writer, repository, embedding_service = await create_writer()

    repeated_chunk = "Repeated memory."

    writer.chunker.chunk_text = Mock(
        return_value = [repeated_chunk, repeated_chunk]
    )

    repository.get_by_content_hash = AsyncMock(return_value = None)

    embedding_service.generate_embeddings = AsyncMock(
        return_value = [[0.1] * 1024]
    )

    repository.save_memories_batch = AsyncMock(return_value=[1])

    company_id = uuid4()

    result = await writer.write(
        company_id = company_id,
        text = "Some input"
    )

    assert result == [1]

    embedding_service.generate_embeddings.assert_awaited_once_with(
        [repeated_chunk]
    )

    repository.save_memories_batch.assert_awaited_once_with([{
        "company_id": company_id,
        "memory_type": "semantic",
        "content": repeated_chunk,
        "content_hash": create_content_hash(repeated_chunk),
        "metadata": {},
        "importance": 0.5,
        "embedding": [0.1] * 1024,
    }])


async def test_memory_writer_rejects_embedding_count_mismatch():
    writer, repository, embedding_service = await create_writer()

    writer.chunker.chunk_text = Mock(
        return_value = [
            "memory one",
            "memory two",
        ]
    )

    repository.get_by_content_hash = AsyncMock(
        return_value = None
    )

    embedding_service.generate_embeddings = AsyncMock(
        return_value = [
            [0.1] * 1024
        ]  # only one embedding, but two chunks
    )

    with pytest.raises(ValueError):
        await writer.write(
            company_id = uuid4(),
            text = "test",
        )


async def test_memory_writer_returns_existing_memories_only():

    writer, repository, embedding_service = await create_writer()

    existing_memory = {
        "id": 123,
        "content": "already saved",
    }

    repository.get_by_content_hash = AsyncMock(
        return_value = existing_memory["id"]
    )

    embedding_service.generate_embeddings = AsyncMock()

    repository.save_memories_batch = AsyncMock()

    result = await writer.write(
        company_id = uuid4(),
        text = "already saved",
    )

    assert result == [existing_memory["id"]]

    embedding_service.generate_embeddings.assert_not_called()

    repository.save_memories_batch.assert_not_called()