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
import logging
import uuid
from typing import Any, Iterable

import structlog
from structlog.contextvars import bind_contextvars, unbind_contextvars


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


def log_event(logger: logging.Logger, level: int, event: str, *, exc_info: bool = False, **data: Any,) -> None:
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


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


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
