from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.memory.chunker import TextChunker
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.extraction import MemoryExtractionPolicy
from backend.memory.writer import MemoryWriter
from backend.tests.mocks.bedrock import MockBedrockClient
from backend.tests.mocks.repository import MockMemoryRepository


async def create_writer(extraction_response='{"memories": []}'):

    chunker = TextChunker()

    bedrock_client = MockBedrockClient()
    bedrock_client.generate_text = AsyncMock(
        return_value = extraction_response
    )

    bedrock_service = BedrockEmbeddingService(bedrock_client = bedrock_client)

    repository = MockMemoryRepository()

    extraction_policy = MemoryExtractionPolicy(
        bedrock_client
    )

    writer = MemoryWriter(
        chunker = chunker,
        embedding_service = bedrock_service,
        repository = repository,
        extraction_policy = extraction_policy
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

    writer, repository, _ = await create_writer(
        extraction_response = """
        {
            "memories": [
                {
                    "content": "A team lead will be away this evening.",
                    "memory_type": "episodic",
                    "importance": 0.7,
                    "metadata": {
                        "source": "conversation"
                    }
                }
            ]
        }
        """
    )

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

    writer, repository, _ = await create_writer(
        extraction_response = """
        {
            "memories": [
                {
                    "content": "First memory.",
                    "memory_type": "semantic",
                    "importance": 0.7,
                    "metadata": {}
                },
                {
                    "content": "Second memory.",
                    "memory_type": "episodic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }
        """
    )

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

    writer, repository, embedding_service = await create_writer(
        extraction_response="""
        {
            "memories": [
                {
                    "content": "Existing memory",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                }
            ]
        }
        """
    )


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


async def test_memory_writer_deduplicates_repeated_memories():
    writer, repository, embedding_service = await create_writer(
        extraction_response="""
        {
            "memories": [
                {
                    "content": "Repeated memory.",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                },
                {
                    "content": "Repeated memory.",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                }
            ]
        }
        """
    )

    repository.get_by_content_hash = AsyncMock(return_value=None)

    embedding_service.generate_embeddings = AsyncMock(
        return_value=[[0.1] * 1024]
    )

    repository.save_memories_batch = AsyncMock(return_value=[1])

    result = await writer.write(
        company_id=uuid4(),
        text="Some input"
    )

    assert result == [1]

    embedding_service.generate_embeddings.assert_awaited_once_with(
        ["Repeated memory."]
    )

async def test_memory_writer_rejects_embedding_count_mismatch():
    writer, repository, embedding_service = await create_writer(
        extraction_response="""
        {
            "memories": [
                {
                    "content": "memory one",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                },
                {
                    "content": "memory two",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                }
            ]
        }
        """
    )

    repository.get_by_content_hash = AsyncMock(
        return_value=None
    )

    embedding_service.generate_embeddings = AsyncMock(
        return_value=[
            [0.1] * 1024
        ]
    )

    with pytest.raises(ValueError):
        await writer.write(
            company_id=uuid4(),
            text="test",
        )

async def test_memory_writer_returns_existing_memories_only():

    writer, repository, embedding_service = await create_writer(
        extraction_response="""
        {
            "memories": [
                {
                    "content": "already saved",
                    "memory_type": "semantic",
                    "importance": 0.5,
                    "metadata": {}
                }
            ]
        }
        """
    )

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

@pytest.mark.asyncio
async def test_memory_writer_uses_extracted_memory_policy():
    writer, repository, embedding_service = await create_writer(
        extraction_response="""
        {
            "memories": [
                {
                    "content": "The founder prefers concise explanations.",
                    "memory_type": "user",
                    "importance": 0.9,
                    "metadata": {
                        "source": "conversation"
                    }
                }
            ]
        }
        """
    )

    embedding_service.generate_embeddings = AsyncMock(
        return_value=[[0.1] * 1024]
    )

    repository.get_by_content_hash = AsyncMock(return_value=None)
    repository.save_memories_batch = AsyncMock(return_value=[123])

    result = await writer.write(
        company_id=uuid4(),
        text="The founder prefers concise explanations.",
    )

    assert result == [123]

    repository.save_memories_batch.assert_awaited_once()

    saved_memory = repository.save_memories_batch.call_args.args[0][0]

    assert saved_memory["memory_type"] == "user"
    assert saved_memory["importance"] == 0.9
    assert saved_memory["metadata"] == {
        "source": "conversation"
    }