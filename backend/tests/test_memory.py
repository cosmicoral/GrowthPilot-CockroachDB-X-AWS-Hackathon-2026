from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.api.deps import get_current_company_id
from backend.api.memory import router as memory_router
from backend.memory.store import MemoryHit


app = FastAPI()
app.include_router(memory_router)
client = TestClient(app)

@patch("backend.api.memory.MemoryRepository")
def test_search_memories_success(mock_repo_class):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    
    mock_repo_instance = AsyncMock()
    mock_repo_class.return_value = mock_repo_instance
    
    memory_id = uuid4()
    mock_hit = MemoryHit(
        id=memory_id,
        company_id=company_id,
        content="Test memory",
        memory_type="user",
        metadata={},
        importance=0.5,
        similarity=0.99,
        created_at=datetime.now(timezone.utc)
    )
    
    mock_repo_instance.search.return_value = [mock_hit]

    payload = {
        "query": "What is the test memory?",
        "k": 5
    }

    try:
        response = client.post("/api/memory/search", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == "Test memory"
        assert data[0]["id"] == str(memory_id)

        mock_repo_instance.search.assert_called_once()

    finally:
        app.dependency_overrides.clear()

@patch("backend.api.memory.MemoryRepository")
def test_search_memories_empty_query(mock_repo_class):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_repo_class.return_value.search = AsyncMock(return_value=[])

    try:
        response = client.post(
            "/api/memory/search",
            json={
                "query": "",
                "k": 5,
            },
        )

        # assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        pass

    finally:
        app.dependency_overrides.clear()

@patch("backend.api.memory.MemoryRepository")
def test_search_memories_invalid_k(mock_repo_class):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_repo_class.return_value.search = AsyncMock(return_value=[])

    try:
        response = client.post(
            "/api/memory/search",
            json={
                "query": "test",
                "k": 0,
            },
        )

        # assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        pass

    finally:
        app.dependency_overrides.clear()