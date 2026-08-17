"""Seed previous-week demo memories for Sarah's FlowForge AI."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database  # noqa: E402
from backend.llm.client import BedrockClient  # noqa: E402
from backend.memory.embedding import BedrockEmbeddingService  # noqa: E402
from backend.memory.hash import create_content_hash  # noqa: E402
from backend.memory.repository import MemoryRepository  # noqa: E402

COMPANY_ID = UUID("3f2b8c41-6e57-4a92-9d13-7c5e8b24a601")
COMPANY_NAME = "FlowForge AI"
COMPANY_WEBSITE = "https://example.com/flowforge-ai"

DEMO_MEMORIES = [
    {
        "key": "initial-positioning",
        "memory_type": "user",
        "content": (
            "Sarah's initial positioning for FlowForge AI was to help "
            "small and mid-sized SaaS engineering teams reduce repetitive "
            "work, improve engineering workflows, and ship faster."
        ),
        "metadata": {
            "source": "research-agent",
            "founder": "Sarah",
            "stage": "week-1",
            "simulated": True,
        },
        "importance": 0.8,
        "age_days": 7,
    },
    {
        "key": "initial-icp",
        "memory_type": "semantic",
        "content": (
            "Sarah's initial ICP hypothesis is engineering managers and "
            "technical leads at small and mid-sized SaaS companies with "
            "growing engineering teams. These teams are likely to "
            "experience friction from repetitive workflows, coordination, "
            "and delivery processes."
        ),
        "metadata": {
            "source": "research-agent",
            "founder": "Sarah",
            "stage": "week-1",
            "simulated": True,
        },
        "importance": 0.85,
        "age_days": 7,
    },
    {
        "key": "competitor-research",
        "memory_type": "semantic",
        "content": (
            "Sarah identified GitHub Copilot, Linear, Jira, and internal "
            "engineering automation as relevant alternatives for "
            "FlowForge AI. The initial differentiation hypothesis is to "
            "focus on improving end-to-end engineering workflows rather "
            "than competing only as an AI coding assistant."
        ),
        "metadata": {
            "source": "research-agent",
            "founder": "Sarah",
            "stage": "week-1",
            "simulated": True,
        },
        "importance": 0.7,
        "age_days": 7,
    },
    {
        "key": "linkedin-ai-automation-post",
        "memory_type": "episodic",
        "content": (
            "Sarah published a LinkedIn post titled "
            "\"5 engineering tasks your team can automate with AI.\" "
            "The post shared practical examples of using AI to automate "
            "repetitive engineering tasks."
        ),
        "metadata": {
            "source": "content-agent",
            "founder": "Sarah",
            "channel": "linkedin",
            "status": "published",
            "simulated": True,
            "content_id": "linkedin-ai-automation-01",
            "title": "5 engineering tasks your team can automate with AI",
            "theme": "ai_automation",
            "icp": "engineering_managers",
            "messaging_angle": "tactical_list",
            "engagement": {
                "likes": 18,
                "comments": 3,
                "clicks": 7,
            },
        },
        "importance": 0.75,
        "age_days": 6,
    },
    {
        "key": "linkedin-engineering-workflows-post",
        "memory_type": "episodic",
        "content": (
            "Sarah published a LinkedIn post titled "
            "\"5 ways to remove friction from your engineering workflow.\" "
            "The post focused on practical ways engineering teams can "
            "improve planning, development, code review, and delivery."
        ),
        "metadata": {
            "source": "content-agent",
            "founder": "Sarah",
            "channel": "linkedin",
            "status": "published",
            "simulated": True,
            "content_id": "linkedin-engineering-workflow-01",
            "title": "5 ways to remove friction from your engineering workflow",
            "theme": "engineering_workflows",
            "icp": "engineering_managers",
            "messaging_angle": "problem_solution",
            "engagement": {
                "likes": 64,
                "comments": 14,
                "clicks": 29,
            },
        },
        "importance": 0.9,
        "age_days": 5,
    },
    {
        "key": "linkedin-ai-code-review-post",
        "memory_type": "episodic",
        "content": (
            "Sarah published a LinkedIn post titled "
            "\"3 AI automations for faster code review.\" "
            "The post showed technical leads how AI could summarise pull "
            "requests, identify review risks, and prepare review notes."
        ),
        "metadata": {
            "source": "content-agent",
            "founder": "Sarah",
            "channel": "linkedin",
            "status": "published",
            "simulated": True,
            "content_id": "linkedin-ai-code-review-01",
            "title": "3 AI automations for faster code review",
            "theme": "ai_automation",
            "icp": "technical_leads",
            "messaging_angle": "problem_solution",
            "engagement": {
                "likes": 26,
                "comments": 5,
                "clicks": 11,
            },
        },
        "importance": 0.75,
        "age_days": 4,
    },
    {
        "key": "linkedin-release-handoffs-post",
        "memory_type": "episodic",
        "content": (
            "Sarah published a LinkedIn post titled "
            "\"4 release handoffs slowing down growing engineering teams.\" "
            "The post gave technical leads a practical checklist for "
            "reducing friction between development, review, and release."
        ),
        "metadata": {
            "source": "content-agent",
            "founder": "Sarah",
            "channel": "linkedin",
            "status": "published",
            "simulated": True,
            "content_id": "linkedin-release-handoffs-01",
            "title": (
                "4 release handoffs slowing down growing engineering teams"
            ),
            "theme": "engineering_workflows",
            "icp": "technical_leads",
            "messaging_angle": "tactical_list",
            "engagement": {
                "likes": 55,
                "comments": 12,
                "clicks": 24,
            },
        },
        "importance": 0.88,
        "age_days": 3,
    },
    {
        "key": "previous-week-reflection",
        "memory_type": "reflection",
        "content": (
            "Last week's LinkedIn experiment showed that engineering "
            "workflow content generated significantly more engagement "
            "than AI automation content. The engineering workflow post "
            "received substantially more likes, comments, and clicks. "
            "Future content should focus more on practical engineering "
            "workflow problems, lessons, and improvements."
        ),
        "metadata": {
            "source": "reflection-agent",
            "founder": "Sarah",
            "stage": "previous-week-reflection",
            "simulated": True,
            "seed_role": "baseline-reflection",
        },
        "importance": 0.95,
        "age_days": 2,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seed previous-week demo memories for Sarah's FlowForge AI."
        )
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the demo company and all associated memories.",
    )

    return parser.parse_args()


async def ensure_company() -> None:
    """Create or refresh the fixed FlowForge AI demo company."""

    async with database.pool.acquire() as connection:
        await connection.execute(
            """
            INSERT INTO companies
            (
                id,
                name,
                website,
                industry,
                description
            )
            VALUES
            (
                $1,
                $2,
                $3,
                $4,
                $5
            )
            ON CONFLICT (id)
            DO UPDATE SET
                name = excluded.name,
                website = excluded.website,
                industry = excluded.industry,
                description = excluded.description
            """,
            COMPANY_ID,
            COMPANY_NAME,
            COMPANY_WEBSITE,
            "B2B SaaS / AI",
            (
                "AI-powered engineering workflow assistant for "
                "small and mid-sized SaaS teams."
            ),
        )


async def cleanup() -> None:
    """Delete the FlowForge AI demo company and its memories."""

    async with database.pool.acquire() as connection:
        result = await connection.execute(
            """
            DELETE FROM companies
            WHERE id = $1
            """,
            COMPANY_ID,
        )

    print(f"Cleanup completed: {result}")


async def seed_memories() -> None:
    """Seed Sarah's previous-week demo memories."""

    await ensure_company()

    bedrock_client = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock_client)
    repository = MemoryRepository(
        embedding_service=embedding_service,
    )

    seed_time = datetime.now(timezone.utc)

    inserted = 0
    reused = 0

    for index, memory in enumerate(DEMO_MEMORIES, start=1):
        content = memory["content"]
        content_hash = create_content_hash(content)

        memory_id = await repository.get_by_content_hash(
            COMPANY_ID,
            content_hash,
        )

        if memory_id is None:
            memory_id = await repository.write(
                company_id=COMPANY_ID,
                memory_type=memory["memory_type"],
                content=content,
                metadata={
                    **memory["metadata"],
                    "demo_key": memory["key"],
                    "product": "FlowForge AI",
                },
                importance=memory["importance"],
            )

            inserted += 1
            action = "inserted"
        else:
            reused += 1
            action = "reused"

        created_at = seed_time - timedelta(
            days=memory["age_days"],
        )

        async with database.pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE memories
                SET
                    memory_type = $3,
                    metadata = $4,
                    importance = $5,
                    created_at = $6
                WHERE company_id = $1 AND id = $2
                """,
                COMPANY_ID,
                memory_id,
                memory["memory_type"],
                {
                    **memory["metadata"],
                    "demo_key": memory["key"],
                    "product": "FlowForge AI",
                    "age_days": memory["age_days"],
                },
                memory["importance"],
                created_at,
            )

        print(
            f"[{index:02d}/{len(DEMO_MEMORIES)}] "
            f"{action}: {memory['key']}"
        )

    async with database.pool.acquire() as connection:
        stored_count = await connection.fetchval(
            """
            SELECT count(*)
            FROM memories
            WHERE company_id = $1
            """,
            COMPANY_ID,
        )

    print()
    print("FlowForge AI demo seed completed")
    print(f"Company ID: {COMPANY_ID}")
    print(f"Inserted: {inserted}")
    print(f"Reused: {reused}")
    print(f"Stored memories: {stored_count}")


async def main() -> None:
    args = parse_args()

    await database.connect()

    try:
        if args.cleanup:
            await cleanup()
        else:
            await seed_memories()
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())