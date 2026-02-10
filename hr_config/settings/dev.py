# hr_config/settings/dev.py

import os  # noqa

from dotenv import load_dotenv

from hr_config.settings import sqlite as sqlite_settings
from hr_config.settings.common import BASE_DIR, env_bool  # noqa

IN_DOCKER = env_bool('IN_DOCKER', default=False)

# ===============================================
#  Environment
# ===============================================
if not IN_DOCKER:
    load_dotenv(BASE_DIR / "hr_config" / "env" / "dev.env", override=False)

from hr_config.settings.base import *  # noqa
from hr_config.django_vite_patch import patch_django_vite_dev_url


DEBUG = env_bool('DEBUG', True)
DEBUG_TOKENS = True

if EMAIL_PROVIDER == 'mailjet':
    if not MAILJET_API_KEY or not MAILJET_API_SECRET:
        raise RuntimeError(
            'Mailjet selected but MAILJET_API_KEY / MAILJET_API_SECRET are not set'
        )

patch_django_vite_dev_url()

# ===============================================
#  Database
# ===============================================
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    # Use dj-database-url if installed; otherwise parse manually.
    import dj_database_url  # type: ignore

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=60)}
else:
    DATABASES = sqlite_settings.DATABASES


ENABLE_MEDIA_JOBS = True

# --- Static files (dev) ---
# Manifest storage is strict and will fail if built assets reference missing files.
# In dev we prefer speed + resilience; prod will keep CompressedManifestStaticFilesStorage.
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}


# ===============================================
#  Network
# ===============================================
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",") if h.strip()]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", True)
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)

INTERNAL_IPS = ["127.0.0.1"]

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")


# ===============================================
#  Apps + Middleware
# ===============================================
INSTALLED_APPS += ["debug_toolbar", "django_browser_reload", "django_rq"]

MIDDLEWARE.insert(2, "debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")
MIDDLEWARE.append('hr_core.middleware.media_cache.MediaCacheMiddleware')


TEMPLATES[0]["OPTIONS"]["context_processors"].append('hr_common.context_processors.template_flags')

WHITENOISE_USE_FINDERS = True


# ===============================================
#  Debug Toolbar
# ===============================================
DEBUG_TOOLBAR_CONFIG = {"DISABLE_PANELS": ["debug_toolbar.panels.staticfiles.StaticFilesPanel"]}



EXTERNAL_BASE_URL = os.getenv('EXTERNAL_BASE_URL', 'localhost:8080').rstrip('/')
# ===============================================
#  Ngrok
# ===============================================
USE_NGROK = env_bool("USE_NGROK", False)

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

FILE_UPLOAD_PERMISSIONS = None
FILE_UPLOAD_DIRECTORY_PERMISSIONS = None
