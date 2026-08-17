"""Seed synthetic GrowthGraph founders (T35).

GrowthGraph (T36) is a cross-tenant, anonymised aggregate query over the
`memories` table. T13's demo seed gives us exactly one company, which is
enough to test the single-founder loop but useless for proving a
cross-tenant query actually aggregates across tenants. This script seeds a
larger synthetic cohort so T36 has something real to query against.

Design decisions worth recording (the "why", not just the "what"):

1. Content is template-generated with `random.Random`, not one Bedrock
   text-generation call per founder. Only *embeddings* need to come from
   Bedrock -- the memory content itself just needs to be varied and
   plausible, not creative. This keeps the script fast, free to re-run,
   and deterministic.

2. Every random choice is seeded from the founder's index (see
   `_rng_for_founder`), not from wall-clock time. Re-running the script
   regenerates the exact same companies and memory content every time.
   Combined with the dedup path already built into
   `MemoryRepository.save_memories_batch()` (content_hash + semantic
   similarity), reruns are idempotent: no duplicate rows, no duplicate
   Bedrock embedding calls for content that's already stored.

3. `company_id` is a UUID5 derived from a fixed namespace + founder index
   (`derive_company_id`), not `gen_random_uuid()`. That means the whole
   cohort's ids are reproducible from the index alone -- no manifest file
   needed for T36 or for `--cleanup` to find "our" synthetic companies
   again later.

4. Each founder is written in its own transaction (one
   `save_memories_batch()` call per founder), not one transaction for the
   whole cohort. CockroachDB is SERIALIZABLE by default, so a write
   conflict aborts the *whole* transaction and it has to be retried from
   scratch (see `backend/database/database.py::with_retry`). Seventy-five
   founders' worth of inserts in a single transaction would make every
   retry expensive and hold one long-lived transaction open the whole
   run. Per-founder batches keep each transaction small and each retry
   cheap -- and it matches how a real agent would actually write (one
   founder's memories at a time), not an artefact of seeding in bulk.

5. Embeddings are generated once per founder via
   `BedrockEmbeddingService.generate_embeddings()` (T9's batching path),
   and only for memories whose content_hash isn't already in the table --
   `get_by_content_hash()` is checked first so reruns don't re-pay for
   embeddings on content that's already persisted.

Usage:
    python scripts/seed_growthgraph_founders.py
    python scripts/seed_growthgraph_founders.py --count 100
    python scripts/seed_growthgraph_founders.py --cleanup
    python scripts/seed_growthgraph_founders.py --cleanup --count 100
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid5

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database  # noqa: E402
from backend.llm.client import BedrockClient  # noqa: E402
from backend.memory.embedding import BedrockEmbeddingService  # noqa: E402
from backend.memory.hash import create_content_hash  # noqa: E402
from backend.memory.repository import MemoryRepository  # noqa: E402

# Fixed, non-secret constant. Only used to seed UUID5 / random.Random so
# the synthetic cohort is reproducible across runs -- not a credential.
SEED_NAMESPACE = UUID("f2f5f2a0-6b8b-4b8e-9f4b-9d3f6b1c2e40")

DEFAULT_FOUNDER_COUNT = 75
MIN_FOUNDER_COUNT = 50
MAX_FOUNDER_COUNT = 100

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

CHANNELS = ["linkedin", "twitter", "newsletter", "blog"]

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
    "Priya", "Jordan", "Aisha", "Mateo", "Nina", "Kwame", "Elena", "Sam",
    "Noor", "Diego", "Freya", "Tariq", "Lucia", "Owen", "Yuki", "Iris",
    "Rafael", "Mei", "Hassan", "Sofia", "Kenji", "Amara", "Leo", "Zara",
    "Felix", "Ingrid", "Omar", "Chiara", "Viktor", "Aaliyah",
]

CONTENT_TITLE_TEMPLATES = {
    "product_education": "How {icp_short} actually use {product}",
    "founder_story": "Why I started {company} for {icp_short}",
    "customer_case_study": "How one {icp_short} team cut wasted work with {product}",
    "industry_trend": "What's changing for {icp_short} in {industry_short}",
    "tactical_howto": "{n} ways {icp_short} can save time this week",
    "pricing_positioning": "Why we priced {product} the way we did",
}


def derive_company_id(index: int) -> UUID:
    """Deterministic company_id for founder `index`.

    UUID5 of the fixed namespace + index -- same input always produces the
    same id, so the cohort never needs a manifest file to be found again.
    """

    return uuid5(SEED_NAMESPACE, f"growthgraph-synthetic-founder-{index}")


def _rng_for_founder(index: int) -> random.Random:
    """Seed a Random instance from the founder index, not wall-clock time."""

    return random.Random(f"growthgraph-founder-seed-{index}")


def _short(text: str) -> str:
    return text.split(",")[0].split(" at ")[0]


def generate_founder(index: int) -> dict:
    """Build one synthetic founder: company row + list of memory dicts."""

    rng = _rng_for_founder(index)

    name = rng.choice(FOUNDER_NAMES)
    industry = rng.choice(INDUSTRIES)
    icp = rng.choice(ICPS)
    product = f"{name}'s {industry.split(' / ')[-1]} tool"
    company_name = f"{name} — {industry.split(' / ')[-1]} #{index}"
    company_id = derive_company_id(index)

    # Stagger "signup" age so companies aren't all the same vintage --
    # matters for T36 since a real cohort wouldn't all onboard on day 0.
    founder_age_days = rng.randint(3, 60)

    memories = []

    memories.append({
        "memory_type": "user",
        "content": (
            f"{name}'s initial positioning is to help {icp} "
            f"reduce manual work and make faster decisions using "
            f"{product}."
        ),
        "metadata": {
            "source": "research-agent",
            "founder": name,
            "stage": "week-1",
            "synthetic": True,
        },
        "importance": round(rng.uniform(0.6, 0.85), 2),
        "age_days": founder_age_days,
    })

    memories.append({
        "memory_type": "semantic",
        "content": (
            f"{name}'s ICP hypothesis is {icp}. These teams are likely to "
            f"feel friction from manual coordination and inconsistent "
            f"processes, which {product} is meant to remove."
        ),
        "metadata": {
            "source": "research-agent",
            "founder": name,
            "stage": "week-1",
            "synthetic": True,
        },
        "importance": round(rng.uniform(0.65, 0.9), 2),
        "age_days": founder_age_days,
    })

    # Two published content pieces, varied theme/channel/angle/engagement.
    for post_index in range(2):
        theme = rng.choice(THEMES)
        channel = rng.choice(CHANNELS)
        angle = rng.choice(MESSAGING_ANGLES)
        title = CONTENT_TITLE_TEMPLATES[theme].format(
            icp_short=_short(icp),
            product=product,
            company=company_name.split(" — ")[0],
            industry_short=industry.split(" / ")[-1],
            n=rng.choice([3, 4, 5]),
        )
        likes = rng.randint(2, 80)
        comments = rng.randint(0, max(1, likes // 5))
        clicks = rng.randint(0, max(1, likes // 3))

        memories.append({
            "memory_type": "episodic",
            "content": (
                f"{name} published a {channel} post titled \"{title}\". "
                f"The post targeted {icp} with a {angle.replace('_', ' ')} "
                f"angle."
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
            "importance": round(rng.uniform(0.5, 0.95), 2),
            "age_days": max(1, founder_age_days - rng.randint(1, founder_age_days)),
        })

    # Reflection, always the most recent memory for this founder.
    best_theme = rng.choice(THEMES)
    memories.append({
        "memory_type": "reflection",
        "content": (
            f"Recent content performance suggests {_short(icp)} respond "
            f"best to {best_theme.replace('_', ' ')} content. Future posts "
            f"for {company_name.split(' — ')[0]} should lean into that "
            f"theme."
        ),
        "metadata": {
            "source": "reflection-agent",
            "founder": name,
            "synthetic": True,
        },
        "importance": round(rng.uniform(0.7, 0.95), 2),
        "age_days": max(1, min(m["age_days"] for m in memories) - 1),
    })

    return {
        "company_id": company_id,
        "company_name": company_name,
        "industry": industry,
        "description": (
            f"{product}, built for {icp}."
        ),
        "memories": memories,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed a synthetic cohort of GrowthGraph founders (T35)."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_FOUNDER_COUNT,
        help=(
            f"Number of synthetic founders "
            f"({MIN_FOUNDER_COUNT}-{MAX_FOUNDER_COUNT}, "
            f"default {DEFAULT_FOUNDER_COUNT})."
        ),
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the synthetic cohort's companies and memories.",
    )
    return parser.parse_args()


async def ensure_company(connection, founder: dict) -> None:
    await connection.execute(
        """
        INSERT INTO companies (id, name, website, industry, description)
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


