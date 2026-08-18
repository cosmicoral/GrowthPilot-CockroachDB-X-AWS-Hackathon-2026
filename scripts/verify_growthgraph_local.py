from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from pathlib import Path
from uuid import UUID, uuid5


# ---------------------------------------------------------------------------
# Project import path
#
# IMPORTANT: this must run BEFORE any `backend.*` import below, since
# Python resolves imports at the top of the file immediately. Doing the
# sys.path fix after the import (as in an earlier version of this
# script) causes "ModuleNotFoundError: No module named 'backend'" when
# run from outside the project root (e.g. from scripts\ on Windows).
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database.database import database


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED_NAMESPACE = UUID(
    "f2f5f2a0-6b8b-4b8e-9f4b-9d3f6b1c2e40"
)

EMBEDDING_DIMENSION = 1024

QUERY = "What content and messaging approaches have performed well?"

K = 10

MEMORY_TYPES = (
    "reflection",
    "episodic",
)

COMPANY_COUNT = 10


# ---------------------------------------------------------------------------
# Deterministic T35 helpers
# ---------------------------------------------------------------------------

def derive_company_id(index: int) -> UUID:
    """Return the deterministic T35 company UUID."""

    return uuid5(
        SEED_NAMESPACE,
        f"growthgraph-synthetic-founder-{index}",
    )


def deterministic_embedding(text: str) -> list[float]:
    """
    Generate the same deterministic local VECTOR(1024) format
    used by the T35 synthetic seed script.

    This is NOT an ML embedding.

    It exists only for local GrowthGraph verification when AWS
    Bedrock is unavailable.
    """

    values: list[float] = []

    seed = text.encode("utf-8")

    for block_index in range(32):
        digest = hashlib.sha256(
            seed + block_index.to_bytes(4, "big")
        ).digest()

        for byte in digest:
            value = (byte / 127.5) - 1.0
            values.append(value)

    if len(values) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSION} vector values, "
            f"got {len(values)}"
        )

    magnitude = sum(
        value * value
        for value in values
    ) ** 0.5

    if magnitude == 0:
        raise RuntimeError(
            "Generated zero-length vector"
        )

    return [
        value / magnitude
        for value in values
    ]


def to_vector_literal(vector: list[float]) -> str:
    """Convert a vector to CockroachDB VECTOR literal format."""

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
# Metadata helpers
# ---------------------------------------------------------------------------

def parse_metadata(value: object) -> dict:
    """
    Normalize CockroachDB JSONB output.

    Depending on the driver/configuration, JSONB may arrive as:
      - dict
      - JSON string
      - another unexpected value

    Unexpected values are treated as empty metadata.
    """

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}

        return parsed if isinstance(parsed, dict) else {}

    return {}


