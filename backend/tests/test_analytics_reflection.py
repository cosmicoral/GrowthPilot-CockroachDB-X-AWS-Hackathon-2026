"""Tests for the Analytics and Reflection Agent."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, call
from uuid import uuid4

import pytest

from backend.agents.analytics_reflection import (
    AnalyticsReflectionAgent,
    AnalyticsReflectionOutput,
)


from backend.agents.context import AgentContext
from backend.agents.skills.loader import SkillLoader
from backend.memory.store import MemoryHit
from backend.memory.stub import InMemoryStore

COMPANY_ID = uuid4()

GENERATED_REFLECTION = (
    "The simulated performance data shows that engineering_workflows "
    "performed best, generating 119 likes, 26 comments, and 53 clicks. "
    "A possible hypothesis is that practical workflow problems feel more "
    "immediately relevant to engineering teams. The next experiment should "
    "test another workflow-focused post with a different opening hook."
)


def make_memory(
    *,
    content_id: str,
    title: str,
    theme: str,
    icp: str,
    messaging_angle: str,
    likes: int,
    comments: int,
    clicks: int,
    channel: str = "linkedin",
    status: str = "published",
    simulated: bool = True,
) -> MemoryHit:
    """Create one valid simulated performance memory."""

    return MemoryHit(
        id=uuid4(),
        company_id=COMPANY_ID,
        content=title,
        memory_type="episodic",
        metadata={
            "source": "content-agent",
            "channel": channel,
            "status": status,
            "simulated": simulated,
            "content_id": content_id,
            "title": title,
            "theme": theme,
            "icp": icp,
            "messaging_angle": messaging_angle,
            "engagement": {
                "likes": likes,
                "comments": comments,
                "clicks": clicks,
            },
        },
        importance=0.8,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def performance_memories() -> list[MemoryHit]:
    return [
        make_memory(
            content_id="ai-automation-01",
            title="5 engineering tasks to automate with AI",
            theme="ai_automation",
            icp="engineering_managers",
            messaging_angle="tactical_list",
            likes=18,
            comments=3,
            clicks=7,
        ),
        make_memory(
            content_id="workflow-01",
            title="5 ways to remove engineering workflow friction",
            theme="engineering_workflows",
            icp="engineering_managers",
            messaging_angle="problem_solution",
            likes=64,
            comments=14,
            clicks=29,
        ),
        make_memory(
            content_id="ai-code-review-01",
            title="3 AI automations for code review",
            theme="ai_automation",
            icp="technical_leads",
            messaging_angle="problem_solution",
            likes=26,
            comments=5,
            clicks=11,
        ),
        make_memory(
            content_id="release-handoff-01",
            title="4 release handoffs slowing down teams",
            theme="engineering_workflows",
            icp="technical_leads",
            messaging_angle="tactical_list",
            likes=55,
            comments=12,
            clicks=24,
        ),
    ]


def build_agent(
    memories: list[MemoryHit],
    *,
    reflection: str = GENERATED_REFLECTION,
):
    """Create an agent with mocked production dependencies."""

    bedrock = AsyncMock()
    bedrock.generate_text.return_value = reflection

    repository = AsyncMock()
    repository.recent.return_value = memories
    repository.write.return_value = uuid4()

    context = AgentContext(
        company_id=COMPANY_ID,
        bedrock_client=bedrock,
        memory_repository=repository,
    )

    return (
        AnalyticsReflectionAgent(context),
        bedrock,
        repository,
    )


def test_agent_name(performance_memories):
    agent, _, _ = build_agent(performance_memories)

    assert agent.name == "analytics-reflection-agent"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "group_by",
        "expected_best_group",
        "expected_averages",
        "expected_best_metrics",
    ),
    [
        (
            "theme",
            "engineering_workflows",
            {
                "ai_automation": 35.0,
                "engineering_workflows": 99.0,
            },
            (119, 26, 53),
        ),
        (
            "icp",
            "engineering_managers",
            {
                "engineering_managers": 67.5,
                "technical_leads": 66.5,
            },
            (82, 17, 36),
        ),
        (
            "messaging_angle",
            "problem_solution",
            {
                "problem_solution": 74.5,
                "tactical_list": 59.5,
            },
            (90, 19, 40),
        ),
    ],
)
async def test_agent_aggregates_supported_dimensions(
    performance_memories,
    group_by,
    expected_best_group,
    expected_averages,
    expected_best_metrics,
):
    likes, comments, clicks = expected_best_metrics
    reflection = (
        "The simulated performance data shows that "
        f"{expected_best_group} performed best, generating {likes} likes, "
        f"{comments} comments, and {clicks} clicks. A possible hypothesis "
        "is that this approach resonated with the audience. The next "
        "experiment should test another post in this group."
    )
    agent, _, _ = build_agent(
        performance_memories,
        reflection=reflection,
    )

    result = await agent.run(group_by=group_by)

    assert result.success is True
    assert isinstance(
        result.output,
        AnalyticsReflectionOutput,
    )

    output = result.output

    assert output.group_by == group_by
    assert output.post_count == 4
    assert output.best_group == expected_best_group
    assert output.analyzed_memory_ids == [
        memory.id
        for memory in performance_memories
    ]
    assert output.reflection == reflection
    assert output.reflection_memory_id is not None

    groups = {
        group.group_name: group
        for group in output.groups
    }

    assert set(groups) == set(expected_averages)

    for group_name, expected_average in expected_averages.items():
        assert (
            groups[group_name].average_engagement_per_post
            == expected_average
        )


@pytest.mark.asyncio
async def test_theme_analysis_uses_correct_metric_totals(
    performance_memories,
):
    agent, _, _ = build_agent(performance_memories)

    result = await agent.run(group_by="theme")

    assert result.success is True

    groups = {
        group.group_name: group
        for group in result.output.groups
    }

    ai_group = groups["ai_automation"]

    assert ai_group.post_count == 2
    assert ai_group.total_likes == 44
    assert ai_group.total_comments == 8
    assert ai_group.total_clicks == 18
    assert ai_group.total_engagement == 70

    workflow_group = groups["engineering_workflows"]

    assert workflow_group.post_count == 2
    assert workflow_group.total_likes == 119
    assert workflow_group.total_comments == 26
    assert workflow_group.total_clicks == 53
    assert workflow_group.total_engagement == 198


@pytest.mark.asyncio
async def test_retrieves_recent_episodic_memories(
    performance_memories,
):
    agent, _, repository = build_agent(performance_memories)

    await agent.run(
        group_by="theme",
        limit=25,
    )

    repository.recent.assert_awaited_once_with(
        company_id=COMPANY_ID,
        memory_type="episodic",
        limit=25,
    )


@pytest.mark.asyncio
async def test_ignores_ineligible_memories(
    performance_memories,
):
    ineligible = [
        make_memory(
            content_id="x-post",
            title="An X post",
            theme="ai_automation",
            icp="technical_leads",
            messaging_angle="tactical_list",
            likes=500,
            comments=100,
            clicks=200,
            channel="x",
        ),
        make_memory(
            content_id="draft-post",
            title="Unpublished draft",
            theme="ai_automation",
            icp="technical_leads",
            messaging_angle="tactical_list",
            likes=500,
            comments=100,
            clicks=200,
            status="draft",
        ),
        make_memory(
            content_id="live-post",
            title="Non-simulated post",
            theme="ai_automation",
            icp="technical_leads",
            messaging_angle="tactical_list",
            likes=500,
            comments=100,
            clicks=200,
            simulated=False,
        ),
    ]

    agent, _, _ = build_agent(
        performance_memories + ineligible,
    )

    result = await agent.run(group_by="theme")

    assert result.success is True
    assert result.output.post_count == 4

    groups = {
        group.group_name: group
        for group in result.output.groups
    }

    assert groups["ai_automation"].total_likes == 44


@pytest.mark.asyncio
async def test_calls_bedrock_with_deterministic_analysis(
    performance_memories,
):
    agent, bedrock, _ = build_agent(performance_memories)

    result = await agent.run(group_by="theme")

    assert result.success is True

    bedrock.generate_text.assert_awaited_once()

    call = bedrock.generate_text.await_args.kwargs

    assert '"data_source": "simulated_linkedin_performance"' in call["prompt"]
    assert '"best_group_by_average_engagement": "engineering_workflows"' in (
        call["prompt"]
    )
    assert '"total_likes": 119' in call["prompt"]
    assert '"total_comments": 26' in call["prompt"]
    assert '"total_clicks": 53' in call["prompt"]
    assert "simulated" in call["system_prompt"].lower()
    assert call["temperature"] == 0.2
    assert call["max_tokens"] == 500


@pytest.mark.asyncio
async def test_persists_reflection_memory(
    performance_memories,
):
    agent, _, repository = build_agent(performance_memories)

    result = await agent.run(group_by="theme")

    assert result.success is True

    repository.write.assert_awaited_once()

    call = repository.write.await_args.kwargs

    assert call["company_id"] == COMPANY_ID
    assert call["memory_type"] == "reflection"
    assert call["content"] == GENERATED_REFLECTION
    assert call["importance"] == 0.9

    metadata = call["metadata"]

    assert metadata["source"] == "analytics-reflection-agent"
    assert metadata["simulated"] is True
    assert metadata["channel"] == "linkedin"
    assert metadata["group_by"] == "theme"
    assert metadata["best_group"] == "engineering_workflows"
    assert metadata["post_count"] == 4
    assert metadata["analyzed_memory_ids"] == [
        str(memory.id)
        for memory in performance_memories
    ]
    assert len(metadata["aggregates"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reflection",
    [
        (
            "The simulated performance data shows ai_automation performed "
            "best with 119 likes, 26 comments, and 53 clicks. Hypothesis: "
            "the topic resonated. Next, test another practical post."
        ),
        (
            "The simulated performance data shows engineering_workflows "
            "performed best with 120 likes, 26 comments, and 53 clicks. "
            "Hypothesis: the topic resonated. Next, test another post."
        ),
    ],
)
async def test_rejects_ungrounded_reflection_before_persisting(
    performance_memories,
    reflection,
):
    agent, _, repository = build_agent(
        performance_memories,
        reflection=reflection,
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "Bedrock reflection does not" in result.output
    repository.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_fails_when_there_are_not_two_groups(
    performance_memories,
):
    same_group_memories = [
        performance_memories[0],
        performance_memories[2],
    ]

    agent, bedrock, repository = build_agent(
        same_group_memories,
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "at least two groups" in result.output

    bedrock.generate_text.assert_not_awaited()
    repository.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_fails_when_there_are_not_two_valid_posts(
    performance_memories,
):
    agent, bedrock, repository = build_agent(
        [performance_memories[0]],
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "at least two valid" in result.output

    bedrock.generate_text.assert_not_awaited()
    repository.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejects_unsupported_group_by(
    performance_memories,
):
    agent, bedrock, repository = build_agent(
        performance_memories,
    )

    result = await agent.run(group_by="channel")

    assert result.success is False
    assert "Unsupported group_by" in result.output

    bedrock.generate_text.assert_not_awaited()
    repository.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_bedrock_failure_does_not_persist_memory(
    performance_memories,
):
    agent, bedrock, repository = build_agent(
        performance_memories,
    )
    bedrock.generate_text.side_effect = RuntimeError(
        "Bedrock unavailable"
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "Bedrock unavailable" in result.output
    repository.write.assert_not_awaited()


@pytest.mark.asyncio
async def test_memory_write_failure_returns_unsuccessful_result(
    performance_memories,
):
    agent, _, repository = build_agent(
        performance_memories,
    )
    repository.write.side_effect = RuntimeError(
        "Database unavailable"
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "Database unavailable" in result.output


@pytest.mark.asyncio
async def test_future_content_run_can_retrieve_reflection(
    performance_memories,
):
    """
    Confirm the stored reflection is available to a later content run.

    This uses the MemoryStore interface without requiring CockroachDB or
    AWS credentials.
    """

    store = InMemoryStore()

    for memory in performance_memories:
        await store.write(
            company_id=COMPANY_ID,
            memory_type="episodic",
            content=memory.content,
            metadata=memory.metadata,
            importance=memory.importance,
        )

    bedrock = AsyncMock()
    bedrock.generate_text.return_value = GENERATED_REFLECTION

    context = AgentContext(
        company_id=COMPANY_ID,
        bedrock_client=bedrock,
        memory_repository=store,
    )
    agent = AnalyticsReflectionAgent(context)

    result = await agent.run(group_by="theme")

    assert result.success is True
    assert result.output.reflection_memory_id is not None

    retrieved = await store.search(
        company_id=COMPANY_ID,
        query="engineering workflows engagement",
        types=["reflection"],
        k=5,
    )

    assert len(retrieved) == 1
    assert retrieved[0].id == result.output.reflection_memory_id
    assert retrieved[0].memory_type == "reflection"
    assert retrieved[0].content == GENERATED_REFLECTION

    future_content_prompt = (
        "Use this previous campaign reflection when creating the next post:\n"
        f"{retrieved[0].content}"
    )

    assert GENERATED_REFLECTION in future_content_prompt


def test_campaign_analysis_skill_is_discovered_and_loaded():
    skills_dir = Path("backend/agents/skills")
    loader = SkillLoader(skills_dir)

    discovered = loader.discover()

    assert "campaign_analysis" in discovered

    skill = loader.load("campaign_analysis")

    assert skill is not None
    assert skill.name == "campaign-analysis"
    assert "campaign performance" in skill.description.lower()
    assert "Identify the most important performance metrics." in skill.instructions


@pytest.mark.asyncio
async def test_analytics_agent_uses_campaign_analysis_skill(
    performance_memories,
):
    agent, bedrock, _ = build_agent(performance_memories)

    result = await agent.run(group_by="theme")

    assert result.success is True

    call = bedrock.generate_text.await_args.kwargs

    assert "campaign performance" in call["prompt"].lower()
    assert "Identify the most important performance metrics." in call["prompt"]


@pytest.mark.asyncio
async def test_missing_campaign_analysis_skill_is_handled_gracefully(
    performance_memories,
):
    agent, bedrock, repository = build_agent(performance_memories)

    agent.context.skill_loader = SkillLoader(
        Path("backend/agents/skills/does-not-exist")
    )

    result = await agent.run(group_by="theme")

    assert result.success is False
    assert "Required campaign-analysis skill is unavailable" in result.output

    bedrock.generate_text.assert_not_awaited()
    repository.write.assert_not_awaited()