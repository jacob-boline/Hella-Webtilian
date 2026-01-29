# hr_common/utils/unified_logging.py


"""
Request-id + payload redaction utilities for unified logging.

Provides:
- A request_id contextvar that is bound into structlog contextvars
- Generation and propagation of request IDs (X-Request-ID)
- A logging.Filter that injects request_id into standard logging records
- Recursive payload redaction helpers to prevent sensitive data leaks in logs

Design goals:
- Every log line in a request should carry a request_id
- Logs should be safe by default (redact common sensitive fields)
- Works with both standard logging and structlog
"""

from __future__ import annotations

import contextvars
import hashlib
import logging
import uuid
from collections.abc import Iterable
from typing import Any

import structlog
from structlog.contextvars import bind_contextvars, unbind_contextvars

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_META_KEY = "HTTP_X_REQUEST_ID"

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

_user_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar("user_id", default=None)

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


def _safe_email(value: Any) -> Any:
    if not isinstance(value, str):
        return "**redacted**"
    v = value.strip().lower()
    if "@" not in v:
        return "**redacted**"
    domain = v.rsplit("@", 1)[-1]
    fp = hashlib.sha256(v.encode("utf-8")).hexdigest()[:12]
    return f"**redacted** ({domain}, fp={fp}"


def get_user_id() -> int | None:
    return _user_id_var.get()


def set_user_id(user_id: int | None) -> contextvars.Token:
    token = _user_id_var.set(user_id)
    if user_id is not None:
        bind_contextvars(user_id=user_id)
    else:
        unbind_contextvars("user_id")
    return token


def reset_user_id(token: contextvars.Token) -> None:
    _user_id_var.reset(token)
    unbind_contextvars("user_id")


def log_event(logger: logging.Logger, level: int, event: str, *, exc_info: bool = False, **data: Any) -> None:
    payload = redact_payload(data)
    struct_logger = structlog.get_logger(logger.name)
    struct_logger.log(level, event, **payload, exc_info=exc_info)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(request_id: str | None) -> contextvars.Token:
    token = _request_id_var.set(request_id)
    if request_id is not None:
        bind_contextvars(request_id=request_id)
    else:
        unbind_contextvars("request_id")
    return token


def reset_request_id(token: contextvars.Token) -> None:
    _request_id_var.reset(token)
    unbind_contextvars("request_id")


def generate_request_id() -> str:
    return uuid.uuid4().hex


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.user_id = get_user_id()
        return True


def redact_payload(
    payload: Any,
    *,
    redacted_value: str = "**redacted**",
    sensitive_key_parts: Iterable[str] = _SENSITIVE_KEY_PARTS,
) -> Any:
    if isinstance(payload, dict):
        out = {}
        for key, value in payload.items():
            if _is_sensitive_key(key, sensitive_key_parts):
                # special-case email to keep a tiny bit of signal
                if isinstance(key, str) and "email" in key.lower():
                    out[key] = _safe_email(value)
                else:
                    out[key] = redacted_value
            else:
                out[key] = redact_payload(
                    value,
                    redacted_value=redacted_value,
                    sensitive_key_parts=sensitive_key_parts,
                )
        return out

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
