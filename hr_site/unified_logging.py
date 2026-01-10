from __future__ import annotations

import logging
from typing import Any

import structlog

from hr_core.utils.logging import redact_payload


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    exc_info: bool = False,
    **data: Any,
) -> None:
    payload = redact_payload(data)
    struct_logger = structlog.stdlib.wrap_logger(logger)
    struct_logger.log(level, event, **payload, exc_info=exc_info)
