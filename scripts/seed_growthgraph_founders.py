"""Seed deterministic synthetic GrowthGraph founders for T35.

This script intentionally does NOT use AWS Bedrock.

It creates:
    - 75 deterministic synthetic companies
    - 5 memories per company
    - deterministic local VECTOR(1024) embeddings

The data is intended for testing T36's cross-company GrowthGraph query.

Usage:
    python scripts/seed_growthgraph_founders.py
    python scripts/seed_growthgraph_founders.py --count 75
    python scripts/seed_growthgraph_founders.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid5

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database  # noqa: E402
from backend.memory.hash import create_content_hash  # noqa: E402


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED_NAMESPACE = UUID("f2f5f2a0-6b8b-4b8e-9f4b-9d3f6b1c2e40")

DEFAULT_FOUNDER_COUNT = 75
MIN_FOUNDER_COUNT = 50
MAX_FOUNDER_COUNT = 100

EMBEDDING_DIMENSION = 1024


# ---------------------------------------------------------------------------
# Synthetic data
# ---------------------------------------------------------------------------

INDUSTRIES = [
    "B2B SaaS / DevTools",
    "B2B SaaS / Fintech",
    "B2B SaaS / HR Tech",
    "B2B SaaS / MarTech",
    "Consumer / Health & Wellness",
    "Consumer / EdTech",
    "Vertical SaaS / Logistics",
    "Vertical SaaS / Legal",
    "Vertical SaaS / Real Estate",
    "AI Infra / Data Tooling",
]

ICPS = [
    "engineering managers at mid-sized SaaS companies",
    "solo founders bootstrapping their first product",
    "marketing leads at Series A startups",
    "operations managers at logistics companies",
    "compliance officers at regulated fintechs",
    "HR business partners at scaling remote teams",
    "clinicians running small private practices",
    "property managers overseeing five to twenty units",
]

CHANNELS = [
    "linkedin",
    "twitter",
    "newsletter",
    "blog",
]

THEMES = [
    "product_education",
    "founder_story",
    "customer_case_study",
    "industry_trend",
    "tactical_howto",
    "pricing_positioning",
]

MESSAGING_ANGLES = [
    "problem_solution",
    "tactical_list",
    "contrarian_take",
    "data_led",
]

FOUNDER_NAMES = [
    "Priya",
    "Jordan",
    "Aisha",
    "Mateo",
    "Nina",
    "Kwame",
    "Elena",
    "Sam",
    "Noor",
    "Diego",
    "Freya",
    "Tariq",
    "Lucia",
    "Owen",
    "Yuki",
    "Iris",
    "Rafael",
    "Mei",
    "Hassan",
    "Sofia",
    "Kenji",
    "Amara",
    "Leo",
    "Zara",
    "Felix",
    "Ingrid",
    "Omar",
    "Chiara",
    "Viktor",
    "Aaliyah",
]

CONTENT_TITLE_TEMPLATES = {
    "product_education": "How {icp_short} actually use {product}",
    "founder_story": "Why I started {company} for {icp_short}",
    "customer_case_study": (
        "How one {icp_short} team cut wasted work with {product}"
    ),
    "industry_trend": (
        "What's changing for {icp_short} in {industry_short}"
    ),
    "tactical_howto": (
        "{n} ways {icp_short} can save time this week"
    ),
    "pricing_positioning": (
        "Why we priced {product} the way we did"
    ),
}


# ---------------------------------------------------------------------------
# Deterministic IDs
# ---------------------------------------------------------------------------

def derive_company_id(index: int) -> UUID:
    """Return the deterministic UUID for synthetic founder `index`."""

    return uuid5(
        SEED_NAMESPACE,
        f"growthgraph-synthetic-founder-{index}",
    )


def derive_memory_id(company_id: UUID, memory_index: int) -> UUID:
    """Return a deterministic UUID for a synthetic memory."""

    return uuid5(
        company_id,
        f"growthgraph-memory-{memory_index}",
    )


# ---------------------------------------------------------------------------
# Deterministic vectors
# ---------------------------------------------------------------------------

def deterministic_embedding(text: str) -> list[float]:
    """Create a deterministic local VECTOR(1024).

    This is NOT an ML embedding.

    It exists solely so the synthetic test data contains valid
    VECTOR(1024) values without requiring AWS Bedrock.
    """

    values: list[float] = []

    seed = text.encode("utf-8")

    # SHA-256 gives 32 bytes per digest.
    # 32 * 32 = 1024 deterministic values.
    for block_index in range(32):
        digest = hashlib.sha256(
            seed + block_index.to_bytes(4, "big")
        ).digest()

        for byte in digest:
            # Map [0, 255] -> approximately [-1.0, 1.0].
            value = (byte / 127.5) - 1.0
            values.append(value)

    if len(values) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSION} vector values, "
            f"got {len(values)}"
        )

    # Normalize the vector.
    magnitude = sum(value * value for value in values) ** 0.5

    if magnitude == 0:
        raise RuntimeError("Generated zero-length vector")

    return [
        value / magnitude
        for value in values
    ]


def to_vector_literal(vector: list[float]) -> str:
    """Convert a vector to CockroachDB vector literal format."""

    if len(vector) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, "
            f"got {len(vector)}"
        )

    return "[" + ",".join(
        f"{value:.8f}"
        for value in vector
    ) + "]"


# ---------------------------------------------------------------------------
# Synthetic founder generation
# ---------------------------------------------------------------------------

def _rng_for_founder(index: int) -> random.Random:
    return random.Random(
        f"growthgraph-founder-seed-{index}"
    )


def _short(text: str) -> str:
    return text.split(",")[0].split(" at ")[0]


def generate_founder(index: int) -> dict:
    """Generate one deterministic synthetic company and five memories."""

    rng = _rng_for_founder(index)

    name = rng.choice(FOUNDER_NAMES)
    industry = rng.choice(INDUSTRIES)
    icp = rng.choice(ICPS)

    product = (
        f"{name}'s "
        f"{industry.split(' / ')[-1]} tool"
    )

    company_name = (
        f"{name} — "
        f"{industry.split(' / ')[-1]} #{index}"
    )

    company_id = derive_company_id(index)

    founder_age_days = rng.randint(3, 60)

    memories: list[dict] = []

    # ---------------------------------------------------------------
    # Memory 1: user positioning
    # ---------------------------------------------------------------

    memories.append(
        {
            "memory_type": "user",
            "content": (
                f"{name}'s initial positioning is to help "
                f"{icp} reduce manual work and make faster "
                f"decisions using {product}."
            ),
            "metadata": {
                "source": "research-agent",
                "founder": name,
                "stage": "week-1",
                "synthetic": True,
            },
            "importance": round(
                rng.uniform(0.60, 0.85),
                2,
            ),
            "age_days": founder_age_days,
        }
    )

    # ---------------------------------------------------------------
    # Memory 2: semantic ICP hypothesis
    # ---------------------------------------------------------------

    memories.append(
        {
            "memory_type": "semantic",
            "content": (
                f"{name}'s ICP hypothesis is {icp}. "
                f"These teams are likely to feel friction from "
                f"manual coordination and inconsistent processes, "
                f"which {product} is meant to remove."
            ),
            "metadata": {
                "source": "research-agent",
                "founder": name,
                "stage": "week-1",
                "synthetic": True,
            },
            "importance": round(
                rng.uniform(0.65, 0.90),
                2,
            ),
            "age_days": founder_age_days,
        }
    )

    # ---------------------------------------------------------------
    # Memories 3-4: content performance
    # ---------------------------------------------------------------

    for post_index in range(2):
        theme = rng.choice(THEMES)
        channel = rng.choice(CHANNELS)
        angle = rng.choice(MESSAGING_ANGLES)

        title = CONTENT_TITLE_TEMPLATES[theme].format(
            icp_short=_short(icp),
            product=product,
            company=name,
            industry_short=industry.split(" / ")[-1],
            n=rng.choice([3, 4, 5]),
        )

        likes = rng.randint(2, 80)
        comments = rng.randint(
            0,
            max(1, likes // 5),
        )
        clicks = rng.randint(
            0,
            max(1, likes // 3),
        )

        memories.append(
            {
                "memory_type": "episodic",
                "content": (
                    f"{name} published a {channel} post "
                    f'titled "{title}". '
                    f"The post targeted {icp} with a "
                    f"{angle.replace('_', ' ')} angle."
                ),
                "metadata": {
                    "source": "content-agent",
                    "founder": name,
                    "channel": channel,
                    "status": "published",
                    "synthetic": True,
                    "theme": theme,
                    "messaging_angle": angle,
                    "engagement": {
                        "likes": likes,
                        "comments": comments,
                        "clicks": clicks,
                    },
                },
                "importance": round(
                    rng.uniform(0.50, 0.95),
                    2,
                ),
                "age_days": max(
                    1,
                    founder_age_days
                    - rng.randint(
                        1,
                        founder_age_days,
                    ),
                ),
            }
        )

    # ---------------------------------------------------------------
    # Memory 5: recent reflection
    # ---------------------------------------------------------------

    best_theme = rng.choice(THEMES)

    memories.append(
        {
            "memory_type": "reflection",
            "content": (
                f"Recent content performance suggests "
                f"{_short(icp)} respond best to "
                f"{best_theme.replace('_', ' ')} content. "
                f"Future posts for {name} should lean into "
                f"that theme."
            ),
            "metadata": {
                "source": "reflection-agent",
                "founder": name,
                "synthetic": True,
            },
            "importance": round(
                rng.uniform(0.70, 0.95),
                2,
            ),
            "age_days": 1,
        }
    )

    return {
        "company_id": company_id,
        "company_name": company_name,
        "industry": industry,
        "description": (
            f"{product}, built for {icp}."
        ),
        "memories": memories,
    }


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def seed_company(
    connection,
    founder: dict,
) -> None:
    """Insert/update one synthetic company."""

    await connection.execute(
        """
        INSERT INTO companies (
            id,
            name,
            website,
            industry,
            description
        )
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (id)
        DO UPDATE SET
            name = excluded.name,
            industry = excluded.industry,
            description = excluded.description
        """,
        founder["company_id"],
        founder["company_name"],
        None,
        founder["industry"],
        founder["description"],
    )


async def seed_memory(
    connection,
    company_id: UUID,
    memory: dict,
    memory_index: int,
    seed_time: datetime,
) -> str:
    """Insert one deterministic synthetic memory."""

    content = memory["content"]

    content_hash = create_content_hash(content)

    memory_id = derive_memory_id(
        company_id,
        memory_index,
    )

    vector = deterministic_embedding(content)

    vector_literal = to_vector_literal(vector)

    metadata_json = json.dumps(
        memory["metadata"],
        separators=(",", ":"),
    )

    created_at = (
        seed_time
        - timedelta(days=memory["age_days"])
    )

    # Direct SQL only.
    #
    # We deliberately do not call MemoryRepository here.
    # This avoids the CockroachDB v26.2 active-portal problem
    # encountered by the previous implementation.
    result = await connection.execute(
        f"""
        INSERT INTO memories (
            id,
            company_id,
            memory_type,
            content,
            content_hash,
            metadata,
            importance,
            embedding,
            created_at
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5,
            $6::JSONB,
            $7,
            $8::VECTOR({EMBEDDING_DIMENSION}),
            $9
        )
        ON CONFLICT (company_id, content_hash)
        DO UPDATE SET
            memory_type = excluded.memory_type,
            metadata = excluded.metadata,
            importance = excluded.importance,
            embedding = excluded.embedding,
            created_at = excluded.created_at
        """,
        memory_id,
        company_id,
        memory["memory_type"],
        content,
        content_hash,
        metadata_json,
        memory["importance"],
        vector_literal,
        created_at,
    )

    return result


# ---------------------------------------------------------------------------
# Cohort seeding
# ---------------------------------------------------------------------------

async def seed_founder(
    connection,
    founder: dict,
    seed_time: datetime,
) -> int:
    """Seed one founder directly through SQL."""

    await seed_company(
        connection,
        founder,
    )

    memory_count = 0

    for memory_index, memory in enumerate(
        founder["memories"]
    ):
        await seed_memory(
            connection=connection,
            company_id=founder["company_id"],
            memory=memory,
            memory_index=memory_index,
            seed_time=seed_time,
        )

        memory_count += 1

    return memory_count


async def seed_cohort(count: int) -> None:
    """Seed the complete deterministic synthetic cohort."""

    seed_time = datetime.now(timezone.utc)

    type_counts: dict[str, int] = {}
    industry_counts: dict[str, int] = {}

    total_memories = 0

    # One normal database connection.
    #
    # No nested transaction callbacks.
    # No repository queries.
    # No Bedrock calls.
    async with database.pool.acquire() as connection:
        for index in range(count):
            founder = generate_founder(index)

            memory_count = await seed_founder(
                connection=connection,
                founder=founder,
                seed_time=seed_time,
            )

            total_memories += memory_count

            industry = founder["industry"]
            industry_counts[industry] = (
                industry_counts.get(industry, 0) + 1
            )

            for memory in founder["memories"]:
                memory_type = memory["memory_type"]

                type_counts[memory_type] = (
                    type_counts.get(memory_type, 0) + 1
                )

            print(
                f"[{index + 1:03d}/{count}] "
                f"{founder['company_name']}: "
                f"{memory_count} memories"
            )

    print()
    print("=" * 70)
    print("GrowthGraph synthetic cohort seed completed")
    print("=" * 70)
    print(f"Founders: {count}")
    print(f"Memories: {total_memories}")
    print(f"Vector dimension: {EMBEDDING_DIMENSION}")
    print("Embedding provider: LOCAL / DETERMINISTIC")
    print()
    print("Memory type spread:")
    for memory_type, amount in sorted(
        type_counts.items()
    ):
        print(f"  {memory_type}: {amount}")

    print()
    print("Industry spread:")
    for industry, amount in sorted(
        industry_counts.items()
    ):
        print(f"  {industry}: {amount}")

    print()
    print("AWS / Bedrock was NOT used.")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

async def cleanup() -> None:
    """Remove the complete deterministic T35 cohort."""

    company_ids = [
        derive_company_id(index)
        for index in range(MAX_FOUNDER_COUNT)
    ]

    async with database.pool.acquire() as connection:
        result = await connection.execute(
            """
            DELETE FROM companies
            WHERE id = ANY($1::UUID[])
            """,
            company_ids,
        )

    print(
        f"Cleanup completed for "
        f"{MAX_FOUNDER_COUNT} possible synthetic companies: "
        f"{result}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Seed deterministic synthetic GrowthGraph founders."
        )
    )

    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_FOUNDER_COUNT,
        help=(
            f"Number of founders "
            f"({MIN_FOUNDER_COUNT}-{MAX_FOUNDER_COUNT}, "
            f"default={DEFAULT_FOUNDER_COUNT})."
        ),
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help=(
            "Delete the deterministic synthetic GrowthGraph cohort."
        ),
    )

    args = parser.parse_args()

    if not (
        MIN_FOUNDER_COUNT
        <= args.count
        <= MAX_FOUNDER_COUNT
    ):
        parser.error(
            f"--count must be between "
            f"{MIN_FOUNDER_COUNT} and "
            f"{MAX_FOUNDER_COUNT}"
        )

    return args


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    args = parse_args()

    await database.connect()

    try:
        if args.cleanup:
            await cleanup()
        else:
            await seed_cohort(args.count)
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())