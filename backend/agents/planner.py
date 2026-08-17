from __future__ import annotations

import asyncio
import json
import logging
import re
from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, Field, ValidationError, model_validator

from backend.agents.base import Agent, AgentResult

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    RESEARCH = "research"
    CONTENT = "content"
    ANALYTICS = "analytics"
    GENERAL = "general"


class ExecutionMode(str, Enum):
    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class IntentClassification(BaseModel):
    """Untrusted classifier output. Execution is deliberately not LLM-owned."""

    intents: list[Intent] = Field(min_length=1)
    reason: str = ""


class PlannerDecision(BaseModel):
    intents: list[Intent] = Field(min_length=1)
    execution: ExecutionMode
    reason: str = ""

    @model_validator(mode="after")
    def validate_decision(self):
        if len(set(self.intents)) != len(self.intents):
            raise ValueError("Planner intents must be unique")

        if Intent.GENERAL in self.intents and len(self.intents) != 1:
            raise ValueError("general intent cannot be combined with other intents")

        if len(self.intents) == 1 and self.execution != ExecutionMode.SINGLE:
            raise ValueError("A single intent must use single execution")

        if len(self.intents) > 1 and self.execution == ExecutionMode.SINGLE:
            raise ValueError("Multiple intents cannot use single execution")

        return self


class PlannerOutput(BaseModel):
    decision: PlannerDecision
    response: str
    sub_results: list[AgentResult]
    partial: bool = False
    failed_agents: list[str] = Field(default_factory=list)


ROUTING_TABLE = {
    Intent.RESEARCH: "market_research",
    Intent.CONTENT: "content",
    Intent.ANALYTICS: "analytics-reflection-agent",
}

INTENT_EXECUTION_ORDER = (
    Intent.RESEARCH,
    Intent.ANALYTICS,
    Intent.CONTENT,
    Intent.GENERAL,
)

FALLBACK_KEYWORDS = {
    Intent.RESEARCH: (
        "research",
        "competitor",
        "market",
        "industry",
        "customer",
        "trend",
    ),
    Intent.CONTENT: (
        "write",
        "create",
        "draft",
        "rewrite",
        "content",
        "post",
        "copy",
        "campaign",
        "email",
    ),
    Intent.ANALYTICS: (
        "analyze",
        "analyse",
        "analytics",
        "performance",
        "metric",
        "conversion",
        "reflection",
    ),
}


