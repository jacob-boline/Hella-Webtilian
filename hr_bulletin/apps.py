# hr_bulletin/apps.py

from django.apps import AppConfig


class BulletinConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr_bulletin"

    def ready(self):
        import hr_bulletin.signals  # noqa
