# hr_access/apps.py

from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr_access'

    def ready(self):
        import hr_access.signals  # noqa
