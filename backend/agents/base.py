import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field

from backend.agents.context import AgentContext

logger = logging.getLogger(__name__)


class AgentResult(BaseModel):
    """
    Standard schema for agent execution results.
    """
    agent_name: str
    success: bool
    output: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Agent(ABC):
    """
    Abstract base class for all GrowthPilot GTM agents.

    All custom agents inherit from this class and utilize the provided
    AgentContext to access shared resources (LLM client, DB repository, Trace repository).
    """

    def __init__(self, context: AgentContext):
        self.context = context

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique name identifier of the agent.
        """
        pass

    async def run(self, *args, **kwargs) -> AgentResult:
        """
        Orchestrate the standard agent lifecycle with automatic trace recording:
        1. Retrieve memories/context
        2. Execute reasoning/actions (process)
        3. Persist new memories or reflections
        4. Record execution trace (duration, memories retrieved, input, output, success/error)
        """
        start_perf = time.perf_counter()
        start_time = datetime.now(timezone.utc)
        memories = None
        memories_summary: List[Dict[str, Any]] = []
        output_data: Any = None
        success = False
        error_msg: Optional[str] = None

        try:
            memories = await self.retrieve_memories(*args, **kwargs)
            memories_summary = self._summarize_memories_for_trace(memories)

            output_data = await self.process(memories, *args, **kwargs)
            await self.persist_memories(output_data)

            success = True
            result = AgentResult(
                agent_name=self.name,
                success=True,
                output=output_data,
            )
        except Exception as e:
            success = False
            error_msg = str(e)
            output_data = {"error": error_msg}
            result = AgentResult(
                agent_name=self.name,
                success=False,
                output=error_msg,
            )
        finally:
            duration_ms = (time.perf_counter() - start_perf) * 1000.0
            await self._record_trace_safe(
                start_time=start_time,
                duration_ms=duration_ms,
                args=args,
                kwargs=kwargs,
                memories_retrieved=memories_summary,
                output_data=output_data,
                success=success,
                error_msg=error_msg,
            )

        return result

    def _summarize_memories_for_trace(self, memories: Any) -> List[Dict[str, Any]]:
        """
        Extract structured summary of retrieved memories for trace recording.
        """
        if not memories:
            return []

        items = memories if isinstance(memories, (list, tuple)) else [memories]
        summary = []

        for m in items:
            if hasattr(m, "id"):
                summary.append({
                    "id": str(getattr(m, "id", "")),
                    "similarity": getattr(m, "similarity", None),
                    "memory_type": getattr(m, "memory_type", None),
                    "importance": getattr(m, "importance", None),
                    "content_preview": str(getattr(m, "content", ""))[:100],
                })
            elif isinstance(m, dict):
                summary.append({
                    "id": str(m.get("id")) if m.get("id") else None,
                    "similarity": m.get("similarity"),
                    "memory_type": m.get("memory_type"),
                    "importance": m.get("importance"),
                    "content_preview": str(m.get("content", ""))[:100],
                })
            else:
                summary.append({"summary": str(m)[:100]})

        return summary

    async def _record_trace_safe(
        self,
        start_time: datetime,
        duration_ms: float,
        args: tuple,
        kwargs: dict,
        memories_retrieved: List[Dict[str, Any]],
        output_data: Any,
        success: bool,
        error_msg: Optional[str],
    ) -> None:
        """
        Record trace safely without interrupting primary execution flow if DB fails.
        """
        try:
            if (
                not hasattr(self.context, "trace_repository")
                or self.context.trace_repository is None
            ):
                return

            company_id = getattr(self.context, "company_id", None)
            if not company_id:
                return

            # Traces are persisted as JSONB. Encode recursively so UUIDs,
            # datetimes, Pydantic models, and values nested inside containers
            # cannot make an otherwise successful agent run lose its trace.
            input_summary = jsonable_encoder(
                {
                    "args": list(args),
                    "kwargs": kwargs,
                }
            )
            output_summary = jsonable_encoder(output_data)
            memories_summary = jsonable_encoder(memories_retrieved)

            await self.context.trace_repository.save_trace(
                company_id=company_id,
                agent_name=self.name,
                start_time=start_time,
                duration_ms=duration_ms,
                input=input_summary,
                output=output_summary,
                memories_retrieved=memories_summary,
                success=success,
                error=error_msg,
            )
        except Exception as exc:
            logger.warning("Non-blocking trace recording failed for agent %s: %s", self.name, exc)

    async def retrieve_memories(self, *args, **kwargs) -> Any:
        """
        Hook to retrieve relevant memories/context prior to execution.
        """
        return None

    @abstractmethod
    async def process(self, retrieved_memories: Any, *args, **kwargs) -> Any:
        """
        Execute core reasoning and actions. Must be implemented by sub-classes.
        """
        pass

    async def persist_memories(self, result_data: Any) -> None:
        """
        Hook to persist new memories or reflections back to storage.
        """
        pass
