from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agents.base import AgentResult
from backend.agents.context import AgentContext
from backend.agents.market_research import MarketResearchAgent
from backend.api.deps import get_current_company_id
from backend.api.research import router as research_router
from backend.memory.hash import create_content_hash
from backend.memory.store import MemoryHit
from backend.tests.mocks.bedrock import MockBedrockClient
from backend.tests.mocks.repository import MockMemoryRepository

SAMPLE_COMPANY_PROFILE = {
    "name": "EcoCharge",
    "industry": "CleanTech",
    "description": "Smart ultra-fast EV charging stations powered by solar grids.",
    "website": "https://ecocharge.example.com",
}

SAMPLE_LLM_RESEARCH = (
    "COMPETITOR LANDSCAPE:\n"
    "ChargePoint and EVgo dominate municipal charging networks. "
    "Tesla Supercharger leads proprietary networks. EcoCharge differentiates "
    "with integrated solar micro-grids and battery buffer storage, reducing "
    "grid demand charges by 40%.\n\n"
    "INDUSTRY TRENDS:\n"
    "EV adoption is accelerating worldwide with an EU mandate for "
    "zero-emission vehicles by 2035. Grid congestion is forcing operators "
    "toward localized energy storage and renewable generation.\n\n"
    "CUSTOMER PAIN POINTS:\n"
    "EV drivers face long wait times at broken charging ports. Commercial "
    "fleet operators suffer expensive demand charges from peak grid draws. "
    "High installation costs slow rural charging station deployments."
)


def create_test_agent():
    company_id = uuid4()
    mock_bedrock = MockBedrockClient()
    mock_bedrock.generate_text = AsyncMock(return_value=SAMPLE_LLM_RESEARCH)
    mock_repo = MockMemoryRepository()

    context = AgentContext(
        company_id=company_id,
        bedrock_client=mock_bedrock,
        memory_repository=mock_repo,
    )

    agent = MarketResearchAgent(context)
    return agent, context, mock_bedrock, mock_repo


def test_market_research_agent_initialization():
    agent, context, _, _ = create_test_agent()
    assert agent.name == "market_research"
    assert agent.context == context


@pytest.mark.asyncio
async def test_fetch_stage_llm_generation():
    agent, _, mock_bedrock, _ = create_test_agent()

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        trigger_source="onboarding",
    )

    assert result.success is True
    assert result.agent_name == "market_research"

    mock_bedrock.generate_text.assert_called_once()
    call_args = mock_bedrock.generate_text.call_args[1]
    assert "EcoCharge" in call_args["prompt"]
    assert "CleanTech" in call_args["prompt"]


@pytest.mark.asyncio
async def test_fetch_stage_custom_research_override():
    agent, _, mock_bedrock, _ = create_test_agent()

    custom_text = "COMPETITOR LANDSCAPE: Custom external research text about local competitors."

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        custom_research_text=custom_text,
        trigger_source="manual",
    )

    assert result.success is True
    mock_bedrock.generate_text.assert_not_called()
    assert result.output["raw_research"] == custom_text
    metadata = result.output["structured_chunks"][0]["metadata"]
    assert metadata["content_origin"] == "user_supplied"
    assert metadata["generated_by"] == "user_input"
    assert metadata["verified"] is False


@pytest.mark.asyncio
async def test_structure_stage_chunking_and_categorization():
    agent, _, _, _ = create_test_agent()

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        trigger_source="onboarding",
    )

    structured_chunks = result.output["structured_chunks"]
    assert len(structured_chunks) >= 3

    categories = [chunk["category"] for chunk in structured_chunks]
    assert "competitors" in categories
    assert "trends" in categories
    assert "pain_points" in categories

    for chunk in structured_chunks:
        meta = chunk["metadata"]
        assert meta["source"] == "market_research"
        assert meta["company_name"] == "EcoCharge"
        assert meta["industry"] == "CleanTech"
        assert meta["agent"] == "market_research"
        assert meta["trigger_source"] == "onboarding"
        assert meta["content_origin"] == "llm_generated"
        assert meta["generated_by"] == "bedrock"
        assert meta["verified"] is False
        assert meta["confidence"] == "unverified"
        assert chunk["importance"] == 0.7


def test_structure_stage_preserves_explicit_section_heading():
    agent, _, _, _ = create_test_agent()
    chunks = agent._structure_research(
        raw_research=(
            "COMPETITOR LANDSCAPE:\n"
            "Competitors discuss customer pain points in their messaging."
        ),
        company_name="EcoCharge",
        industry="CleanTech",
        trigger_source="manual",
    )

    assert chunks
    assert {chunk["category"] for chunk in chunks} == {"competitors"}


@pytest.mark.asyncio
async def test_dedup_stage_content_hash():
    agent, context, mock_bedrock, mock_repo = create_test_agent()

    custom_text = "COMPETITOR LANDSCAPE: ChargePoint and EVgo dominate municipal charging networks."
    existing_hash = create_content_hash(custom_text)

    existing_id = uuid4()
    mock_repo.memories.append({
        "id": existing_id,
        "company_id": context.company_id,
        "content": custom_text,
        "content_hash": existing_hash,
    })

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        custom_research_text=custom_text,
        trigger_source="manual",
    )

    assert result.success is True
    output = result.output
    assert output["memories_deduplicated"] == 1
    assert output["memories_created"] == 0
    assert existing_id in output["saved_memory_ids"]


