from __future__ import annotations

import re
from typing import Any


SENSITIVE_METADATA_KEYS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "session_token",
    "refresh_token",
    "authorization",
    "cookie",
    "private_key",
    "client_secret",
}

SENSITIVE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passwd|pwd)\b"
        r"(?:\s*[:=]\s*|\s+is\s+)\S+"
    ),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
        r"session[_-]?token|refresh[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*\S+"
    ),
    re.compile(
        r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+\S+"
    ),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
)


def contains_sensitive_data(value: str) -> bool:
    """Return True when text contains a recognizable secret."""
    return any(
        pattern.search(value)
        for pattern in SENSITIVE_PATTERNS
    )


def contains_sensitive_metadata(metadata: dict[str, Any]) -> bool:
    """Return True when metadata contains a sensitive key."""
    return any(
        str(key).strip().lower() in SENSITIVE_METADATA_KEYS
        for key in metadata
    )


def is_safe_memory(
    content: str,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Deterministically reject memories containing sensitive data.

    This is a security boundary and does not depend on LLM behavior.
    """
    if contains_sensitive_data(content):
        return False

    if metadata and contains_sensitive_metadata(metadata):
        return False

    return True