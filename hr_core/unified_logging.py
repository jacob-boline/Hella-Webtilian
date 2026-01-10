from __future__ import annotations

import logging
from typing import Any

from hr_core.utils.logging import get_request_id, redact_payload

hr_common_logger = logging.getLogger(__name__)


def log_event(
    logger: hr_common_logger,
    level: int,
    event: str,
    *,
    exc_info: bool = False,
    **data: Any,
) -> None:
    request_id = get_request_id()
    payload = redact_payload(data)
    logger.log(
        level,
        "event=%s request_id=%s data=%s",
        event,
        request_id,
        payload,
        exc_info=exc_info,
    )
