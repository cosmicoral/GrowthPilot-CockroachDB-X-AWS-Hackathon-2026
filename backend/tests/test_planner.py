from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.agents.base import AgentResult
from backend.agents.context import AgentContext
from backend.agents.planner import (
    ExecutionMode,
    Intent,
    PlannerAgent,
    PlannerOutput,
)


@pytest.fixture
def dependencies():
    bedrock = AsyncMock()
    repository = AsyncMock()
    context = AgentContext(
        company_id=uuid4(),
        bedrock_client=bedrock,
        memory_repository=repository,
    )
    return context, bedrock, repository


def mock_agent(name: str, output, *, success: bool = True):
    agent = MagicMock()
    agent.name = name
    agent.run = AsyncMock(
        return_value=AgentResult(
            agent_name=name,
            success=success,
            output=output,
        )
    )
    return agent


@pytest.mark.asyncio
async def test_routes_content_request(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["content"],'
        '"execution":"single",'
        '"reason":"User requested a post"}'
    )
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(context, agents={"content": content})

    result = await planner.run(message="Write a LinkedIn post")

    assert result.success is True
    assert isinstance(result.output, PlannerOutput)
    assert result.output.decision.intents == [Intent.CONTENT]
    assert result.output.decision.execution == ExecutionMode.SINGLE
    assert result.output.response == "Generated post"
    assert result.output.partial is False
    content.run.assert_awaited_once_with(prompt="Write a LinkedIn post")


@pytest.mark.asyncio
async def test_execution_mode_is_derived_in_code_not_trusted_from_llm(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["content","research"],'
        '"execution":"parallel",'
        '"reason":"Model chose an unsafe mode"}'
    )
    research = mock_agent("market_research", "Research result")
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(
        context,
        agents={"market_research": research, "content": content},
    )

    result = await planner.run(message="Research competitors and write a post")

    assert result.success is True
    assert result.output.decision.intents == [Intent.RESEARCH, Intent.CONTENT]
    assert result.output.decision.execution == ExecutionMode.SEQUENTIAL
    assert "Research result" in content.run.await_args.kwargs["prompt"]


@pytest.mark.asyncio
async def test_runs_dependent_agents_sequentially(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research","content"],'
        '"execution":"sequential",'
        '"reason":"Content depends on research"}'
    )
    research = mock_agent("market_research", "Research result")
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(
        context,
        agents={
            "market_research": research,
            "content": content,
        },
    )

    result = await planner.run(
        message="Research competitors and write a post",
    )

    assert result.success is True
    assert result.output.decision.execution == ExecutionMode.SEQUENTIAL
    research.run.assert_awaited_once_with(
        prompt="Research competitors and write a post",
    )
    content.run.assert_awaited_once()
    content_prompt = content.run.await_args.kwargs["prompt"]
    assert "Research result" in content_prompt
    assert "upstream agent results" in content_prompt


@pytest.mark.asyncio
async def test_runs_independent_agents_in_parallel(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research","analytics"],'
        '"execution":"parallel",'
        '"reason":"The tasks are independent"}'
    )
    research = mock_agent("market_research", "Research result")
    analytics = mock_agent(
        "analytics-reflection-agent",
        "Analytics result",
    )
    planner = PlannerAgent(
        context,
        agents={
            "market_research": research,
            "analytics-reflection-agent": analytics,
        },
    )

    result = await planner.run(
        message="Research competitors and analyze performance",
    )

    assert result.success is True
    assert result.output.decision.execution == ExecutionMode.PARALLEL
    assert len(result.output.sub_results) == 2
    assert "Research result" in result.output.response
    assert "Analytics result" in result.output.response
    research.run.assert_awaited_once()
    analytics.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_partial_output_when_later_agent_fails(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research","content"],'
        '"execution":"sequential",'
        '"reason":"Content depends on research"}'
    )
    research = mock_agent("market_research", "Research result")
    content = mock_agent(
        "content",
        "Bedrock unavailable",
        success=False,
    )
    planner = PlannerAgent(
        context,
        agents={
            "market_research": research,
            "content": content,
        },
    )

    result = await planner.run(
        message="Research competitors and write a post",
    )

    assert result.success is True
    assert result.output.partial is True
    assert result.output.failed_agents == ["content"]
    assert result.output.response == "Research result"


@pytest.mark.asyncio
async def test_sequential_plan_preserves_independent_upstream_success(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research","analytics","content"],'
        '"reason":"Content depends on available upstream findings"}'
    )
    research = mock_agent("market_research", "Research unavailable", success=False)
    analytics = mock_agent("analytics-reflection-agent", "Analytics result")
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(
        context,
        agents={
            "market_research": research,
            "analytics-reflection-agent": analytics,
            "content": content,
        },
    )

    result = await planner.run(message="Research, analyze, then write a post")

    assert result.success is True
    assert result.output.partial is True
    assert result.output.failed_agents == ["market_research"]
    analytics.run.assert_awaited_once()
    content.run.assert_awaited_once()
    content_prompt = content.run.await_args.kwargs["prompt"]
    assert "Analytics result" in content_prompt
    assert "Research unavailable" not in content_prompt


