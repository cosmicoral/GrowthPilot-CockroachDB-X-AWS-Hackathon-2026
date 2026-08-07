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
    
    # Use client.post to test a StreamingResponse directly
    response = client.post("/api/chat/stream", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    content = response.text
    
    assert 'data: {"text": "Hello"}\n\n' in content
    assert 'data: {"text": " World"}\n\n' in content
        
    app.dependency_overrides.clear()
