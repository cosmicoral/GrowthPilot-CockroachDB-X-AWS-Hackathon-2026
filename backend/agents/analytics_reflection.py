"""Analytics and reflection agent for simulated campaign performance."""

from __future__ import annotations

import json
from typing import Literal, cast
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from backend.agents.base import Agent
from backend.memory.store import MemoryHit

GroupBy = Literal[
    "theme",
    "icp",
    "messaging_angle",
]

VALID_GROUP_BY: tuple[str, ...] = (
    "theme",
    "icp",
    "messaging_angle",
)

SYSTEM_PROMPT = """
You are GrowthPilot's Analytics and Reflection Agent.

You receive aggregated performance metrics from simulated LinkedIn posts.

Rules:
- Use only the supplied metrics.
- Explicitly describe the data as simulated performance data.
- Cite concrete likes, comments, and clicks from the supplied analysis.
- Do not invent impressions, conversions, signups, revenue, or other metrics.
- Treat explanations as hypotheses, not proven causal conclusions.
- Identify the best-performing group.
- Suggest one concrete next content experiment.
- Keep the reflection concise and useful to a future Content Generation Agent.
""".strip()

class EngagementMetrics(BaseModel):
    """Engagement metrics for one simulated content piece."""

    likes: int = Field(ge=0, strict=True)
    comments: int = Field(ge=0, strict=True)
    clicks: int = Field(ge=0, strict=True)

    @property
    def total(self) -> int:
        """Return total measured engagement."""

        return self.likes + self.comments + self.clicks

class PerformancePost(BaseModel):
    """Validated performance data extracted from one episodic memory."""

    memory_id: UUID
    content_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    theme: str = Field(min_length=1)
    icp: str = Field(min_length=1)
    messaging_angle: str = Field(min_length=1)
    engagement: EngagementMetrics

class GroupPerformance(BaseModel):
    """Aggregated engagement metrics for one comparison group."""

    group_name: str
    post_count: int = Field(ge=1)
    total_likes: int = Field(ge=0)
    total_comments: int = Field(ge=0)
    total_clicks: int = Field(ge=0)
    total_engagement: int = Field(ge=0)
    average_engagement_per_post: float = Field(ge=0)

class AnalyticsReflectionOutput(BaseModel):
    """Structured output returned by the analytics agent."""

    group_by: GroupBy
    post_count: int = Field(ge=2)
    groups: list[GroupPerformance]
    best_group: str
    reflection: str
    reflection_memory_id: UUID | None = None