async def seed_founder(
    founder: dict,
    repository: MemoryRepository,
    embedding_service: BedrockEmbeddingService,
    seed_time: datetime,
) -> dict:
    company_id = founder["company_id"]

    async with database.pool.acquire() as connection:
        await ensure_company(connection, founder)

    # Work out which memories are actually new before paying for
    # embeddings -- reruns should be near-free.
    to_embed = []
    for memory in founder["memories"]:
        content_hash = create_content_hash(memory["content"])
        existing_id = await repository.get_by_content_hash(
            company_id, content_hash,
        )
        memory["content_hash"] = content_hash
        memory["existing_id"] = existing_id
        if existing_id is None:
            to_embed.append(memory["content"])

    embeddings_by_content = {}
    if to_embed:
        vectors = await embedding_service.generate_embeddings(to_embed)
        embeddings_by_content = dict(zip(to_embed, vectors))

    memory_inputs = []
    for memory in founder["memories"]:
        if memory["existing_id"] is not None:
            continue
        memory_inputs.append({
            "company_id": company_id,
            "memory_type": memory["memory_type"],
            "content": memory["content"],
            "content_hash": memory["content_hash"],
            "metadata": memory["metadata"],
            "importance": memory["importance"],
            "embedding": embeddings_by_content[memory["content"]],
        })

    inserted_ids = []
    if memory_inputs:
        inserted_ids = await repository.save_memories_batch(memory_inputs)

    # Backdate created_at so recency-decay ranking has something real to
    # rank against, same approach as T13's seed_demo_founder.py.
    async with database.pool.acquire() as connection:
        for memory in founder["memories"]:
            memory_id = memory["existing_id"]
            if memory_id is None:
                # Newly inserted -- look it up by hash now that it exists.
                memory_id = await repository.get_by_content_hash(
                    company_id, memory["content_hash"],
                )
            created_at = seed_time - timedelta(days=memory["age_days"])
            await connection.execute(
                """
                UPDATE memories
                SET importance = $2, created_at = $3
                WHERE id = $1
                """,
                memory_id,
                memory["importance"],
                created_at,
            )

    return {
        "company_id": company_id,
        "inserted": len(memory_inputs),
        "reused": len(founder["memories"]) - len(memory_inputs),
    }


