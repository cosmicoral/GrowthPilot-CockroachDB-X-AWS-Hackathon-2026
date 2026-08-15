from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import asyncpg
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.auth_config import get_auth_settings
from backend.database.database import database

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SESSION_COOKIE_NAME = "session_token"
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
LEGACY_PASSWORD_ITERATIONS = 100_000


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    website: str | None = None
    industry: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Company name must not be blank")
        return stripped


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class SessionResponse(BaseModel):
    company_id: UUID


def _normalise_email(email: EmailStr | str) -> str:
    return str(email).strip().lower()


def hash_password(password: str, *, iterations: int = PASSWORD_ITERATIONS) -> str:
    """Hash a password using versioned PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"{PASSWORD_ALGORITHM}${iterations}${salt.hex()}${pwd_hash.hex()}"


def _password_hash_parts(stored_hash: str) -> tuple[int, bytes, bytes]:
    parts = stored_hash.split("$")

    if len(parts) == 4 and parts[0] == PASSWORD_ALGORITHM:
        iterations = int(parts[1])
        salt_hex, hash_hex = parts[2], parts[3]
    elif len(parts) == 2:
        # Compatibility with hashes created before password parameters were
        # stored in the encoded value. They are upgraded after a valid login.
        iterations = LEGACY_PASSWORD_ITERATIONS
        salt_hex, hash_hex = parts
    else:
        raise ValueError("Unsupported password hash format")

    if iterations <= 0:
        raise ValueError("Invalid password iteration count")
    return iterations, bytes.fromhex(salt_hex), bytes.fromhex(hash_hex)


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Verify both current and legacy password hashes in constant time."""
    if not stored_hash:
        return False

    try:
        iterations, salt, expected_hash = _password_hash_parts(stored_hash)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False


def password_needs_rehash(stored_hash: str | None) -> bool:
    if not stored_hash:
        return True
    try:
        iterations, _, _ = _password_hash_parts(stored_hash)
    except (ValueError, TypeError):
        return True
    return not stored_hash.startswith(f"{PASSWORD_ALGORITHM}$") or (
        iterations < PASSWORD_ITERATIONS
    )


# Keep missing-account logins on the same expensive verification path as real
# accounts so response timing does not reveal whether an email is registered.
DUMMY_PASSWORD_HASH = hash_password("growthpilot-dummy-password")


def generate_session_token() -> str:
    """Return a URL-safe token with 256 bits of cryptographic randomness."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Return the one-way value stored in the sessions table."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_presented_session_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        scheme, _, credentials = auth_header.partition(" ")
        if scheme.lower() == "bearer" and credentials.strip():
            return credentials.strip()
    return request.cookies.get(SESSION_COOKIE_NAME)


def _set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    settings = get_auth_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
        max_age=settings.session_ttl_seconds,
        expires=expires_at,
    )
    response.headers["Cache-Control"] = "no-store"


async def create_session_token(
    company_id: UUID,
    response: Response,
    *,
    connection: asyncpg.Connection | None = None,
) -> str:
    """Create a server-side session and expose only its opaque token cookie."""
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=get_auth_settings().session_ttl_seconds
    )
    query = """
    INSERT INTO sessions (token_hash, company_id, expires_at)
    VALUES ($1, $2, $3);
    """

    if connection is None:
        async with database.acquire() as conn:
            await conn.execute(query, hash_session_token(token), company_id, expires_at)
    else:
        await connection.execute(query, hash_session_token(token), company_id, expires_at)

    _set_session_cookie(response, token, expires_at)
    return token


@router.post(
    "/signup",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(request: SignupRequest, response: Response) -> SessionResponse:
    """Create a company account and its first session atomically."""
    email = _normalise_email(request.email)
    password_hash = await asyncio.to_thread(hash_password, request.password)
    insert_query = """
    INSERT INTO companies (name, email, password_hash, website, industry, description)
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id;
    """

    try:
        async with database.acquire() as conn:
            async with conn.transaction():
                company_id = await conn.fetchval(
                    insert_query,
                    request.name,
                    email,
                    password_hash,
                    request.website,
                    request.industry,
                    request.description,
                )
                await create_session_token(company_id, response, connection=conn)
    except asyncpg.UniqueViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc

    return SessionResponse(company_id=company_id)


@router.post("/login", response_model=SessionResponse)
async def login(request: LoginRequest, response: Response) -> SessionResponse:
    """Authenticate credentials, upgrade legacy hashes, and start a session."""
    email = _normalise_email(request.email)
    query = "SELECT id, password_hash FROM companies WHERE email = $1;"
    async with database.acquire() as conn:
        row = await conn.fetchrow(query, email)

    stored_hash = row["password_hash"] if row and row["password_hash"] else DUMMY_PASSWORD_HASH
    is_valid = await asyncio.to_thread(verify_password, request.password, stored_hash)
    if not row or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    company_id = row["id"]
    replacement_hash = None
    if password_needs_rehash(stored_hash):
        replacement_hash = await asyncio.to_thread(hash_password, request.password)

    async with database.acquire() as conn:
        async with conn.transaction():
            if replacement_hash is not None:
                await conn.execute(
                    "UPDATE companies SET password_hash = $1 WHERE id = $2;",
                    replacement_hash,
                    company_id,
                )
            await create_session_token(company_id, response, connection=conn)

    return SessionResponse(company_id=company_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    """Invalidate the presented session server-side and clear its cookie."""
    token = get_presented_session_token(request)
    if token:
        async with database.acquire() as conn:
            await conn.execute(
                "DELETE FROM sessions WHERE token_hash = $1;",
                hash_session_token(token),
            )

    settings = get_auth_settings()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )
    response.headers["Cache-Control"] = "no-store"
