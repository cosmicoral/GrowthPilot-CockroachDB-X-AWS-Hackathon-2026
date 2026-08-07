import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.repository import MemoryRepository

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Stream a chat response from the AI, augmented with relevant memories.
    """
    bedrock = BedrockClient()
    repo = MemoryRepository(embedding_service=bedrock)

    # 1. Search for relevant memories based on the user's message
    try:
        memories = await repo.search(
            company_id=company_id,
            query=request.message,
            k=3,
        )
    except Exception:
        memories = []

    # 2. Build the system prompt with retrieved context
    context_text = "\n".join(m.content for m in memories)
    system_prompt = (
        "You are GrowthPilot, an AI assistant for this company.\n"
        "Here is some relevant context from your memory:\n"
        f"{context_text}\n\n"
        "Answer the user's question concisely."
    )

    # 3. Stream the response using Server-Sent Events (SSE)
    async def sse_generator():
        async for chunk in bedrock.generate_text_stream(
            prompt=request.message,
            system_prompt=system_prompt,
        ):
            data = json.dumps({"text": chunk})
            yield f"data: {data}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )
