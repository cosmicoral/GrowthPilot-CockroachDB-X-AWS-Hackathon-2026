import pytest

from backend.memory.extraction import MemoryExtractionPolicy


class MockExtractionClient:
    def __init__(self, response: str):
        self.response = response

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        return self.response


@pytest.mark.asyncio
async def test_extracts_durable_user_preference():
    client = MockExtractionClient(
        """
        {
            "memories": [
                {
                    "content": "The founder prefers concise technical explanations.",
                    "memory_type": "user",
                    "importance": 0.85,
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
        "The founder said they prefer concise technical explanations."
    )

    assert len(result.memories) == 1
    assert result.memories[0].memory_type == "user"
    assert result.memories[0].importance == 0.85


@pytest.mark.asyncio
async def test_rejects_irrelevant_conversation():
    client = MockExtractionClient(
        '{"memories": []}'
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract(
        "Hey, how are you? Thanks!"
    )

    assert result.memories == []


@pytest.mark.asyncio
async def test_extracts_business_context():
    client = MockExtractionClient(
        """
        {
            "memories": [
                {
                    "content": "GrowthPilot targets B2B founders.",
                    "memory_type": "semantic",
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
        "GrowthPilot targets B2B founders."
    )

    assert result.memories[0].memory_type == "semantic"
    assert result.memories[0].importance == 0.9


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

    with pytest.raises(ValueError, match="invalid structured output"):
        await policy.extract("Some input")


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

    with pytest.raises(ValueError, match="invalid structured output"):
        await policy.extract("Some input")


@pytest.mark.asyncio
async def test_empty_input_returns_no_memories():
    client = MockExtractionClient(
        '{"memories": []}'
    )

    policy = MemoryExtractionPolicy(client)

    result = await policy.extract("   ")

    assert result.memories == []