@pytest.mark.asyncio
async def test_running_same_research_twice_is_idempotent():
    agent, _, _, _ = create_test_agent()

    first = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        custom_research_text=SAMPLE_LLM_RESEARCH,
        trigger_source="manual",
    )
    second = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        custom_research_text=SAMPLE_LLM_RESEARCH,
        trigger_source="manual",
    )

    assert first.success is True
    assert first.output["memories_created"] > 0
    assert second.success is True
    assert second.output["memories_created"] == 0
    assert second.output["memories_deduplicated"] > 0


@pytest.mark.asyncio
async def test_embed_and_persist_stage():
    agent, context, _, mock_repo = create_test_agent()

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        trigger_source="periodic",
    )

    assert result.success is True
    saved_ids = result.output["saved_memory_ids"]
    assert len(saved_ids) > 0

    assert len(mock_repo.memories) == len(saved_ids)
    for mem in mock_repo.memories:
        assert mem["memory_type"] == "semantic"
        assert len(mem["embedding"]) == 1024
        assert mem["metadata"]["source"] == "market_research"
        assert mem["metadata"]["trigger_source"] == "periodic"


@pytest.mark.asyncio
async def test_retrieve_prior_memories():
    agent, context, _, mock_repo = create_test_agent()

    hit = MemoryHit(
        id=uuid4(),
        company_id=context.company_id,
        content="Prior competitor analysis",
        memory_type="semantic",
        metadata={"source": "market_research"},
        importance=0.7,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.recent = AsyncMock(return_value=[hit])

    prior = await agent.retrieve_memories()
    assert len(prior) == 1
    assert prior[0].content == "Prior competitor analysis"


@pytest.mark.asyncio
async def test_prior_research_is_used_for_llm_refresh():
    agent, context, mock_bedrock, mock_repo = create_test_agent()
    prior_content = "Prior finding: regional installers are gaining share."
    mock_repo.recent = AsyncMock(
        return_value=[
            MemoryHit(
                id=uuid4(),
                company_id=context.company_id,
                content=prior_content,
                memory_type="semantic",
                metadata={"source": "market_research"},
                importance=0.7,
                created_at=datetime.now(timezone.utc),
            )
        ]
    )

    result = await agent.run(
        company_profile=SAMPLE_COMPANY_PROFILE,
        prompt="Find newly emerging competitors",
        trigger_source="periodic",
    )

    assert result.success is True
    prompt = mock_bedrock.generate_text.await_args.kwargs["prompt"]
    assert "Find newly emerging competitors" in prompt
    assert prior_content in prompt


def test_api_run_market_research_endpoint():
    test_app = FastAPI()
    test_app.include_router(research_router)

    company_id = uuid4()
    test_app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_result = AgentResult(
        agent_name="market_research",
        success=True,
        output={
            "company_id": str(company_id),
            "company_name": "EcoCharge",
            "industry": "CleanTech",
            "trigger_source": "onboarding",
            "raw_research": SAMPLE_LLM_RESEARCH,
            "structured_chunks": [],
            "saved_memory_ids": [],
            "memories_created": 3,
            "memories_deduplicated": 0,
        },
    )

    with patch("backend.api.research.database") as mock_db, patch(
        "backend.api.research.MarketResearchAgent"
    ) as mock_agent_cls:
        mock_conn = AsyncMock()
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchrow.return_value = {
            "id": company_id,
            "name": "EcoCharge",
            "email": "contact@ecocharge.example.com",
            "website": "https://ecocharge.example.com",
            "industry": "CleanTech",
            "description": "EV charging startup",
        }

        mock_agent_instance = MagicMock()
        mock_agent_instance.run = AsyncMock(return_value=mock_result)
        mock_agent_cls.return_value = mock_agent_instance

        with TestClient(test_app) as client:
            response = client.post(
                "/api/research/run",
                json={"trigger": "onboarding"},
                headers={"Authorization": f"Bearer {company_id}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["agent_name"] == "market_research"
            assert data["success"] is True
            assert data["output"]["company_name"] == "EcoCharge"

    test_app.dependency_overrides.clear()


def test_api_get_research_memories_endpoint():
    test_app = FastAPI()
    test_app.include_router(research_router)

    company_id = uuid4()
    test_app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_memories = [
        MemoryHit(
            id=uuid4(),
            company_id=company_id,
            content="Competitor analysis memory",
            memory_type="semantic",
            metadata={"source": "market_research", "category": "competitors"},
            importance=0.7,
            created_at=datetime.now(timezone.utc),
        )
    ]

    with patch("backend.api.research.MemoryRepository") as mock_repo_cls:
        mock_repo_instance = MagicMock()
        mock_repo_instance.recent = AsyncMock(return_value=mock_memories)
        mock_repo_cls.return_value = mock_repo_instance

        with TestClient(test_app) as client:
            response = client.get(
                "/api/research/memories?limit=10",
                headers={"Authorization": f"Bearer {company_id}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["content"] == "Competitor analysis memory"
            assert data[0]["metadata"]["source"] == "market_research"

    test_app.dependency_overrides.clear()