async def cleanup(count: int) -> None:
    company_ids = [derive_company_id(i) for i in range(count)]

    async with database.pool.acquire() as connection:
        result = await connection.execute(
            """
            DELETE FROM companies
            WHERE id = ANY($1::UUID[])
            """,
            company_ids,
        )

    print(f"Cleanup completed for {len(company_ids)} companies: {result}")


async def seed_cohort(count: int) -> None:
    bedrock_client = BedrockClient()
    embedding_service = BedrockEmbeddingService(bedrock_client)
    repository = MemoryRepository(embedding_service=embedding_service)

    seed_time = datetime.now(timezone.utc)

    total_inserted = 0
    total_reused = 0
    type_counts: dict[str, int] = {}
    industry_counts: dict[str, int] = {}

    for index in range(count):
        founder = generate_founder(index)
        industry_counts[founder["industry"]] = (
            industry_counts.get(founder["industry"], 0) + 1
        )
        for memory in founder["memories"]:
            type_counts[memory["memory_type"]] = (
                type_counts.get(memory["memory_type"], 0) + 1
            )

        result = await seed_founder(
            founder, repository, embedding_service, seed_time,
        )
        total_inserted += result["inserted"]
        total_reused += result["reused"]

        print(
            f"[{index + 1:03d}/{count}] {founder['company_name']}: "
            f"inserted={result['inserted']} reused={result['reused']}"
        )

    print()
    print("GrowthGraph synthetic cohort seed completed")
    print(f"Founders: {count}")
    print(f"Memories inserted: {total_inserted}")
    print(f"Memories reused (already present): {total_reused}")
    print(f"Memory type spread: {type_counts}")
    print(f"Industry spread: {industry_counts}")


async def main() -> None:
    args = parse_args()

    if not MIN_FOUNDER_COUNT <= args.count <= MAX_FOUNDER_COUNT:
        print(
            f"--count must be between {MIN_FOUNDER_COUNT} and "
            f"{MAX_FOUNDER_COUNT} (got {args.count})"
        )
        return

    await database.connect()

    try:
        if args.cleanup:
            await cleanup(args.count)
        else:
            await seed_cohort(args.count)
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
