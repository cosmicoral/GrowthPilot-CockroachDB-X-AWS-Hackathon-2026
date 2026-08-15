import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from backend.agents.analytics_reflection import (
    AnalyticsReflectionAgent,
)
from backend.agents.content import ContentAgent
from backend.agents.context import AgentContext
from backend.agents.market_research import MarketResearchAgent
from backend.agents.planner import PlannerAgent, PlannerOutput
from backend.api.deps import get_current_company_id
from backend.llm.client import BedrockClient
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.repository import MemoryRepository

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be empty or whitespace")

        return value.strip()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Route a chat request through the Planner Agent and return the result
    using Server-Sent Events.
    """

    bedrock = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock)
    repo = MemoryRepository(
        embedding_service=embedding_service,
    )

    context = AgentContext(
        company_id=company_id,
        bedrock_client=bedrock,
        memory_repository=repo,
    )

    agents = {
        "market_research": MarketResearchAgent(context=context),
        "content": ContentAgent(context=context),
        "analytics-reflection-agent": AnalyticsReflectionAgent(
            context=context,
        ),
    }

    planner = PlannerAgent(
        context=context,
        agents=agents,
    )

    try:
        memories = await repo.search(
            company_id=company_id,
            query=request.message,
            k=3,
        )
    except Exception as exc:
        logger.warning(
            "Memory retrieval failed for company %s, "
            "continuing without memory preview: %s",
            company_id,
            exc,
        )
        memories = []

    async def sse_generator():
        try:
            memories_data = [
                memory.model_dump(mode="json")
                for memory in memories
            ]

            memories_event = {
                "type": "memories",
                "memories": memories_data,
            }

            yield (
                "data: "
                f"{json.dumps(memories_event, ensure_ascii=False)}"
                "\n\n"
            )

            # intent classification
            # routing
            # sequential/parallel orchestration
            # result merging
            result = await planner.run(
                message=request.message,
            )

            if not result.success:
                error_event = {
                    "type": "error",
                    "detail": str(result.output),
                }

                yield (
                    "data: "
                    f"{json.dumps(error_event, ensure_ascii=False)}"
                    "\n\n"
                )
                return

            if not isinstance(result.output, PlannerOutput):
                error_event = {
                    "type": "error",
                    "detail": (
                        "Planner returned an unexpected output type"
                    ),
                }

                yield (
                    "data: "
                    f"{json.dumps(error_event, ensure_ascii=False)}"
                    "\n\n"
                )
                return

            planner_output = result.output


            token_event = {
                "type": "token",
                "text": planner_output.response,
            }

            yield (
                "data: "
                f"{json.dumps(token_event, ensure_ascii=False)}"
                "\n\n"
            )

            done_event = {
                "type": "done",
                "metadata": {
                    "decision": (
                        planner_output.decision.model_dump(
                            mode="json",
                        )
                    ),
                    "partial": planner_output.partial,
                    "failed_agents": (
                        planner_output.failed_agents
                    ),
                },
            }

            yield (
                "data: "
                f"{json.dumps(done_event, ensure_ascii=False)}"
                "\n\n"
            )

        except Exception as exc:
            logger.exception(
                "Planner chat request failed for company %s",
                company_id,
            )

            error_event = {
                "type": "error",
                "detail": str(exc),
            }

            yield (
                "data: "
                f"{json.dumps(error_event, ensure_ascii=False)}"
                "\n\n"
            )

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )


class GenerateContentRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "prompt must not be empty or whitespace"
            )

        return value.strip()


@router.post("/generate-content")
async def generate_content(
    request: GenerateContentRequest,
    company_id: UUID = Depends(get_current_company_id),
):
    """
    Generate tailored GTM content directly through ContentAgent.

    This endpoint is retained for backwards compatibility.
    """

    bedrock = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock)
    repo = MemoryRepository(
        embedding_service=embedding_service,
    )

    context = AgentContext(
        company_id=company_id,
        bedrock_client=bedrock,
        memory_repository=repo,
    )

    agent = ContentAgent(context=context)

    result = await agent.run(
        prompt=request.prompt,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Content generation failed: {result.output}"
            ),
        )

    return {
        "content": result.output,
    }
