from __future__ import annotations

import asyncio
import json
import re
from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel, Field, model_validator

from backend.agents.base import Agent, AgentResult


class Intent(str, Enum):
    RESEARCH = "research"
    CONTENT = "content"
    ANALYTICS = "analytics"
    GENERAL = "general"


class ExecutionMode(str, Enum):
    SINGLE = "single"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class PlannerDecision(BaseModel):
    intents: list[Intent] = Field(min_length=1)
    execution: ExecutionMode
    reason: str =""

    @model_validator(mode="after")
    def validate_decision(self):
        if len(set(self.intents)) != len(self.intents):
            raise ValueError("Planner intents must be unique")

        if Intent.GENERAL in self.intents and len(self.intents) !=1:
            raise ValueError("general intent cannot be combined with other intents")

        if len(self.intents) == 1 and self.execution != ExecutionMode.SINGLE:
            raise ValueError("A single intent must use single execution")

        if len(self.intents) > 1 and self.execution ==ExecutionMode.SINGLE:
            raise ValueError("Multiple intents cannot use single execution")

        return self

class PlannerOutput(BaseModel):
    decision: PlannerDecision
    response: str
    sub_results: list[AgentResult]
    partial: bool = False
    failed_agents: list[str] = Field(default_factory= list)

ROUTING_TABLE = {
    Intent.RESEARCH: "market_research",
    Intent.CONTENT: "content",
    Intent.ANALYTICS: "analytics-reflection-agent",
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
    You are the routing planner for GrowthPilot.

    Classify the request into one or more intents:
    - research: market, competitor, customer, or industry research
    - content: generate or rewrite marketing content
    - analytics: analyze performance or produce a reflection
    - general: memory-grounded question answering

    Choose execution:
    - single: exactly one intent
    - sequential: a later task depends on an earlier result
    - parallel: multiple tasks are independent

    Rules:
    - Research followed by content generation is sequential.
    - Analytics followed by content generation is sequential.
    - Independent research and analytics requests may run in parallel.
    - General must appear alone.
    - Return JSON only.

    Schema:
    {
    "intents": ["research", "content"],
    "execution": "sequential",
    "reason": "Content depends on research"
    }
    """.strip()

    async def _classify(self, message: str) -> PlannerDecision:
        raw = await self.context.bedrock_client.generate_text(
            prompt=message,
            system_prompt=self.CLASSIFIER_SYSTEM_PROMPT,
            max_tokens=250,
            temperature=0.0,
        )

        raw = raw.strip()

        fenced = re.fullmatch(
            r"```(?:json)?\s*(.*?)\s*```",
            raw,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if fenced:
            raw = fenced.group(1)

        return PlannerDecision.model_validate_json(raw)

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
            result
            for result in upstream_results or []
            if result.success
        ]

        if successful_upstream:
            context = "\n\n".join(
                self._render_output(result.output)
                for result in successful_upstream
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

    async def _run_sequential(
        self,
        intents: list[Intent],
        message: str,
    ) -> list[AgentResult]:
        results: list[AgentResult] = []

        for intent in intents:
            result = await self._run_one(
                intent,
                message,
                upstream_results=results,
            )
            results.append(result)

            if not result.success:
                break

        return results

    async def _run_parallel(
        self,
        intents: list[Intent],
        message: str,
    ) -> list[AgentResult]:
        return list(
            await asyncio.gather(
                *[
                    self._run_one(intent, message)
                    for intent in intents
                ]
            )
        )

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

        context_text = "\n".join(
            f"- {memory.content}"
            for memory in memories
        )

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
            metadata={
                "memory_ids": [
                    str(memory.id)
                    for memory in memories
                ],
            },
        )

    @staticmethod
    def _render_output(output: Any) -> str:
        if isinstance(output, BaseModel):
            return output.model_dump_json(indent=2)

        if isinstance(output, str):
            return output

        return json.dumps(
            output,
            default=str,
            ensure_ascii=False,
            indent=2,
        )

    def _merge_results(self, results: list[AgentResult]) -> str:
        successful = [result for result in results if result.success]

        if len(successful) == 1:
            return self._render_output(successful[0].output)

        return "\n\n".join(
            f"## {result.agent_name}\n"
            f"{self._render_output(result.output)}"
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
            results = await self._run_sequential(
                decision.intents,
                message,
            )

        elif decision.execution == ExecutionMode.PARALLEL:
            results = await self._run_parallel(
                decision.intents,
                message,
            )

        else:
            results = [
                await self._run_one(
                    decision.intents[0],
                    message,
                )
            ]

        successful = [result for result in results if result.success]
        failed = [result.agent_name for result in results if not result.success]

        if not successful:
            details = "; ".join(
                f"{result.agent_name}: {result.output}"
                for result in results
            )
            raise RuntimeError(f"All planned agents failed: {details}")

        return PlannerOutput(
            decision=decision,
            response=self._merge_results(results),
            sub_results=results,
            partial=bool(failed),
            failed_agents=failed,
        )