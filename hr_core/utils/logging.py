from __future__ import annotations

import contextvars
import uuid
from typing import Any, Iterable


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_META_KEY = "HTTP_X_REQUEST_ID"

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

_SENSITIVE_KEY_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "email",
    "phone",
    "address",
    "card",
    "client_secret",
    "stripe",
    "ssn",
)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(request_id: str | None) -> contextvars.Token:
    return _request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    _request_id_var.reset(token)


def generate_request_id() -> str:
    return uuid.uuid4().hex


def redact_payload(
    payload: Any,
    *,
    redacted_value: str = "**redacted**",
    sensitive_key_parts: Iterable[str] = _SENSITIVE_KEY_PARTS,
) -> Any:
    if isinstance(payload, dict):
        return {
            key: redacted_value if _is_sensitive_key(key, sensitive_key_parts) else redact_payload(
                value,
                redacted_value=redacted_value,
                sensitive_key_parts=sensitive_key_parts,
            )
            for key, value in payload.items()
        }

    if isinstance(payload, list):
        return [
            redact_payload(
                item,
                redacted_value=redacted_value,
                sensitive_key_parts=sensitive_key_parts,
            )
            for item in payload
        ]

    if isinstance(payload, tuple):
        return tuple(
            redact_payload(
                item,
                redacted_value=redacted_value,
                sensitive_key_parts=sensitive_key_parts,
            )
            for item in payload
        )

    return payload


def _is_sensitive_key(key: Any, sensitive_key_parts: Iterable[str]) -> bool:
    if not isinstance(key, str):
        return False
    lower_key = key.lower()
    return any(part in lower_key for part in sensitive_key_parts)
