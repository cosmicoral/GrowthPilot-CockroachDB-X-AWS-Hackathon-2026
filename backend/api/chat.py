import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


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
    embedding_service = BedrockEmbeddingService(bedrock)
    repo = MemoryRepository(embedding_service=embedding_service)

    # 1. Search for relevant memories based on the user's message
    try:
        memories = await repo.search(
            company_id=company_id,
            query=request.message,
            k=3,
        )
    except Exception as exc:
        logger.warning(
            "Memory retrieval failed for company %s, continuing without context: %s",
            company_id,
            exc,
        )
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
        try:
            memories_data = [m.model_dump(mode="json") for m in memories]
            yield f"data: {json.dumps({'type': 'memories', 'memories': memories_data})}\n\n"

            async for chunk in bedrock.generate_text_stream(
                prompt=request.message,
                system_prompt=system_prompt,
            ):
                data = json.dumps({"type": "token", "text": chunk})
                yield f"data: {data}\n\n"

            # Signal a clean finish so the frontend knows the stream ended normally
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            # Signal an error so the frontend can show a proper message
            # instead of silently stopping
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )


from pydantic import BaseModel, field_validator

class GenerateContentRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("prompt must not be empty or whitespace")
        return v


@router.post("/generate-content")
async def generate_content(
    request: GenerateContentRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Generate tailored GTM content (e.g. social posts) using the ContentAgent.
    """
    from backend.agents.content import ContentAgent
    from backend.agents.context import AgentContext

    bedrock = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock)
    repo = MemoryRepository(embedding_service=embedding_service)

    context = AgentContext(
        company_id=company_id,
        bedrock_client=bedrock,
        memory_repository=repo
    )

    agent = ContentAgent(context=context)
    result = await agent.run(prompt=request.prompt)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {result.output}"
        )

    return {"content": result.output}
