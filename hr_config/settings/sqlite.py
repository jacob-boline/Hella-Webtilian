# hr_config/settings/sqlite.py


from hr_config.settings.common import BASE_DIR

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
