import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from backend.api.auth import (
    LEGACY_PASSWORD_ITERATIONS,
    PASSWORD_ITERATIONS,
    generate_session_token,
    hash_password,
    hash_session_token,
    password_needs_rehash,
    verify_password,
)
from backend.api.auth import (
    router as auth_router,
)
from backend.api.deps import get_current_company_id
from backend.auth_config import AuthSettings, get_auth_settings

app = FastAPI()
app.include_router(auth_router)


@app.get("/test-protected")
async def protected_route(company_id=Depends(get_current_company_id)):
    return {"company_id": str(company_id)}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_auth_settings_cache():
    """Keep environment changes isolated between authentication tests."""
    get_auth_settings.cache_clear()
    yield
    get_auth_settings.cache_clear()


def configure_mock_database(mock_db):
    conn = AsyncMock()

    acquire_context = MagicMock()
    acquire_context.__aenter__ = AsyncMock(return_value=conn)
    acquire_context.__aexit__ = AsyncMock(return_value=None)
    mock_db.acquire.return_value = acquire_context

    transaction_context = MagicMock()
    transaction_context.__aenter__ = AsyncMock(return_value=None)
    transaction_context.__aexit__ = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=transaction_context)
    return conn


def make_legacy_password_hash(password: str) -> str:
    salt = b"0123456789abcdef"
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        LEGACY_PASSWORD_ITERATIONS,
    )
    return f"{salt.hex()}${pwd_hash.hex()}"


