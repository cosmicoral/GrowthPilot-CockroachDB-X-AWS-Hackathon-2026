import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from backend.agents.content import ContentAgent
from backend.agents.context import AgentContext
from backend.memory.store import MemoryHit

@pytest.fixture
def mock_bedrock_client():
    client = MagicMock()
    client.generate_text = AsyncMock(return_value="Generated Mock Content")
    return client

@pytest.fixture
def mock_memory_repo():
    repo = MagicMock()
    repo.search = AsyncMock()
    repo.write = AsyncMock()
    return repo

@pytest.fixture
def agent_context(mock_bedrock_client, mock_memory_repo):
    return AgentContext(
        company_id=uuid.uuid4(),
        bedrock_client=mock_bedrock_client,
        memory_repository=mock_memory_repo
    )

@pytest.mark.asyncio
async def test_content_agent_with_memories(agent_context):
    agent = ContentAgent(context=agent_context)
    
    # Mock MemoryStore returning context
    mock_hit = MemoryHit(
        id=uuid.uuid4(),
        company_id=agent_context.company_id,
        content="Target audience is enterprise SaaS startups.",
        memory_type="semantic",
        created_at="2026-08-12T00:00:00Z"
    )
    agent_context.memory_repository.search.return_value = [mock_hit]

    result = await agent.run(prompt="Write a LinkedIn post")
    
    assert result.success is True
    assert result.output == "Generated Mock Content"
    
    # Verify memory search was called correctly
    agent_context.memory_repository.search.assert_called_once_with(
        company_id=agent_context.company_id,
        query="Write a LinkedIn post",
        k=5,
        types=["episodic", "semantic", "user", "task"]
    )
    
    # Verify bedrock was called with the context
    agent_context.bedrock_client.generate_text.assert_called_once()
    system_prompt = agent_context.bedrock_client.generate_text.call_args.kwargs["system_prompt"]
    assert "Target audience is enterprise SaaS startups." in system_prompt
    
    # Verify the generated content was saved back to memory
    agent_context.memory_repository.write.assert_called_once()
    write_args = agent_context.memory_repository.write.call_args.kwargs
    assert write_args["memory_type"] == "task"
    assert "Generated Content" in write_args["content"]


@pytest.mark.asyncio
async def test_content_agent_empty_context(agent_context):
    agent = ContentAgent(context=agent_context)
    
    # Mock MemoryStore returning NO context
    agent_context.memory_repository.search.return_value = []

    result = await agent.run(prompt="Write a Twitter post")
    
    assert result.success is True
    assert result.output == "Generated Mock Content"
    
    # Verify bedrock was called with the empty context fallback
    agent_context.bedrock_client.generate_text.assert_called_once()
    system_prompt = agent_context.bedrock_client.generate_text.call_args.kwargs["system_prompt"]
    assert "No specific background context found" in system_prompt
