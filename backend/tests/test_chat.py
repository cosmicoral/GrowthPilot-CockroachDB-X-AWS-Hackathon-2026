from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from backend.api.chat import router as chat_router
from backend.api.deps import get_current_company_id

app = FastAPI()
app.include_router(chat_router)
client = TestClient(app)


@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_chat_stream_success(mock_bedrock_class, mock_repo_class):
    """Stream should yield text chunks followed by a done terminal event."""
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_repo_instance = AsyncMock()
    mock_repo_class.return_value = mock_repo_instance
    mock_repo_instance.search.return_value = []

    mock_bedrock_instance = AsyncMock()
    mock_bedrock_class.return_value = mock_bedrock_instance

    async def fake_stream(*args, **kwargs):
        yield "Hello"
        yield " World"

    mock_bedrock_instance.generate_text_stream = fake_stream

    payload = {"message": "Hi"}

    response = client.post("/api/chat/stream", json=payload)

    assert response.status_code == status.HTTP_200_OK
    content = response.text

    assert 'data: {"type": "memories", "memories": []}\n\n' in content
    assert 'data: {"type": "token", "text": "Hello"}\n\n' in content
    assert 'data: {"type": "token", "text": " World"}\n\n' in content
    # A clean finish must emit a done terminal event
    assert 'data: {"type": "done"}\n\n' in content

    app.dependency_overrides.clear()


@patch("backend.api.chat.MemoryRepository")
@patch("backend.api.chat.BedrockClient")
def test_chat_stream_error_event(mock_bedrock_class, mock_repo_class):
    """A mid-stream crash should emit an error terminal event instead of silently stopping."""
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_repo_instance = AsyncMock()
    mock_repo_class.return_value = mock_repo_instance
    mock_repo_instance.search.return_value = []

    mock_bedrock_instance = AsyncMock()
    mock_bedrock_class.return_value = mock_bedrock_instance

    async def failing_stream(*args, **kwargs):
        yield "Starting..."
        raise RuntimeError("Bedrock connection lost")

    mock_bedrock_instance.generate_text_stream = failing_stream

    payload = {"message": "Hi"}

    response = client.post("/api/chat/stream", json=payload)

    assert response.status_code == status.HTTP_200_OK
    content = response.text

    assert 'data: {"type": "memories", "memories": []}\n\n' in content
    # The partial chunk should still have been sent
    assert 'data: {"type": "token", "text": "Starting..."}\n\n' in content
    # An error terminal event should be emitted with the error detail
    assert '"type": "error"' in content
    assert "Bedrock connection lost" in content

    app.dependency_overrides.clear()


@patch("backend.agents.content.ContentAgent")
def test_generate_content_success(mock_agent_class):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_agent_instance = AsyncMock()
    mock_agent_class.return_value = mock_agent_instance
    
    # Create a mock result
    from backend.agents.base import AgentResult
    mock_agent_instance.run.return_value = AgentResult(
        agent_name="content",
        success=True,
        output="Generated post",
    )

    response = client.post("/api/chat/generate-content", json={"prompt": "test prompt"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"content": "Generated post"}

    app.dependency_overrides.clear()


@patch("backend.agents.content.ContentAgent")
def test_generate_content_failure(mock_agent_class):
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    mock_agent_instance = AsyncMock()
    mock_agent_class.return_value = mock_agent_instance
    
    from backend.agents.base import AgentResult
    mock_agent_instance.run.return_value = AgentResult(
        agent_name="content",
        success=False,
        output="Error occurred",
    )

    response = client.post("/api/chat/generate-content", json={"prompt": "test prompt"})

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Content generation failed: Error occurred" in response.text

    app.dependency_overrides.clear()


def test_generate_content_validation_error():
    company_id = uuid4()
    app.dependency_overrides[get_current_company_id] = lambda: company_id

    # Empty prompt should fail validation (HTTP 422) before hitting the agent
    response = client.post("/api/chat/generate-content", json={"prompt": "   "})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    app.dependency_overrides.clear()
