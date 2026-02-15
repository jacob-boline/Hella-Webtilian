# hr_config/structlog_config.py

from __future__ import annotations

import os
from typing import cast

import structlog
from structlog.typing import BindableLogger


def _console_enabled() -> bool:
    return os.environ.get("STRUCTLOG_CONSOLE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_structlog_processors() -> list[structlog.types.Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def get_structlog_renderer() -> structlog.types.Processor:
    if _console_enabled():
        return structlog.dev.ConsoleRenderer()
    return structlog.processors.JSONRenderer()


def configure_structlog() -> None:
    if getattr(configure_structlog, "_configured", False):
        return

    structlog.configure(
        processors=[
            *get_structlog_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=cast(type[BindableLogger], structlog.stdlib.BoundLogger),
        cache_logger_on_first_use=True,
    )
    configure_structlog._configured = True
