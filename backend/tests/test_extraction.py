from unittest.mock import AsyncMock

import pytest

from backend.memory.extraction import MemoryExtractionPolicy
from backend.tests.mocks.bedrock import MockBedrockClient


class MockExtractionClient:
    def __init__(self, response: str):
        self.response = response

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
    ) -> str:
        return self.response


@pytest.mark.asyncio
async def test_extracts_valid_memories():
    client = MockExtractionClient(
        """
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

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract(
        "The founder prefers concise explanations."
    )

    assert len(result.memories) == 1
    assert result.memories[0].content == (
        "The founder prefers concise explanations."
    )
    assert result.memories[0].memory_type == "user"
    assert result.memories[0].importance == 0.9
    assert result.memories[0].metadata == {
        "source": "conversation"
    }


@pytest.mark.asyncio
async def test_extracts_multiple_memories():
    client = MockExtractionClient(
        """
        {
            "memories": [
                {
                    "content": "The founder prefers concise explanations.",
                    "memory_type": "user",
                    "importance": 0.9,
                    "metadata": {}
                },
                {
                    "content": "The company uses CockroachDB.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some conversation.")

    assert len(result.memories) == 2


@pytest.mark.asyncio
async def test_returns_empty_for_empty_input():
    client = MockExtractionClient(
        '{"memories": [{"content": "Should not be used"}]}'
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("   ")

    assert result.memories == []


@pytest.mark.asyncio
async def test_returns_empty_when_model_returns_no_memories():
    client = MockExtractionClient(
        """
        {
            "memories": []
        }
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Just a greeting.")

    assert result.memories == []


@pytest.mark.asyncio
async def test_rejects_invalid_memory_type():
    client = MockExtractionClient(
        """
        {
            "memories": [
                {
                    "content": "Some memory",
                    "memory_type": "invalid",
                    "importance": 0.5,
                    "metadata": {}
                }
            ]
        }
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some input")

    assert result.memories == []


@pytest.mark.asyncio
async def test_rejects_invalid_importance():
    client = MockExtractionClient(
        """
        {
            "memories": [
                {
                    "content": "Some memory",
                    "memory_type": "semantic",
                    "importance": 1.5,
                    "metadata": {}
                }
            ]
        }
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some input")

    assert result.memories == []


@pytest.mark.asyncio
async def test_extraction_rejects_sensitive_content():
    bedrock_client = MockBedrockClient()

    bedrock_client.generate_text = AsyncMock(
        return_value="""
        {
            "memories": [
                {
                    "content": "The user's password is Secret123.",
                    "memory_type": "user",
                    "importance": 0.9,
                    "metadata": {}
                },
                {
                    "content": "The company uses CockroachDB.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }
        """
    )

    policy = MemoryExtractionPolicy(bedrock_client)

    result = await policy.extract(
        "Some conversation containing sensitive information."
    )

    assert len(result.memories) == 1
    assert result.memories[0].content == (
        "The company uses CockroachDB."
    )


@pytest.mark.asyncio
async def test_extraction_rejects_sensitive_metadata():
    bedrock_client = MockBedrockClient()

    bedrock_client.generate_text = AsyncMock(
        return_value="""
        {
            "memories": [
                {
                    "content": "Safe memory.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {
                        "api_key": "secret-value"
                    }
                },
                {
                    "content": "The company uses CockroachDB.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }
        """
    )

    policy = MemoryExtractionPolicy(bedrock_client)

    result = await policy.extract(
        "Some conversation."
    )

    assert len(result.memories) == 1
    assert result.memories[0].content == (
        "The company uses CockroachDB."
    )


@pytest.mark.asyncio
async def test_accepts_fenced_json():
    client = MockExtractionClient(
        """
        Here is the extracted memory:

        ```json
        {
            "memories": [
                {
                    "content": "The company uses CockroachDB.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }
        ```

        """

    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some conversation.")

    assert len(result.memories) == 1
    assert result.memories[0].content == (
        "The company uses CockroachDB."
    )


@pytest.mark.asyncio
async def test_accepts_json_embedded_in_prose():
    client = MockExtractionClient(
        """
        I found one durable memory:

        {
            "memories": [
                {
                    "content": "The company uses CockroachDB.",
                    "memory_type": "semantic",
                    "importance": 0.8,
                    "metadata": {}
                }
            ]
        }

        Hope this helps.
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some conversation.")

    assert len(result.memories) == 1
    assert result.memories[0].content == (
        "The company uses CockroachDB."
    )


@pytest.mark.asyncio
async def test_malformed_output_returns_empty_result():
    client = MockExtractionClient(
        """
        This is not valid JSON and cannot be parsed.
        """
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("Some conversation.")

    assert result.memories == []