def test_password_hashing_and_verification():
    raw_password = "secure_password_123"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith(f"pbkdf2_sha256${PASSWORD_ITERATIONS}$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    assert password_needs_rehash(hashed) is False


def test_legacy_password_hash_is_accepted_and_marked_for_upgrade():
    raw_password = "legacy_password_123"
    hashed = make_legacy_password_hash(raw_password)

    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    assert password_needs_rehash(hashed) is True


def test_session_token_is_random_and_only_its_hash_is_stable():
    first = generate_session_token()
    second = generate_session_token()

    assert first != second
    assert len(first) >= 32
    assert hash_session_token(first) == hash_session_token(first)
    assert hash_session_token(first) != first


def test_session_cookie_is_secure_by_default(monkeypatch):
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
    settings = AuthSettings(_env_file=None)

    assert settings.session_cookie_secure is True


def test_signup_rejects_blank_company_name(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "   ",
            "email": "info@acme.com",
            "password": "supersecurepassword",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "must not be blank" in response.json()["detail"][0]["msg"].lower()


@patch("backend.api.deps.database")
def test_dependency_token_valid(mock_db, client):
    company_uuid = uuid4()
    session_token = generate_session_token()
    conn = configure_mock_database(mock_db)
    conn.fetchrow.return_value = {
        "company_id": company_uuid,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
    }

    response = client.get(
        "/test-protected",
        headers={"Authorization": f"Bearer {session_token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"company_id": str(company_uuid)}
    query, token_hash = conn.fetchrow.await_args.args
    assert "WHERE token_hash = $1" in query
    assert token_hash == hash_session_token(session_token)


@patch("backend.api.deps.database")
def test_dependency_token_expired_is_deleted(mock_db, client):
    session_token = generate_session_token()
    conn = configure_mock_database(mock_db)
    expired_row = {
        "company_id": uuid4(),
        "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
    }
    events = []

    async def fetch_expired_session(*args):
        events.append("fetch")
        return expired_row

    async def delete_expired_session(*args):
        events.append("delete")

    async def release_connection(*args):
        events.append("release")

    conn.fetchrow.side_effect = fetch_expired_session
    conn.execute.side_effect = delete_expired_session
    mock_db.acquire.return_value.__aexit__.side_effect = release_connection

    response = client.get(
        "/test-protected",
        headers={"Authorization": f"Bearer {session_token}"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()
    conn.execute.assert_awaited_once()
    assert conn.execute.await_args.args[1] == hash_session_token(session_token)
    assert events == ["fetch", "delete", "release"]


@patch("backend.api.deps.database")
def test_dependency_token_missing(mock_db, client):
    response = client.get("/test-protected")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "missing" in response.json()["detail"].lower()
    mock_db.acquire.assert_not_called()


@patch("backend.api.auth.database")
def test_signup_creates_hashed_session_cookie(mock_db, client, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    company_uuid = uuid4()
    conn = configure_mock_database(mock_db)
    conn.fetchval.return_value = company_uuid

    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Acme Inc",
            "email": "INFO@ACME.COM",
            "password": "supersecurepassword",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"company_id": str(company_uuid)}
    assert "session_token" not in response.json()
    assert response.cookies.get("session_token")
    assert response.headers["cache-control"] == "no-store"

    company_insert = conn.fetchval.await_args
    assert company_insert.args[2] == "info@acme.com"

    session_insert = next(
        call for call in conn.execute.await_args_list if "INSERT INTO sessions" in call.args[0]
    )
    stored_token_hash = session_insert.args[1]
    cookie_token = response.cookies["session_token"]
    assert stored_token_hash == hash_session_token(cookie_token)
    assert cookie_token not in session_insert.args

    set_cookie = response.headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Secure" not in set_cookie


@patch("backend.api.auth._set_session_cookie")
@patch("backend.api.auth.database")
def test_signup_does_not_set_cookie_when_transaction_rolls_back(
    mock_db,
    mock_set_cookie,
    client,
):
    company_uuid = uuid4()
    conn = configure_mock_database(mock_db)
    conn.fetchval.return_value = company_uuid
    transaction_context = conn.transaction.return_value
    transaction_context.__aexit__.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        client.post(
            "/api/auth/signup",
            json={
                "name": "Acme Inc",
                "email": "info@acme.com",
                "password": "supersecurepassword",
            },
        )

    mock_set_cookie.assert_not_called()


@patch("backend.api.auth.database")
def test_login_creates_session_without_returning_token(mock_db, client, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    company_uuid = uuid4()
    password = "securepassword"
    conn = configure_mock_database(mock_db)
    conn.fetchrow.return_value = {
        "id": company_uuid,
        "password_hash": hash_password(password),
    }

    response = client.post(
        "/api/auth/login",
        json={"email": "USER@ACME.COM", "password": password},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"company_id": str(company_uuid)}
    assert response.cookies.get("session_token")
    assert conn.fetchrow.await_args.args[1] == "user@acme.com"
    assert any("INSERT INTO sessions" in call.args[0] for call in conn.execute.await_args_list)


@patch("backend.api.auth.database")
def test_login_upgrades_legacy_password_hash(mock_db, client, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    company_uuid = uuid4()
    password = "legacy-password"
    conn = configure_mock_database(mock_db)
    conn.fetchrow.return_value = {
        "id": company_uuid,
        "password_hash": make_legacy_password_hash(password),
    }

    response = client.post(
        "/api/auth/login",
        json={"email": "legacy@acme.com", "password": password},
    )

    assert response.status_code == status.HTTP_200_OK
    password_update = next(
        call
        for call in conn.execute.await_args_list
        if "UPDATE companies SET password_hash" in call.args[0]
    )
    assert password_update.args[1].startswith(f"pbkdf2_sha256${PASSWORD_ITERATIONS}$")
    assert password_update.args[2] == company_uuid


@patch("backend.api.auth.database")
def test_logout_deletes_server_session_and_cookie(mock_db, client, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    session_token = generate_session_token()
    conn = configure_mock_database(mock_db)
    client.cookies.set("session_token", session_token)

    response = client.post("/api/auth/logout")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    query, stored_token_hash = conn.execute.await_args.args
    assert "DELETE FROM sessions" in query
    assert stored_token_hash == hash_session_token(session_token)
    assert response.headers["cache-control"] == "no-store"
    assert "session_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
