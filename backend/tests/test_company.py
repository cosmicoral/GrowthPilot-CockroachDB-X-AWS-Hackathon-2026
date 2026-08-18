from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.api.company import router as company_router
from backend.api.deps import get_current_company_id

app = FastAPI()
app.include_router(company_router)
client = TestClient(app)

def test_get_my_company_success():
    company_id = uuid4()
    
    # Mock the authentication dependency to avoid setting up valid tokens
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    
    with patch("backend.api.company.database") as mock_db:
        mock_conn = AsyncMock()
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchrow.return_value = {
            "id": company_id,
            "name": "Test Co",
            "email": "test@co.com",
            "website": "test.com",
            "industry": "Tech",
            "description": "A tech co"
        }

        response = client.get("/api/company/me")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Test Co"
        assert response.json()["id"] == str(company_id)
    
    app.dependency_overrides.clear()

def test_get_my_company_not_found():
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    
    with patch("backend.api.company.database") as mock_db:
        mock_conn = AsyncMock()
        mock_db.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchrow.return_value = None

        response = client.get("/api/company/me")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    app.dependency_overrides.clear()


@patch("backend.api.company.BedrockClient")
@patch("backend.api.company.MemoryRepository")
@patch("backend.api.company.database")
def test_onboarding_updates_profile_and_writes_typed_memories(
    mock_db,
    mock_repository_class,
    _mock_bedrock_class,
):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    mock_conn = AsyncMock()
    mock_db.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {
        "id": company_id,
        "name": "Test Co",
        "email": "test@co.com",
        "website": "https://test.co",
        "industry": "SaaS",
        "description": "Testing GTM",
    }
    repository = AsyncMock()
    mock_repository_class.return_value = repository

    response = client.post(
        "/api/company/onboarding",
        json={
            "website": "https://test.co",
            "industry": "SaaS",
            "description": "Testing GTM",
            "ideal_customer": "Seed-stage SaaS founders",
            "three_month_goal": "Reach 100 users",
            "previous_attempts": "LinkedIn worked",
            "current_channels": "LinkedIn and Reddit",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["website"] == "https://test.co"
    assert repository.write.await_count == 4
    written_types = [call.kwargs["memory_type"] for call in repository.write.await_args_list]
    assert written_types == ["user", "user", "episodic", "user"]
    app.dependency_overrides.clear()


@patch("backend.api.company.BedrockClient")
@patch("backend.api.company.MemoryRepository")
@patch("backend.api.company.database")
def test_onboarding_reports_embedding_failure(
    mock_db,
    mock_repository_class,
    _mock_bedrock_class,
):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id
    mock_conn = AsyncMock()
    mock_db.acquire.return_value.__aenter__.return_value = mock_conn
    mock_conn.fetchrow.return_value = {
        "id": company_id,
        "name": "Test Co",
        "email": "test@co.com",
        "website": None,
        "industry": None,
        "description": None,
    }
    mock_repository_class.return_value.write = AsyncMock(
        side_effect=RuntimeError("Bedrock unavailable"),
    )

    response = client.post(
        "/api/company/onboarding",
        json={"ideal_customer": "Founders"},
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "embedding" in response.json()["detail"].lower()
    app.dependency_overrides.clear()