class PlannerAgent(Agent):
    def __init__(
        self,
        context,
        agents: Mapping[str, Agent] | None = None,
    ):
        super().__init__(context)
        self.agents = dict(agents or {})

    @property
    def name(self) -> str:
        return "planner"

    CLASSIFIER_SYSTEM_PROMPT = """
    You are the intent classifier for GrowthPilot.

    Classify the request into one or more intents:
    - research: market, competitor, customer, or industry research
    - content: generate or rewrite marketing content
    - analytics: analyze performance or produce a reflection
    - general: memory-grounded question answering

    Rules:
    - General must appear alone.
    - Return JSON only.
    - Do not choose execution order; application code owns orchestration.

    Schema:
    {
      "intents": ["research", "content"],
      "reason": "The user requested competitor research and a post"
    }
    """.strip()

    @classmethod
    def _decision_from_intents(
        cls,
        intents: list[Intent],
        *,
        reason: str,
    ) -> PlannerDecision:
        unique_intents = list(dict.fromkeys(intents))

        if len(unique_intents) > 1 and Intent.GENERAL in unique_intents:
            unique_intents.remove(Intent.GENERAL)

        if not unique_intents:
            unique_intents = [Intent.GENERAL]

        ordered_intents = [
            intent for intent in INTENT_EXECUTION_ORDER if intent in unique_intents
        ]

        if len(ordered_intents) == 1:
            execution = ExecutionMode.SINGLE
        elif Intent.CONTENT in ordered_intents:
            # Content consumes research/analytics output, so it is always the
            # final stage when combined with either upstream intent.
            execution = ExecutionMode.SEQUENTIAL
        else:
            execution = ExecutionMode.PARALLEL

        return PlannerDecision(
            intents=ordered_intents,
            execution=execution,
            reason=reason,
        )

    @staticmethod
    def _fallback_intents(message: str) -> list[Intent]:
        normalized = message.casefold()
        intents = [
            intent
            for intent, keywords in FALLBACK_KEYWORDS.items()
            if any(keyword in normalized for keyword in keywords)
        ]
        return intents or [Intent.GENERAL]

    @staticmethod
    def _parse_classification(raw: str) -> IntentClassification:
        cleaned = raw.strip()
        candidates = [cleaned]

        fenced = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            candidates.insert(0, fenced.group(1))

        embedded = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if embedded:
            candidates.append(embedded.group(0))

        last_error: ValidationError | None = None
        for candidate in dict.fromkeys(candidates):
            try:
                return IntentClassification.model_validate_json(candidate)
            except ValidationError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error
        raise ValueError("Classifier returned no JSON")

    async def _classify(self, message: str) -> PlannerDecision:
        try:
            raw = await self.context.bedrock_client.generate_text(
                prompt=message,
                system_prompt=self.CLASSIFIER_SYSTEM_PROMPT,
                max_tokens=200,
                temperature=0.0,
            )
            classification = self._parse_classification(str(raw or ""))
            return self._decision_from_intents(
                classification.intents,
                reason=classification.reason or "LLM intent classification",
            )
        except (ValidationError, ValueError, TypeError) as exc:
            logger.warning(
                "Planner classifier returned malformed output; using keyword fallback: %s",
                exc,
            )
        except Exception as exc:
            logger.warning(
                "Planner classifier call failed; using keyword fallback: %s",
                exc,
            )

        return self._decision_from_intents(
            self._fallback_intents(message),
            reason="Deterministic keyword fallback",
        )

    async def _run_one(
        self,
        intent: Intent,
        message: str,
        upstream_results: list[AgentResult] | None = None,
    ) -> AgentResult:
        agent_name = ROUTING_TABLE[intent]
        agent = self.agents.get(agent_name)

        if agent is None:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                output=f"Agent '{agent_name}' is not available",
            )

        prompt = message
        successful_upstream = [
            result for result in upstream_results or [] if result.success
        ]

        if successful_upstream:
            context = "\n\n".join(
                self._render_output(result.output) for result in successful_upstream
            )
            prompt = (
                f"{message}\n\n"
                "Use the following upstream agent results as context:\n"
                f"{context}"
            )

        try:
            return await agent.run(prompt=prompt)
        except Exception as exc:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                output=str(exc),
            )

    async def _run_parallel(
        self,
        intents: list[Intent],
        message: str,
    ) -> list[AgentResult]:
        outcomes = await asyncio.gather(
            *(self._run_one(intent, message) for intent in intents),
            return_exceptions=True,
        )

        results: list[AgentResult] = []
        for intent, outcome in zip(intents, outcomes):
            if isinstance(outcome, asyncio.CancelledError):
                raise outcome
            if isinstance(outcome, BaseException):
                results.append(
                    AgentResult(
                        agent_name=ROUTING_TABLE[intent],
                        success=False,
                        output=str(outcome),
                    )
                )
            else:
                results.append(outcome)
        return results

    async def _run_sequential(
        self,
        intents: list[Intent],
        message: str,
    ) -> list[AgentResult]:
        if Intent.CONTENT in intents:
            upstream_intents = [intent for intent in intents if intent != Intent.CONTENT]

            if len(upstream_intents) > 1:
                upstream_results = await self._run_parallel(upstream_intents, message)
            else:
                upstream_results = [
                    await self._run_one(upstream_intents[0], message)
                ]

            # Independent upstream work is preserved. Content runs when at
            # least one dependency succeeded and receives only successful data.
            if not any(result.success for result in upstream_results):
                return upstream_results

            content_result = await self._run_one(
                Intent.CONTENT,
                message,
                upstream_results=upstream_results,
            )
            return [*upstream_results, content_result]

        # Generic dependency-chain fallback for future sequential policies.
        results: list[AgentResult] = []
        for intent in intents:
            result = await self._run_one(intent, message, upstream_results=results)
            results.append(result)
            if not result.success:
                break
        return results

    async def _run_general(self, message: str) -> AgentResult:
        try:
            memories = await self.context.memory_repository.search(
                company_id=self.context.company_id,
                query=message,
                k=5,
                types=[
                    "episodic",
                    "semantic",
                    "user",
                    "task",
                    "reflection",
                ],
            )
        except Exception:
            memories = []

        context_text = "\n".join(f"- {memory.content}" for memory in memories)
        answer = await self.context.bedrock_client.generate_text(
            prompt=message,
            system_prompt=(
                "Answer using the supplied company memories. "
                "If the memories do not contain the answer, say so.\n\n"
                f"Company memories:\n{context_text or 'No memories found.'}"
            ),
            max_tokens=1000,
            temperature=0.2,
        )

        return AgentResult(
            agent_name="memory-qa",
            success=True,
            output=answer,
            metadata={"memory_ids": [str(memory.id) for memory in memories]},
        )

    @staticmethod
    def _render_output(output: Any) -> str:
        if isinstance(output, BaseModel):
            return output.model_dump_json(indent=2)
        if isinstance(output, str):
            return output
        return json.dumps(output, default=str, ensure_ascii=False, indent=2)

    def _merge_results(self, results: list[AgentResult]) -> str:
        successful = [result for result in results if result.success]

        if len(successful) == 1:
            return self._render_output(successful[0].output)

        return "\n\n".join(
            f"## {result.agent_name}\n{self._render_output(result.output)}"
            for result in successful
        )

    async def process(
        self,
        retrieved_memories,
        message: str,
        **kwargs,
    ) -> PlannerOutput:
        decision = await self._classify(message)

        if decision.intents == [Intent.GENERAL]:
            results = [await self._run_general(message)]
        elif decision.execution == ExecutionMode.SEQUENTIAL:
            results = await self._run_sequential(decision.intents, message)
        elif decision.execution == ExecutionMode.PARALLEL:
            results = await self._run_parallel(decision.intents, message)
        else:
            results = [await self._run_one(decision.intents[0], message)]

        successful = [result for result in results if result.success]
        failed = [result.agent_name for result in results if not result.success]

        if not successful:
            details = "; ".join(
                f"{result.agent_name}: {result.output}" for result in results
            )
            raise RuntimeError(f"All planned agents failed: {details}")

        return PlannerOutput(
            decision=decision,
            response=self._merge_results(results),
            sub_results=results,
            partial=bool(failed),
            failed_agents=failed,
        )
