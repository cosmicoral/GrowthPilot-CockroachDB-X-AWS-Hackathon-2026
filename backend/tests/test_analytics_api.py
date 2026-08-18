from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agents.analytics_reflection import AnalyticsReflectionOutput
from backend.agents.base import AgentResult
from backend.api.analytics import router
from backend.api.deps import get_current_company_id
from backend.memory.store import MemoryHit


def _app(company_id):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    return app


@patch("backend.api.analytics.MemoryRepository")
def test_latest_reflection_returns_analytics_memory(repository_class):
    company_id = uuid4()
    reflection = MemoryHit(
        id=uuid4(),
        company_id=company_id,
        content="Workflow content performed best.",
        memory_type="reflection",
        metadata={"source": "analytics-reflection-agent"},
        importance=0.9,
        created_at=datetime.now(timezone.utc),
    )
    repository_class.return_value.recent = AsyncMock(
        return_value=[reflection],
    )

    with TestClient(_app(company_id)) as client:
        response = client.get("/api/analytics/latest")

    assert response.status_code == 200
    assert response.json()["id"] == str(reflection.id)


@patch("backend.api.analytics.AnalyticsReflectionAgent")
@patch("backend.api.analytics.MemoryRepository")
@patch("backend.api.analytics.BedrockClient")
def test_run_reflection_returns_structured_output(
    bedrock_class,
    repository_class,
    agent_class,
):
    company_id = uuid4()
    output = AnalyticsReflectionOutput(
        group_by="theme",
        post_count=2,
        groups=[
            {
                "group_name": "workflow",
                "post_count": 1,
                "total_likes": 10,
                "total_comments": 2,
                "total_clicks": 3,
                "total_engagement": 15,
                "average_engagement_per_post": 15,
            },
            {
                "group_name": "automation",
                "post_count": 1,
                "total_likes": 4,
                "total_comments": 1,
                "total_clicks": 1,
                "total_engagement": 6,
                "average_engagement_per_post": 6,
            },
        ],
        best_group="workflow",
        analyzed_memory_ids=[uuid4(), uuid4()],
        reflection="Workflow performed best; test another workflow hook.",
        reflection_memory_id=uuid4(),
    )
    agent = MagicMock()
    agent.run = AsyncMock(
        return_value=AgentResult(
            agent_name="analytics-reflection-agent",
            success=True,
            output=output,
        )
    )
    agent_class.return_value = agent

    with TestClient(_app(company_id)) as client:
        response = client.post(
            "/api/analytics/reflection",
            json={"group_by": "theme"},
        )

    assert response.status_code == 200
    assert response.json()["best_group"] == "workflow"
    agent.run.assert_awaited_once_with(group_by="theme")
