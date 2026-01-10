# hr_core/apps.py
from django.apps import AppConfig

from hr_core.utils.structlog_config import configure_structlog


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr_core"

    def ready(self) -> None:
        configure_structlog()
