from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import get_current_company_id
from backend.api.growthgraph import (
    GROWTHGRAPH_COHORT_SIZE,
    GROWTHGRAPH_COMPANY_IDS,
    aggregate_insights,
    router as growthgraph_router,
)
from backend.database.database import database
from backend.memory.repository import MemoryRepository
from backend.memory.store import MemoryHit

app = FastAPI()
app.include_router(growthgraph_router)
client = TestClient(app)


def make_hit(
    *,
    company_id,
    theme: str,
    similarity: float,
    content: str = "private founder memory",
) -> MemoryHit:
    return MemoryHit(
        id=uuid4(),
        company_id=company_id,
        content=content,
        memory_type="episodic",
        metadata={
            "theme": theme,
            "founder": "Private Founder",
        },
        importance=0.8,
        similarity=similarity,
        created_at=datetime.now(timezone.utc),
    )


def test_growthgraph_returns_only_thresholded_aggregates(monkeypatch):
    authenticated_company_id = uuid4()
    company_1, company_2, company_3, company_4 = (
        GROWTHGRAPH_COMPANY_IDS[:4]
    )

    app.dependency_overrides[get_current_company_id] = (
        lambda: authenticated_company_id
    )

    async def fake_search(
        self,
        *,
        company_ids,
        query,
        k,
        types,
        since=None,
    ):
        assert company_ids == GROWTHGRAPH_COMPANY_IDS
        assert query == "What campaign messaging worked?"
        assert k == 100
        assert types == ("episodic",)
        assert since is None
        return [
            make_hit(
                company_id=company_1,
                theme="product_education",
                similarity=0.9,
            ),
            # A second memory from one founder must not inflate prevalence.
            make_hit(
                company_id=company_1,
                theme="product_education",
                similarity=0.8,
            ),
            make_hit(
                company_id=company_2,
                theme="product_education",
                similarity=0.8,
            ),
            make_hit(
                company_id=company_3,
                theme="product_education",
                similarity=0.7,
            ),
            # Two founders are below the disclosure threshold.
            make_hit(
                company_id=company_3,
                theme="industry_trend",
                similarity=0.95,
            ),
            make_hit(
                company_id=company_4,
                theme="industry_trend",
                similarity=0.94,
            ),
        ]

    monkeypatch.setattr(
        MemoryRepository,
        "search_across_companies",
        fake_search,
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={"query": "  What campaign messaging worked?  "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What campaign messaging worked?"
    assert data["cohort_size"] == GROWTHGRAPH_COHORT_SIZE
    assert data["insight"] == (
        "Product education appears in relevant content from "
        "3 of 75 founders."
    )
    assert data["insights"] == [
        {
            "theme": "Product education",
            "summary": (
                "Product education appears in relevant content from "
                "3 of 75 founders."
            ),
            "matched_founders": 3,
            "cohort_size": 75,
            "prevalence": 0.04,
            "average_similarity": 0.8,
        }
    ]

    serialized = response.text
    assert "private founder memory" not in serialized
    assert "Private Founder" not in serialized
    assert "company_id" not in serialized
    assert "memory_id" not in serialized
    assert "metadata" not in serialized


def test_growthgraph_rejects_client_supplied_tenant_ids(monkeypatch):
    app.dependency_overrides[get_current_company_id] = lambda: uuid4()
    search = AsyncMock()
    monkeypatch.setattr(
        MemoryRepository,
        "search_across_companies",
        search,
    )

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={
                "query": "test",
                "company_ids": [str(uuid4())],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    search.assert_not_awaited()


def test_growthgraph_rejects_blank_query():
    app.dependency_overrides[get_current_company_id] = lambda: uuid4()

    try:
        response = client.post(
            "/api/growthgraph/insights",
            json={"query": "   "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_growthgraph_suppresses_small_groups():
    hits = [
        make_hit(
            company_id=GROWTHGRAPH_COMPANY_IDS[0],
            theme="founder_story",
            similarity=0.9,
        ),
        make_hit(
            company_id=GROWTHGRAPH_COMPANY_IDS[1],
            theme="founder_story",
            similarity=0.8,
        ),
    ]

    assert aggregate_insights(hits) == []


def test_growthgraph_route_is_mounted_in_main_app():
    from backend.main import app as main_app

    paths = {route.path for route in main_app.routes}
    assert "/api/growthgraph/insights" in paths


@pytest.mark.asyncio
async def test_repository_binds_explicit_company_allowlist(monkeypatch):
    company_ids = [uuid4(), uuid4()]
    embedding_service = AsyncMock()
    embedding_service.generate_embedding.return_value = [0.0] * 1024

    connection = AsyncMock()
    connection.fetch.return_value = []
    acquire = MagicMock()
    acquire.return_value.__aenter__ = AsyncMock(
        return_value=connection
    )
    acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    pool = MagicMock()
    pool.acquire = acquire
    monkeypatch.setattr(database, "pool", pool)

    repository = MemoryRepository(
        embedding_service=embedding_service,
    )
    result = await repository.search_across_companies(
        company_ids=company_ids,
        query="campaign performance",
        k=20,
        types=("episodic",),
    )

    assert result == []
    query_args = connection.fetch.await_args.args
    assert "company_id = ANY($1::UUID[])" in query_args[0]
    assert query_args[1] == company_ids
    assert query_args[3] == 200
    assert query_args[4] == ["episodic"]
    assert query_args[5] is None
    assert query_args[6] == 20