def count_metadata_field(
    rows: list[dict],
    field: str,
) -> dict[str, int]:
    """
    Count one metadata field across the returned memories.

    Only aggregate counts are returned.
    No company IDs, company names, founders, or memory contents
    are included.
    """

    counts: dict[str, int] = {}

    for row in rows:
        metadata = parse_metadata(
            row.get("metadata")
        )

        value = metadata.get(field)

        if not isinstance(value, str):
            continue

        if not value:
            continue

        counts[value] = counts.get(value, 0) + 1

    return dict(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def top_counts(
    counts: dict[str, int],
    limit: int = 3,
) -> list[tuple[str, int]]:
    """Return the top aggregate values."""

    return list(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    )


# ---------------------------------------------------------------------------
# Aggregate insight
# ---------------------------------------------------------------------------

def build_aggregate_insight(
    rows: list[dict],
) -> dict:
    """
    Build one anonymized aggregate GrowthGraph insight.

    The returned structure contains only aggregate information.

    It deliberately does NOT expose:
      - company IDs
      - company names
      - founder names
      - individual memory contents
      - raw metadata
    """

    if not rows:
        return {
            "summary": (
                "No cross-company insights were found."
            ),
            "top_themes": [],
            "top_channels": [],
            "top_messaging_angles": [],
            "result_count": 0,
        }

    theme_counts = count_metadata_field(
        rows,
        "theme",
    )

    channel_counts = count_metadata_field(
        rows,
        "channel",
    )

    angle_counts = count_metadata_field(
        rows,
        "messaging_angle",
    )

    top_themes = top_counts(
        theme_counts,
        limit=3,
    )

    top_channels = top_counts(
        channel_counts,
        limit=3,
    )

    top_messaging_angles = top_counts(
        angle_counts,
        limit=3,
    )

    if top_themes:
        theme_text = ", ".join(
            theme.replace("_", " ")
            for theme, _ in top_themes
        )

        summary = (
            "Across the selected companies, the most common "
            f"content themes were {theme_text}."
        )
    else:
        summary = (
            "Cross-company results were returned, but no "
            "content theme metadata was available."
        )

    return {
        "summary": summary,
        "top_themes": [
            {
                "theme": theme,
                "count": count,
            }
            for theme, count in top_themes
        ],
        "top_channels": [
            {
                "channel": channel,
                "count": count,
            }
            for channel, count in top_channels
        ],
        "top_messaging_angles": [
            {
                "angle": angle,
                "count": count,
            }
            for angle, count in top_messaging_angles
        ],
        "result_count": len(rows),
    }


# ---------------------------------------------------------------------------
# Main verification
# ---------------------------------------------------------------------------

async def main() -> None:
    await database.connect()

    try:
        # -------------------------------------------------------------------
        # 1. Find deterministic T35 companies.
        # -------------------------------------------------------------------

        company_ids = [
            derive_company_id(index)
            for index in range(COMPANY_COUNT)
        ]

        async with database.pool.acquire() as connection:
            company_rows = await connection.fetch(
                """
                SELECT id, name
                FROM companies
                WHERE id = ANY($1::UUID[])
                ORDER BY id
                """,
                company_ids,
            )

            print("=" * 80)
            print("T36 GROWTHGRAPH LOCAL DEMO")
            print("=" * 80)

            print(
                f"\nSeeded companies found: "
                f"{len(company_rows)} / {len(company_ids)}"
            )

            if len(company_rows) != len(company_ids):
                raise RuntimeError(
                    "Expected all "
                    f"{len(company_ids)} deterministic T35 companies, "
                    f"but found {len(company_rows)}."
                )

            # Do NOT print company names or IDs.
            # The demo output should remain anonymized.

            # ----------------------------------------------------------------
            # 2. Generate local deterministic query embedding.
            # ----------------------------------------------------------------

            query_embedding = deterministic_embedding(
                QUERY
            )

            query_vector = to_vector_literal(
                query_embedding
            )

            print(
                "\nEmbedding provider: "
                "LOCAL / DETERMINISTIC"
            )

            print(
                "AWS / Bedrock: NOT USED"
            )

            print(
                f"Query: {QUERY}"
            )

            # ----------------------------------------------------------------
            # 3. Build the actual cross-company vector query.
            #
            # IMPORTANT:
            #
            # This intentionally uses:
            #
            #     company_id = ANY($1::UUID[])
            #
            # exactly matching the T36 checklist's "company_id IN (...)"
            # restriction, but as a bound parameter instead of a string-
            # interpolated list. company_ids and memory_types are bound
            # via $1/$2; only the vector literal is interpolated, since
            # it needs the ::VECTOR(1024) cast and is generated locally
            # (not user input).
            # ----------------------------------------------------------------

            candidate_limit = max(
                50,
                K * 10,
            )

            sql = f"""
            WITH candidates AS MATERIALIZED
            (
                SELECT
                    id,
                    company_id,
                    content,
                    memory_type,
                    metadata,
                    importance,
                    created_at,
                    1.0 - (
                        embedding <=> '{query_vector}'::VECTOR(
                            {EMBEDDING_DIMENSION}
                        )
                    ) AS similarity
                FROM memories
                WHERE company_id = ANY($1::UUID[])
                  AND memory_type = ANY($2::TEXT[])
                ORDER BY embedding <=> '{query_vector}'::VECTOR(
                    {EMBEDDING_DIMENSION}
                )
                LIMIT {candidate_limit}
            )
            SELECT
                id,
                company_id,
                content,
                memory_type,
                metadata,
                importance,
                similarity,
                created_at
            FROM candidates
            ORDER BY
                GREATEST(similarity, 0.0)
                *
                POWER(
                    0.5::FLOAT8,
                    GREATEST(
                        EXTRACT(
                            EPOCH FROM (now() - created_at)
                        ),
                        0.0
                    )
                    /
                    (30.0 * 86400.0)
                )
                *
                GREATEST(importance, 0.01) DESC,
                similarity DESC,
                created_at DESC,
                id ASC
            LIMIT {K}
            """

            # ----------------------------------------------------------------
            # 4. Execute one cross-company vector query.
            # ----------------------------------------------------------------

            rows = await connection.fetch(
                sql,
                company_ids,
                list(MEMORY_TYPES),
            )

            if not rows:
                raise RuntimeError(
                    "Cross-company vector query returned no results."
                )

            # ----------------------------------------------------------------
            # 5. Verify tenant restriction.
            # ----------------------------------------------------------------

            requested_company_ids = set(
                company_ids
            )

            returned_company_ids = {
                row["company_id"]
                for row in rows
            }

            if not returned_company_ids.issubset(
                requested_company_ids
            ):
                unexpected = (
                    returned_company_ids
                    - requested_company_ids
                )

                raise AssertionError(
                    "Cross-company query returned company IDs "
                    "outside the requested set: "
                    f"{unexpected}"
                )

            # ----------------------------------------------------------------
            # 6. Build anonymized aggregate insight.
            # ----------------------------------------------------------------

            insight = build_aggregate_insight(
                [dict(row) for row in rows]
            )

            # ----------------------------------------------------------------
            # 7. Display ONLY anonymized aggregate information.
            # ----------------------------------------------------------------

            print(
                f"\nCompanies analyzed: "
                f"{len(company_ids)}"
            )

            print(
                f"Candidate memories considered: "
                f"{candidate_limit}"
            )

            print(
                f"Final vector results: "
                f"{len(rows)}"
            )

            print(
                f"Companies represented in results: "
                f"{len(returned_company_ids)}"
            )

            print("\nAggregate insight:")
            print(
                f"  {insight['summary']}"
            )

            print("\nTop themes:")

            if insight["top_themes"]:
                for item in insight["top_themes"]:
                    print(
                        f"  {item['theme'].replace('_', ' ')}: "
                        f"{item['count']} result(s)"
                    )
            else:
                print("  No theme metadata available")

            print("\nTop channels:")

            if insight["top_channels"]:
                for item in insight["top_channels"]:
                    print(
                        f"  {item['channel']}: "
                        f"{item['count']} result(s)"
                    )
            else:
                print("  No channel metadata available")

            print("\nTop messaging angles:")

            if insight["top_messaging_angles"]:
                for item in insight["top_messaging_angles"]:
                    print(
                        f"  {item['angle'].replace('_', ' ')}: "
                        f"{item['count']} result(s)"
                    )
            else:
                print(
                    "  No messaging-angle metadata available"
                )

            # ----------------------------------------------------------------
            # 8. Explicit success checks.
            # ----------------------------------------------------------------

            if len(company_ids) < 2:
                raise AssertionError(
                    "T36 requires multiple companies."
                )

            if not rows:
                raise AssertionError(
                    "Expected at least one vector result."
                )

            if len(rows) > K:
                raise AssertionError(
                    f"Expected at most {K} results, "
                    f"got {len(rows)}."
                )

            if not returned_company_ids:
                raise AssertionError(
                    "No companies were represented in results."
                )

            if not insight["summary"]:
                raise AssertionError(
                    "Aggregate insight is empty."
                )

            if "company_id" in insight["summary"].lower():
                raise AssertionError(
                    "Aggregate insight exposes company-specific data."
                )

            print("\n" + "=" * 80)
            print(
                "SUCCESS: T36 local GrowthGraph demo completed."
            )
            print("=" * 80)

            print("\nChecklist:")
            print("  [x] T35 synthetic data used")
            print("  [x] One cross-company vector query")
            print("  [x] company_id = ANY(...) restriction (bound parameter)")
            print("  [x] Vector similarity ranking")
            print("  [x] Anonymized aggregate insight")
            print("  [x] Working local demo query/output")

            print(
                "\nNOTE: EXPLAIN ANALYZE is verified separately "
                "with scripts\\explain_growthgraph.py."
            )

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())