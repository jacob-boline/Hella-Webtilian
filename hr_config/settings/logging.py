# hr_config/settings/logging.py


import os
from pathlib import Path

from hr_config.settings.common import BASE_DIR
from hr_config.structlog_config import get_structlog_processors, get_structlog_renderer

LOG_DIR = Path(os.environ.get("LOG_DIR", BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", LOG_LEVEL).upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"structlog": {"()": "structlog.stdlib.ProcessorFormatter", "processor": get_structlog_renderer(), "foreign_pre_chain": get_structlog_processors()}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "structlog", "level": LOG_LEVEL},
        "file": {
            "class": "concurrent_log_handler.ConcurrentTimedRotatingFileHandler",
            "formatter": "structlog",
            "filename": str(LOG_DIR / "django.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8",
            "utc": True,
            "delay": True,
            "level": LOG_LEVEL,
        },
        "error_file": {
            "class": "concurrent_log_handler.ConcurrentTimedRotatingFileHandler",
            "formatter": "structlog",
            "filename": str(LOG_DIR / "django-error.log"),
            "when": "midnight",
            "backupCount": 30,
            "encoding": "utf-8",
            "utc": True,
            "delay": True,
            "level": "ERROR",
        },
    },
    # Root is the "meta/all log" funnel.
    # ERROR+ will automatically also go to error_file because that handler is level-gated.
    "root": {"handlers": ["console", "file", "error_file"], "level": LOG_LEVEL},
    # Keep only special cases here; everything else can propagate to root.
    "loggers": {
        # Let Django logs flow to root; tighten/loosen with DJANGO_LOG_LEVEL.
        "django": {"level": DJANGO_LOG_LEVEL, "propagate": True},
        # Requests are noisy at INFO; keep them as errors.
        "django.request": {"level": "ERROR", "propagate": True},
        # SQL logging toggle: LOG_SQL=1 in hr_config.settins.dev
        "django.db.backends": {"level": "WARNING", "propagate": True},
    },
}
