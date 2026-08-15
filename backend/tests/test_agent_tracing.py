from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agents.base import Agent, AgentContext
from backend.agents.trace import AgentTraceHit
from backend.api.deps import get_current_company_id
from backend.api.traces import router as traces_router
from backend.memory.store import MemoryHit

MIGRATION_FILE = Path(__file__).parent.parent / "migrations" / "003_agent_traces.sql"


class SuccessAgent(Agent):
    @property
    def name(self) -> str:
        return "success-agent"

    async def retrieve_memories(self, *args, **kwargs):
        return [
            MemoryHit(
                id=uuid4(),
                company_id=self.context.company_id,
                content="Market trend memory chunk",
                memory_type="semantic",
                metadata={"source": "market_research"},
                importance=0.7,
                similarity=0.92,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def process(self, retrieved_memories, *args, **kwargs):
        return {"status": "processed", "retrieved_count": len(retrieved_memories)}


class FailingAgent(Agent):
    @property
    def name(self) -> str:
        return "failing-agent"

    async def process(self, retrieved_memories, *args, **kwargs):
        raise RuntimeError("LLM rate limit exceeded")


class JsonValueAgent(Agent):
    def __init__(self, context, output_id):
        super().__init__(context)
        self.output_id = output_id

    @property
    def name(self) -> str:
        return "json-value-agent"

    async def process(self, retrieved_memories, *args, **kwargs):
        return {
            "saved_memory_ids": [self.output_id],
            "nested": {"memory_id": self.output_id},
        }


def test_migration_003_exists_and_valid():
    assert MIGRATION_FILE.exists(), "003_agent_traces.sql missing"
    sql = MIGRATION_FILE.read_text().lower()
    assert "create table if not exists agent_traces" in sql
    assert "company_id" in sql
    assert "agent_name" in sql
    assert "duration_ms" in sql
    assert "memories_retrieved" in sql
    assert "success" in sql


@pytest.mark.asyncio
async def test_agent_run_records_trace_on_success():
    company_id = uuid4()
    mock_bedrock = MagicMock()
    mock_memory_repo = MagicMock()
    mock_trace_repo = MagicMock()
    mock_trace_repo.save_trace = AsyncMock(return_value=uuid4())

    context = AgentContext(
        company_id=company_id,
        bedrock_client=mock_bedrock,
        memory_repository=mock_memory_repo,
        trace_repository=mock_trace_repo,
    )

    agent = SuccessAgent(context)
    result = await agent.run(task="analyze_market")

    assert result.success is True
    assert result.agent_name == "success-agent"
    assert result.output["status"] == "processed"

    mock_trace_repo.save_trace.assert_called_once()
    kwargs = mock_trace_repo.save_trace.call_args[1]

    assert kwargs["company_id"] == company_id
    assert kwargs["agent_name"] == "success-agent"
    assert kwargs["duration_ms"] > 0
    assert kwargs["success"] is True
    assert kwargs["error"] is None

    # Check memories retrieved summary
    memories_summary = kwargs["memories_retrieved"]
    assert len(memories_summary) == 1
    assert memories_summary[0]["similarity"] == 0.92
    assert memories_summary[0]["memory_type"] == "semantic"


@pytest.mark.asyncio
async def test_agent_run_records_trace_on_failure():
    company_id = uuid4()
    mock_bedrock = MagicMock()
    mock_memory_repo = MagicMock()
    mock_trace_repo = MagicMock()
    mock_trace_repo.save_trace = AsyncMock(return_value=uuid4())

    context = AgentContext(
        company_id=company_id,
        bedrock_client=mock_bedrock,
        memory_repository=mock_memory_repo,
        trace_repository=mock_trace_repo,
    )

    agent = FailingAgent(context)
    result = await agent.run()

    assert result.success is False
    assert "LLM rate limit exceeded" in result.output

    mock_trace_repo.save_trace.assert_called_once()
    kwargs = mock_trace_repo.save_trace.call_args[1]

    assert kwargs["company_id"] == company_id
    assert kwargs["agent_name"] == "failing-agent"
    assert kwargs["success"] is False
    assert kwargs["error"] == "LLM rate limit exceeded"


@pytest.mark.asyncio
async def test_trace_recording_failure_does_not_break_agent():
    company_id = uuid4()
    mock_bedrock = MagicMock()
    mock_memory_repo = MagicMock()
    mock_trace_repo = MagicMock()
    mock_trace_repo.save_trace = AsyncMock(side_effect=RuntimeError("Database pool closed"))

    context = AgentContext(
        company_id=company_id,
        bedrock_client=mock_bedrock,
        memory_repository=mock_memory_repo,
        trace_repository=mock_trace_repo,
    )

    agent = SuccessAgent(context)
    result = await agent.run()

    # Main execution succeeds even if tracing repository fails
    assert result.success is True
    assert result.output["status"] == "processed"


@pytest.mark.asyncio
async def test_trace_recursively_serializes_nested_uuids():
    company_id = uuid4()
    input_id = uuid4()
    output_id = uuid4()
    trace_repository = MagicMock()
    trace_repository.save_trace = AsyncMock(return_value=uuid4())
    context = AgentContext(
        company_id=company_id,
        bedrock_client=MagicMock(),
        memory_repository=MagicMock(),
        trace_repository=trace_repository,
    )

    result = await JsonValueAgent(context, output_id).run(
        company_profile={"founder_id": input_id},
    )

    assert result.success is True
    trace = trace_repository.save_trace.await_args.kwargs
    assert trace["input"]["kwargs"]["company_profile"]["founder_id"] == str(
        input_id
    )
    assert trace["output"]["saved_memory_ids"] == [str(output_id)]
    assert trace["output"]["nested"]["memory_id"] == str(output_id)


def test_agent_trace_output_accepts_non_dictionary_json_values():
    trace = AgentTraceHit(
        id=uuid4(),
        company_id=uuid4(),
        agent_name="content",
        start_time=datetime.now(timezone.utc),
        duration_ms=10.0,
        output=["draft", {"status": "ready"}],
        success=True,
        created_at=datetime.now(timezone.utc),
    )

    assert trace.output == ["draft", {"status": "ready"}]


def test_api_list_agent_traces_endpoint():
    test_app = FastAPI()
    test_app.include_router(traces_router)

    company_id = uuid4()
    test_app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_trace = AgentTraceHit(
        id=uuid4(),
        company_id=company_id,
        agent_name="market_research",
        start_time=datetime.now(timezone.utc),
        duration_ms=245.5,
        input={"kwargs": {"trigger_source": "onboarding"}},
        output={"memories_created": 3},
        memories_retrieved=[],
        success=True,
        error=None,
        created_at=datetime.now(timezone.utc),
    )

    with patch("backend.api.traces.TraceRepository") as mock_repo_cls:
        mock_repo_instance = MagicMock()
        mock_repo_instance.get_recent_traces = AsyncMock(return_value=[mock_trace])
        mock_repo_cls.return_value = mock_repo_instance

        with TestClient(test_app) as client:
            response = client.get(
                "/api/traces?limit=10",
                headers={"Authorization": f"Bearer {company_id}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["agent_name"] == "market_research"
            assert data[0]["duration_ms"] == 245.5
            assert data[0]["success"] is True

    test_app.dependency_overrides.clear()


def test_api_get_agent_trace_by_id_endpoint():
    test_app = FastAPI()
    test_app.include_router(traces_router)

    company_id = uuid4()
    trace_id = uuid4()
    test_app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_trace = AgentTraceHit(
        id=trace_id,
        company_id=company_id,
        agent_name="market_research",
        start_time=datetime.now(timezone.utc),
        duration_ms=180.0,
        input={},
        output={},
        memories_retrieved=[],
        success=True,
        created_at=datetime.now(timezone.utc),
    )

    with patch("backend.api.traces.TraceRepository") as mock_repo_cls:
        mock_repo_instance = MagicMock()
        mock_repo_instance.get_trace_by_id = AsyncMock(return_value=mock_trace)
        mock_repo_cls.return_value = mock_repo_instance

        with TestClient(test_app) as client:
            response = client.get(
                f"/api/traces/{trace_id}",
                headers={"Authorization": f"Bearer {company_id}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(trace_id)
            assert data["agent_name"] == "market_research"

    test_app.dependency_overrides.clear()
