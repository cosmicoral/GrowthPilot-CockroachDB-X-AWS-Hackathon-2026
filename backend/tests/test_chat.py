import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.agents.base import AgentResult
from backend.agents.planner import PlannerDecision, PlannerOutput
from backend.api.chat import router as chat_router
from backend.api.deps import get_current_company_id
from backend.memory.store import MemoryHit

app = FastAPI()
app.include_router(chat_router)
client = TestClient(app)


@pytest.fixture
def company_id():
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    yield company_id
    app.dependency_overrides.clear()


def planner_success_result(
    response: str = "Hello World",
) -> AgentResult:
    return AgentResult(
        agent_name="planner",
        success=True,
        output=PlannerOutput(
            decision=PlannerDecision(
                intents=["general"],
                execution="single",
                reason="General question",
            ),
            response=response,
            sub_results=[
                AgentResult(
                    agent_name="memory-qa",
                    success=True,
                    output=response,
                )
            ],
        ),
    )


@patch("backend.api.chat.PlannerAgent")
@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_chat_stream_success(
    mock_bedrock_class,
    mock_repo_class,
    mock_planner_class,
    company_id,
):
    """Planner output should be emitted as multiple token events and a done event."""

    planner_response = (
        "This is a longer planner response that should be emitted "
        "as multiple SSE token events."
    )

    mock_repo = AsyncMock()
    mock_repo.search.return_value = []
    mock_repo_class.return_value = mock_repo

    mock_planner = AsyncMock()
    mock_planner.run.return_value = planner_success_result(
        response = planner_response,
    )
    mock_planner_class.return_value = mock_planner

    response = client.post(
        "/api/chat/stream",
        json={"message": "Hi"},
    )

    assert response.status_code == status.HTTP_200_OK

    content = response.text

    assert 'data: {"type": "memories", "memories": []}\n\n' in content
    assert '"type": "done"' in content
    assert '"partial": false' in content

    token_events = [
        line
        for line in content.splitlines()
        if line.startswith('data: {"type": "token"')
    ]

    assert len(token_events) > 1

    token_texts = []

    for event in token_events:
        data = event.removeprefix("data: ")
        token_texts.append(json.loads(data)["text"])

    assert "".join(token_texts) == planner_response

    mock_planner.run.assert_awaited_once_with(
        message="Hi",
    )

    registered_agents = mock_planner_class.call_args.kwargs["agents"]

    assert set(registered_agents) == {
        "market_research",
        "content",
        "analytics-reflection-agent",
    }


@patch("backend.api.chat.PlannerAgent")
@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_chat_stream_error_event(
    mock_bedrock_class,
    mock_repo_class,
    mock_planner_class,
    company_id,
):
    """A failed planner result should be represented as an SSE error."""

    mock_repo = AsyncMock()
    mock_repo.search.return_value = []
    mock_repo_class.return_value = mock_repo

    mock_planner = AsyncMock()
    mock_planner.run.return_value = AgentResult(
        agent_name="planner",
        success=False,
        output="Planner failed",
    )
    mock_planner_class.return_value = mock_planner

    response = client.post(
        "/api/chat/stream",
        json={"message": "Hi"},
    )

    assert response.status_code == status.HTTP_200_OK

    content = response.text

    assert 'data: {"type": "memories", "memories": []}\n\n' in content
    assert '"type": "error"' in content
    assert "Planner failed" in content
    assert '"type": "done"' not in content


@patch("backend.api.chat.ContentAgent")
@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_generate_content_success(
    mock_bedrock_class,
    mock_repo_class,
    mock_agent_class,
    company_id,
):
    mock_agent = AsyncMock()
    mock_agent.run.return_value = AgentResult(
        agent_name="content",
        success=True,
        output="Generated post",
    )
    reflection_id = uuid4()
    mock_agent.retrieved_memories = [
        MemoryHit(
            id=reflection_id,
            company_id=company_id,
            content="Workflow posts performed best.",
            memory_type="reflection",
            metadata={"source": "analytics-reflection-agent"},
            importance=0.9,
            similarity=0.94,
            created_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        )
    ]
    mock_agent_class.return_value = mock_agent

    response = client.post(
        "/api/chat/generate-content",
        json={"prompt": "test prompt"},
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["content"] == "Generated post"
    assert len(payload["memories"]) == 1
    assert payload["memories"][0]["id"] == str(reflection_id)
    assert payload["memories"][0]["memory_type"] == "reflection"
    assert payload["memories"][0]["metadata"] == {
        "source": "analytics-reflection-agent",
    }

    mock_agent.run.assert_awaited_once_with(
        prompt="test prompt",
    )


@patch("backend.api.chat.ContentAgent")
@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_generate_content_failure(
    mock_bedrock_class,
    mock_repo_class,
    mock_agent_class,
    company_id,
):
    mock_agent = AsyncMock()
    mock_agent.run.return_value = AgentResult(
        agent_name="content",
        success=False,
        output="Error occurred",
    )
    mock_agent_class.return_value = mock_agent

    response = client.post(
        "/api/chat/generate-content",
        json={"prompt": "test prompt"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Content generation failed: Error occurred" in response.text


def test_generate_content_validation_error(company_id):
    response = client.post(
        "/api/chat/generate-content",
        json={"prompt": "   "},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_chat_validation_error(company_id):
    response = client.post(
        "/api/chat/stream",
        json={"message": "   "},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
