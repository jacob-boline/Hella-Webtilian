# hr_config/settings/prod_docker.py

from hr_config.settings import postgres as postgres_settings
from hr_config.settings.base import *  # noqa
from hr_config.settings.common import require


# ===============================================
#  Environment
# ===============================================
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
USE_S3_MEDIA = os.environ.get("USE_S3_MEDIA", "").lower() in ("true", "1", "yes")

if DEBUG:
    raise RuntimeError("Production settings must have DEBUG=False")


# ===============================================
#  Network
# ===============================================
# Read from environment for Docker deployment
allowed_hosts_str = os.environ.get("ALLOWED_HOSTS", "hellareptilian.com,www.hellareptilian.com")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(",") if h.strip()]

csrf_origins_str = os.environ.get("CSRF_TRUSTED_ORIGINS", "https://hellareptilian.com")
CSRF_TRUSTED_ORIGINS = [h.strip() for h in csrf_origins_str.split(",") if h.strip()]

SITE_URL = os.environ.get("SITE_URL", "https://hellareptilian.com")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


# ===============================================
#  Database
# ===============================================
DATABASES = postgres_settings.DATABASES


# ===============================================
#  Redis / RQ Configuration
# ===============================================
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": 0,
        "DEFAULT_TIMEOUT": 600
    }
}


# ===============================================
#  Guards
# ===============================================
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    raise RuntimeError("Email credentials must be set when DEBUG=False.")

require("DJANGO_SECRET_KEY")

if USE_S3_MEDIA:
    from hr_storage.conf import *  # noqa

    STORAGES = {
        **STORAGES,
        "default": {"BACKEND": "hr_storage.storage_backends.PublicMediaStorage"}
    }
