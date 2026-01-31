# hr_config/settings/dev.py

import os  # noqa

from dotenv import load_dotenv

from hr_config.settings import sqlite as sqlite_settings
from hr_config.settings.common import BASE_DIR, env_bool  # noqa

# ===============================================
#  Environment
# ===============================================
load_dotenv(BASE_DIR / "hr_config" / "env" / "dev.env", override=False)

DEBUG = True
DEBUG_TOKENS = True

from hr_config.settings.base import *  # noqa

# ===============================================
#  Database
# ===============================================
DATABASES = sqlite_settings.DATABASES


# ===============================================
#  Network
# ===============================================
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]

INTERNAL_IPS = ["127.0.0.1"]

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


# ===============================================
#  Apps + Middleware
# ===============================================
INSTALLED_APPS += ["debug_toolbar", "django_browser_reload"]

MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")
MIDDLEWARE.append('hr_core.middleware.media_cache.MediaCacheMiddleware')

WHITENOISE_USE_FINDERS = True


# ===============================================
#  Debug Toolbar
# ===============================================
DEBUG_TOOLBAR_CONFIG = {"DISABLE_PANELS": ["debug_toolbar.panels.staticfiles.StaticFilesPanel"]}

# ===============================================
#  Ngrok
# ===============================================
USE_NGROK = env_bool("USE_NGROK")

if USE_NGROK:
    EXTERNAL_BASE_URL = os.getenv("EXTERNAL_BASE_URL", "").rstrip("/")
    if not EXTERNAL_BASE_URL:
        raise RuntimeError("USE_NGROK=1 but EXTERNAL_BASE_URL is empty.")
    if not (EXTERNAL_BASE_URL.startswith("http://") or EXTERNAL_BASE_URL.startswith("https://")):
        raise RuntimeError("EXTERNAL_BASE_URL must start with http:// or https://")


# ===============================================
#  Logging
# ===============================================
LOG_SQL = env_bool("LOG_SQL", False)
if LOG_SQL:
    LOGGING["loggers"]["django.db.backends"] = {"level": "DEBUG", "propagate": True}
    for h in ("console", "file"):
        if h in LOGGING["handlers"]:
            LOGGING["handlers"][h]["level"] = "DEBUG"
