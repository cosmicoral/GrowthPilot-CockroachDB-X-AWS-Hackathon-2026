from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID, uuid5

import httpx
from httpx import ASGITransport

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.api.auth import create_session_token
from backend.database.database import database
from backend.main import app

SEED_NAMESPACE = UUID(
    "f2f5f2a0-6b8b-4b8e-9f4b-9d3f6b1c2e40"
)


def derive_company_id(index: int) -> UUID:
    return uuid5(
        SEED_NAMESPACE,
        f"growthgraph-synthetic-founder-{index}",
    )


async def main() -> None:
    await database.connect()

    try:
        # ------------------------------------------------------------
        # 1. Find the deterministic GrowthGraph seed companies.
        # ------------------------------------------------------------
        company_ids = [
            derive_company_id(i)
            for i in range(10)
        ]

        async with database.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name
                FROM companies
                WHERE id = ANY($1::UUID[])
                ORDER BY id
                """,
                company_ids,
            )

        print(
            f"Seeded companies found: "
            f"{len(rows)} / {len(company_ids)}"
        )

        if len(rows) < 2:
            raise RuntimeError(
                "Need at least two seeded GrowthGraph companies "
                "for a real cross-company test."
            )

        found_ids = [row["id"] for row in rows]

        print("\nCompanies:")
        for row in rows:
            print(
                f"  {row['id']}  {row['name']}"
            )

        # ------------------------------------------------------------
        # 2. Use the first seeded company as the authenticated caller.
        # ------------------------------------------------------------
        authenticated_company_id = found_ids[0]

        # IMPORTANT:
        # Use the real application session creation function.
        # This stores SHA-256(token) in sessions.token_hash,
        # which matches backend.api.deps.get_current_company_id().
        token, expires_at = await create_session_token(
            authenticated_company_id
        )

        print(
            "\nAuthenticated company:",
            authenticated_company_id,
        )

        print(
            "Session created successfully; "
            f"expires at {expires_at.isoformat()}"
        )

        # ------------------------------------------------------------
        # 3. Build the real GrowthGraph request.
        # ------------------------------------------------------------
        payload = {
            "query": (
                "What content and messaging approaches "
                "have performed well?"
            ),
            "company_ids": [
                str(company_id)
                for company_id in found_ids
            ],
            "k": 10,
            "types": [
                "reflection",
                "episodic",
            ],
        }

        print("\nPOST /api/growthgraph/insights")

        print("\nRequest:")
        print(payload)

        # ------------------------------------------------------------
        # 4. Call the real FastAPI application.
        #
        # ASGITransport is used instead of TestClient because this
        # script is already running inside asyncio. This avoids the
        # cross-event-loop shutdown problem you hit earlier.
        # ------------------------------------------------------------
        transport = ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://growthpilot.test",
        ) as client:
            response = await client.post(
                "/api/growthgraph/insights",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

        # ------------------------------------------------------------
        # 5. Display the actual result.
        # ------------------------------------------------------------
        print("\nHTTP status:", response.status_code)

        print("\nResponse:")

        try:
            print(response.json())
        except ValueError:
            print(response.text)

        # ------------------------------------------------------------
        # 6. Validate the GrowthGraph response.
        # ------------------------------------------------------------
        if response.status_code != 200:
            raise RuntimeError(
                "GrowthGraph request failed: "
                f"{response.status_code} {response.text}"
            )

        data = response.json()

        if data.get("company_count") != len(found_ids):
            raise AssertionError(
                "Unexpected company_count: "
                f"expected {len(found_ids)}, "
                f"got {data.get('company_count')}"
            )

        if not data.get("results"):
            raise AssertionError(
                "GrowthGraph returned no results."
            )

        print(
            "\nSUCCESS: received "
            f"{len(data['results'])} "
            "cross-company insights."
        )

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())