@pytest.mark.asyncio
async def test_parallel_plan_converts_unexpected_exception_to_partial_result(
    dependencies,
):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research","analytics"],'
        '"reason":"Independent work"}'
    )
    planner = PlannerAgent(context)
    planner._run_one = AsyncMock(
        side_effect=[
            AgentResult(
                agent_name="market_research",
                success=True,
                output="Research result",
            ),
            RuntimeError("Unexpected analytics crash"),
        ]
    )

    result = await planner.run(message="Research and analyze performance")

    assert result.success is True
    assert result.output.partial is True
    assert result.output.failed_agents == ["analytics-reflection-agent"]
    assert result.output.response == "Research result"


@pytest.mark.asyncio
async def test_returns_failure_when_all_agents_fail(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["content"],'
        '"execution":"single",'
        '"reason":"User requested content"}'
    )
    content = mock_agent(
        "content",
        "Bedrock unavailable",
        success=False,
    )
    planner = PlannerAgent(context, agents={"content": content})

    result = await planner.run(message="Write a post")

    assert result.success is False
    assert "All planned agents failed" in result.output
    assert "Bedrock unavailable" in result.output


@pytest.mark.asyncio
async def test_general_chat_uses_memory_repository(dependencies):
    context, bedrock, repository = dependencies
    memory_id = uuid4()
    repository.search.return_value = [
        SimpleNamespace(
            id=memory_id,
            content="Our positioning is workflow automation.",
        )
    ]
    bedrock.generate_text.side_effect = [
        (
            '{"intents":["general"],'
            '"execution":"single",'
            '"reason":"Memory-grounded question"}'
        ),
        "Your positioning is workflow automation.",
    ]
    planner = PlannerAgent(context)

    result = await planner.run(message="What is our positioning?")

    assert result.success is True
    assert result.output.response == (
        "Your positioning is workflow automation."
    )
    assert result.output.sub_results[0].metadata["memory_ids"] == [
        str(memory_id)
    ]
    repository.search.assert_awaited_once_with(
        company_id=context.company_id,
        query="What is our positioning?",
        k=5,
        types=[
            "episodic",
            "semantic",
            "user",
            "task",
            "reflection",
        ],
    )


@pytest.mark.asyncio
async def test_missing_agent_is_reported_as_failure(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        '{"intents":["research"],'
        '"execution":"single",'
        '"reason":"User requested research"}'
    )
    planner = PlannerAgent(context)

    result = await planner.run(message="Research competitors")

    assert result.success is False
    assert "market_research" in result.output
    assert "is not available" in result.output


@pytest.mark.asyncio
async def test_invalid_classifier_output_uses_keyword_fallback(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = "not valid JSON"
    research = mock_agent("market_research", "Research result")
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(
        context,
        agents={"market_research": research, "content": content},
    )

    result = await planner.run(message="Research competitors and write a post")

    assert result.success is True
    assert result.output.decision.intents == [Intent.RESEARCH, Intent.CONTENT]
    assert result.output.decision.execution == ExecutionMode.SEQUENTIAL
    assert result.output.decision.reason == "Deterministic keyword fallback"


@pytest.mark.asyncio
async def test_classifier_extracts_json_surrounded_by_model_commentary(dependencies):
    context, bedrock, _ = dependencies
    bedrock.generate_text.return_value = (
        "Here is the classification:\n"
        '{"intents":["content"],"reason":"User requested a post"}\n'
        "I hope this helps."
    )
    content = mock_agent("content", "Generated post")
    planner = PlannerAgent(context, agents={"content": content})

    result = await planner.run(message="Write a launch post")

    assert result.success is True
    assert result.output.decision.intents == [Intent.CONTENT]
    assert result.output.decision.execution == ExecutionMode.SINGLE


@pytest.mark.asyncio
async def test_classifier_call_failure_uses_general_fallback(dependencies):
    context, bedrock, repository = dependencies
    bedrock.generate_text.side_effect = [
        RuntimeError("Bedrock timeout"),
        "I do not have enough stored context to answer.",
    ]
    repository.search.return_value = []
    planner = PlannerAgent(context)

    result = await planner.run(message="Can you help me?")

    assert result.success is True
    assert result.output.decision.intents == [Intent.GENERAL]
    assert result.output.decision.reason == "Deterministic keyword fallback"
