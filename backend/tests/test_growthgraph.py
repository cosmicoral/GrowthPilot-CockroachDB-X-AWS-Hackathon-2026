from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import get_current_company_id
from backend.api.growthgraph import router as growthgraph_router
from backend.memory.store import MemoryHit


app = FastAPI()
app.include_router(growthgraph_router)
client = TestClient(app)


def test_growthgraph_insights_success(monkeypatch):
    company_id = uuid4()
    selected_company_1 = uuid4()
    selected_company_2 = uuid4()

    app.dependency_overrides[get_current_company_id] = (
        lambda: company_id
    )

    async def fake_search_across_companies(
        self,
        *,
        company_ids,
        query,
        k,
        types,
        since=None,
    ):
        assert company_ids == [
            selected_company_1,
            selected_company_2,
        ]
        assert query == "What campaign messaging worked?"
        assert k == 20
        assert types is None
        assert since is None

        return [
            MemoryHit(
                id=uuid4(),
                company_id=selected_company_1,
                content="Engineering workflow messaging performed well.",
                memory_type="reflection",
                metadata={"source": "synthetic"},
                importance=0.9,
                similarity=0.95,
                created_at=datetime.now(timezone.utc),
            ),
            MemoryHit(
                id=uuid4(),
                company_id=selected_company_2,
                content="Technical content generated strong engagement.",
                memory_type="reflection",
                metadata={"source": "synthetic"},
                importance=0.8,
                similarity=0.91,
                created_at=datetime.now(timezone.utc),
            ),
        ]

    monkeypatch.setattr(
        "backend.api.growthgraph.MemoryRepository.search_across_companies",
        fake_search_across_companies,
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={
                "query": "What campaign messaging worked?",
                "company_ids": [
                    str(selected_company_1),
                    str(selected_company_2),
                ],
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["company_count"] == 2
        assert len(data["results"]) == 2

        assert (
            data["results"][0]["content"]
            == "Engineering workflow messaging performed well."
        )

        assert (
            data["results"][1]["content"]
            == "Technical content generated strong engagement."
        )

        # Cross-tenant identity should not be exposed by the API response.
        assert "company_id" not in data["results"][0]
        assert "company_id" not in data["results"][1]

    finally:
        app.dependency_overrides.clear()


def test_growthgraph_insights_requires_company_ids():
    company_id = uuid4()

    app.dependency_overrides[get_current_company_id] = (
        lambda: company_id
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={
                "query": "test",
                "company_ids": [],
            },
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()


def test_growthgraph_insights_requires_query():
    company_id = uuid4()

    app.dependency_overrides[get_current_company_id] = (
        lambda: company_id
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={
                "query": "",
                "company_ids": [str(uuid4())],
            },
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()


def test_growthgraph_insights_rejects_invalid_k():
    company_id = uuid4()

    app.dependency_overrides[get_current_company_id] = (
        lambda: company_id
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={
                "query": "test",
                "company_ids": [str(uuid4())],
                "k": 0,
            },
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()