class AnalyticsReflectionAgent(Agent):
    """Compare simulated post performance and persist a reflection."""

    @property
    def name(self) -> str:
        return "analytics-reflection-agent"

    async def retrieve_memories(
        self,
        *,
        limit: int = 50,
        **kwargs,
    ) -> list[MemoryHit]:
        """
        Retrieve recent episodic memories.

        Recent retrieval is used instead of semantic search because analytics
        should operate over the complete available performance dataset.
        """

        return await self.context.memory_repository.recent(
            company_id=self.context.company_id,
            memory_type="episodic",
            limit=limit,
        )


    @staticmethod
    def _parse_performance_post(
        memory: MemoryHit,
    ) -> PerformancePost | None:
        """Convert one eligible memory into validated performance data."""

        metadata = memory.metadata

        if metadata.get("channel") != "linkedin":
            return None

        if metadata.get("status") != "published":
            return None

        if metadata.get("simulated") is not True:
            return None

        required_string_fields = (
            "content_id",
            "title",
            "theme",
            "icp",
            "messaging_angle",
        )

        for field_name in required_string_fields:
            value = metadata.get(field_name)

            if not isinstance(value, str) or not value.strip():
                return None

        engagement = metadata.get("engagement")

        if not isinstance(engagement, dict):
            return None

        try:
            return PerformancePost(
                memory_id=memory.id,
                content_id=metadata["content_id"],
                title=metadata["title"],
                theme=metadata["theme"],
                icp=metadata["icp"],
                messaging_angle=metadata["messaging_angle"],
                engagement=EngagementMetrics.model_validate(engagement),
            )
        except ValidationError:
            return None

    @staticmethod
    def _aggregate(
        posts: list[PerformancePost],
        group_by: GroupBy,
    ) -> list[GroupPerformance]:
        """Aggregate performance by the requested content dimension."""

        grouped_posts: dict[str, list[PerformancePost]] = {}

        for post in posts:
            group_name = getattr(post, group_by)
            grouped_posts.setdefault(group_name, []).append(post)

        groups: list[GroupPerformance] = []

        for group_name in sorted(grouped_posts):
            group_posts = grouped_posts[group_name]

            total_likes = sum(
                post.engagement.likes
                for post in group_posts
            )
            total_comments = sum(
                post.engagement.comments
                for post in group_posts
            )
            total_clicks = sum(
                post.engagement.clicks
                for post in group_posts
            )
            total_engagement = (
                total_likes
                + total_comments
                + total_clicks
            )

            groups.append(
                GroupPerformance(
                    group_name=group_name,
                    post_count=len(group_posts),
                    total_likes=total_likes,
                    total_comments=total_comments,
                    total_clicks=total_clicks,
                    total_engagement=total_engagement,
                    average_engagement_per_post=round(
                        total_engagement / len(group_posts),
                        2,
                    ),
                )
            )

        return groups

    @staticmethod
    def _build_prompt(
        *,
        group_by: GroupBy,
        post_count: int,
        groups: list[GroupPerformance],
        best_group: str,
    ) -> str:
        """Build the reflection prompt from deterministic analysis results."""

        analysis = {
            "data_source": "simulated_linkedin_performance",
            "group_by": group_by,
            "post_count": post_count,
            "best_group_by_average_engagement": best_group,
            "groups": [
                group.model_dump(mode="json")
                for group in groups
            ],
        }

        return (
            "Turn the following deterministic performance analysis into "
            "a concise plain-language reflection.\n\n"
            f"{json.dumps(analysis, indent=2, sort_keys=True)}\n\n"
            "The response must contain:\n"
            "1. The best-performing group and exact supporting metrics.\n"
            "2. A possible explanation clearly labelled as a hypothesis.\n"
            "3. One concrete recommendation for the next content experiment."
        )

    async def process(
        self,
        retrieved_memories: list[MemoryHit],
        *,
        group_by: GroupBy = "theme",
        **kwargs,
    ) -> AnalyticsReflectionOutput:
        """Analyze performance and generate a natural-language reflection."""

        if group_by not in VALID_GROUP_BY:
            allowed = ", ".join(VALID_GROUP_BY)
            raise ValueError(
                f"Unsupported group_by value '{group_by}'. "
                f"Expected one of: {allowed}"
            )

        normalized_group_by = cast(GroupBy, group_by)

        posts = [
            post
            for memory in retrieved_memories
            if (
                post := self._parse_performance_post(memory)
            ) is not None
        ]

        if len(posts) < 2:
            raise ValueError(
                "Analytics requires at least two valid simulated "
                "LinkedIn performance records"
            )

        groups = self._aggregate(
            posts,
            normalized_group_by,
        )

        if len(groups) < 2:
            raise ValueError(
                "Analytics requires at least two groups for "
                f"group_by='{normalized_group_by}'"
            )

        ranked_groups = sorted(
            groups,
            key=lambda group: (
                -group.average_engagement_per_post,
                group.group_name,
            ),
        )
        best_group = ranked_groups[0].group_name

        prompt = self._build_prompt(
            group_by=normalized_group_by,
            post_count=len(posts),
            groups=groups,
            best_group=best_group,
        )

        reflection = await self.context.bedrock_client.generate_text(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=500,
            temperature=0.2,
        )

        reflection = reflection.strip()

        if not reflection:
            raise ValueError("Bedrock returned an empty reflection")

        return AnalyticsReflectionOutput(
            group_by=normalized_group_by,
            post_count=len(posts),
            groups=groups,
            best_group=best_group,
            reflection=reflection,
        )

    async def persist_memories(
        self,
        result_data: AnalyticsReflectionOutput,
    ) -> None:
        """Persist the generated reflection for future agent runs."""

        memory_id = await self.context.memory_repository.write(
            company_id=self.context.company_id,
            memory_type="reflection",
            content=result_data.reflection,
            metadata={
                "source": self.name,
                "simulated": True,
                "channel": "linkedin",
                "group_by": result_data.group_by,
                "best_group": result_data.best_group,
                "post_count": result_data.post_count,
                "aggregates": [
                    group.model_dump(mode="json")
                    for group in result_data.groups
                ],
            },
            importance=0.9,
        )

        result_data.reflection_memory_id = memory_id