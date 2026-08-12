"""Run the Analytics and Reflection Agent for the FlowForge AI demo."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.agents.analytics_reflection import (  # noqa: E402
    AnalyticsReflectionAgent,
)
from backend.agents.context import AgentContext  # noqa: E402
from backend.database.database import database  # noqa: E402
from backend.llm.client import BedrockClient  # noqa: E402
from backend.memory.embedding import BedrockEmbeddingService  # noqa: E402
from backend.memory.repository import MemoryRepository  # noqa: E402
from scripts.seed_demo_founder import COMPANY_ID  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze simulated FlowForge AI LinkedIn performance and "
            "persist a reflection."
        )
    )

    parser.add_argument(
        "--group-by",
        choices=(
            "theme",
            "icp",
            "messaging_angle",
        ),
        default="theme",
        help="Performance dimension to compare.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of recent episodic memories to inspect.",
    )

    return parser.parse_args()


async def run_agent(
    *,
    group_by: str,
    limit: int,
) -> int:
    """Construct production dependencies and execute the agent."""

    if limit <= 0:
        raise ValueError("--limit must be positive")

    bedrock_client = BedrockClient()
    embedding_service = BedrockEmbeddingService(
        bedrock_client,
    )
    repository = MemoryRepository(
        embedding_service=embedding_service,
    )

    context = AgentContext(
        company_id=COMPANY_ID,
        bedrock_client=bedrock_client,
        memory_repository=repository,
    )
    agent = AnalyticsReflectionAgent(context)

    result = await agent.run(
        group_by=group_by,
        limit=limit,
    )

    print()
    print("Analytics & Reflection Agent")
    print(f"Company ID: {COMPANY_ID}")
    print(f"Success: {result.success}")

    if not result.success:
        print(f"Error: {result.output}")
        return 1

    print(result.output.model_dump_json(indent=2))
    return 0


async def main() -> int:
    args = parse_args()

    await database.connect()

    try:
        return await run_agent(
            group_by=args.group_by,
            limit=args.limit,
        )
    finally:
        await database.disconnect()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))