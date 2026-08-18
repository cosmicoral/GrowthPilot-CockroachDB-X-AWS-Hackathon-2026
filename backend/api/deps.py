from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status

from backend.api.auth import get_presented_session_token, hash_session_token
from backend.database.database import database, fetch_one


async def get_current_company_id(request: Request) -> UUID:
    """Validate the opaque session token and return its company."""
    token = get_presented_session_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
        )

    # Reject unreasonable values before hashing/querying while avoiding a
    # format-specific token parser that would reduce future flexibility.
    if len(token) < 32 or len(token) > 512:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    token_hash = hash_session_token(token)
    query = """
    SELECT company_id, expires_at
    FROM sessions
    WHERE token_hash = $1;
    """

    async with database.acquire() as conn:
        row = await fetch_one(conn, query, token_hash)

        if row and row["expires_at"] <= datetime.now(timezone.utc):
            await conn.execute(
                "DELETE FROM sessions WHERE token_hash = $1;",
                token_hash,
            )
            row = None

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or has expired",
        )

    return row["company_id"]
