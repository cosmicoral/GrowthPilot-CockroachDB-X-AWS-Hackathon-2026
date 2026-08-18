"""Attach login credentials to the seeded demo company.

`seed_demo_founder.py` creates the FlowForge AI company with a fixed UUID
but no email or password_hash, because it writes directly through the
memory layer rather than going through the signup route. That makes the
seeded narrative unreachable from the UI: there is no account to log in
as, so the Memory Inspector, chat and content pages have nothing to show.

The alternative would be to sign up through the frontend and then migrate
the seeded memories to the new company_id, but that means an UPDATE across
the `memories` table -- and company_id is the vector index prefix column,
so every moved row's index entry moves with it. Setting credentials on the
company that already owns the data is the smaller, safer change, and it
keeps `run_analytics_reflection.py` working unmodified since that imports
COMPANY_ID from the seed script.

Reuses the application's own hash_password() so the stored hash is exactly
what the login route expects -- never reimplement the hashing scheme in a
helper script, or you get a row that looks right and silently fails to
authenticate.

Usage (password is prompted, never passed on the command line, so it stays
out of shell history):

    python scripts/set_demo_credentials.py demo@growthpilot.dev
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.api.auth import hash_password  # noqa: E402
from backend.database.database import (  # noqa: E402
    database,
    fetch_one,
    fetch_value,
)
from scripts.seed_demo_founder import COMPANY_ID  # noqa: E402

UPDATE_SQL = """
UPDATE companies
SET email = $2, password_hash = $3
WHERE id = $1
RETURNING id, name, email
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set login credentials on the seeded demo company."
    )
    parser.add_argument(
        "email",
        help="Login email for the demo account.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    password = getpass.getpass("Demo password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Use at least 8 characters.")
        return

    await database.connect()

    try:
        async with database.pool.acquire() as connection:
            row = await fetch_one(
                connection,
                UPDATE_SQL,
                COMPANY_ID,
                args.email,
                hash_password(password),
            )

        if row is None:
            print(
                f"No company with id {COMPANY_ID}. "
                f"Run scripts/seed_demo_founder.py first."
            )
            return

        memory_count = None
        async with database.pool.acquire() as connection:
            memory_count = await fetch_value(
                connection,
                "SELECT count(*) FROM memories WHERE company_id = $1",
                COMPANY_ID,
            )

        print("Demo credentials set.")
        print(f"  Company : {row['name']} ({row['id']})")
        print(f"  Email   : {row['email']}")
        print(f"  Memories visible after login: {memory_count}")

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
