import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from backend.agents.content import ContentAgent
from backend.agents.context import AgentContext
from backend.memory.store import MemoryHit
from scripts.seed_demo_founder import DEMO_MEMORIES, COMPANY_ID

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
        company_id=COMPANY_ID,
        bedrock_client=mock_bedrock_client,
        memory_repository=mock_memory_repo
    )

@pytest.mark.asyncio
async def test_content_agent_with_memories(agent_context):
    agent = ContentAgent(context=agent_context)
    
    # Mock MemoryStore returning the T13 seeded context
    # Convert DEMO_MEMORIES into MemoryHit objects
    hits = []
    for mem in DEMO_MEMORIES:
        hits.append(MemoryHit(
            id=uuid.uuid4(),
            company_id=COMPANY_ID,
            content=mem["content"],
            memory_type=mem["memory_type"],
            created_at="2026-08-12T00:00:00Z"
        ))
    
    agent_context.memory_repository.search.return_value = hits

    result = await agent.run(prompt="Write a LinkedIn post")
    
    assert result.success is True
    assert result.output == "Generated Mock Content"
    
    # Verify memory search was called correctly with the new reflection type
    agent_context.memory_repository.search.assert_called_once_with(
        company_id=COMPANY_ID,
        query="Write a LinkedIn post",
        k=5,
        types=["episodic", "semantic", "user", "task", "reflection"]
    )
    
    # Verify bedrock was called with the context
    agent_context.bedrock_client.generate_text.assert_called_once()
    system_prompt = agent_context.bedrock_client.generate_text.call_args.kwargs["system_prompt"]
    
    # Assert that specific seeded context from FlowForge AI is present in the prompt
    assert "Sarah's initial positioning for FlowForge AI" in system_prompt  # User memory
    assert "GitHub Copilot, Linear, Jira" in system_prompt  # Semantic memory
    assert "Future content should focus more on practical engineering" in system_prompt  # Reflection memory
    
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
