# hr_config/settings/prod_docker.py

from hr_config.settings import postgres as postgres_settings
from hr_config.settings.base import *  # noqa
from hr_config.settings.common import require


# ===============================================
#  Environment
# ===============================================
DEBUG = False
USE_S3_MEDIA = os.environ.get("USE_S3_MEDIA", "").lower() in ("true", "1", "yes")

if DEBUG:
    raise RuntimeError("Production settings must have DEBUG=False")


# ===============================================
#  Network
# ===============================================
# Read from environment for Docker deployment
# allowed_hosts_str = os.environ.get("ALLOWED_HOSTS", "hellareptilian.com,www.hellareptilian.com")
# ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_str.split(",") if h.strip()]
# ALLOWED_HOSTS += ['172.19.2.178', '127.0.0.1', '0.0.0.0', '[::]']
ALLOWED_HOSTS = ['*']

csrf_origins_str = os.environ.get("CSRF_TRUSTED_ORIGINS", "https://hellareptilian.com")
CSRF_TRUSTED_ORIGINS = [h.strip() for h in csrf_origins_str.split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS += ['http://172.19.2.178', 'http://localhost','http://127.0.0.1']

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
#  Redis / RQ Configuration (Optional)
# ===============================================
# Only configure RQ if Redis is available
# This allows the app to run without Redis for initial deployment
REDIS_URL = os.environ.get("REDIS_URL")
REDIS_HOST = os.environ.get("REDIS_HOST")

if REDIS_URL or REDIS_HOST:
    # Redis is available - configure RQ
    if REDIS_HOST:
        REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
        RQ_QUEUES = {
            "default": {
                "HOST": REDIS_HOST,
                "PORT": REDIS_PORT,
                "DB": 0,
                "DEFAULT_TIMEOUT": 600
            }
        }
    elif REDIS_URL:
        # Parse REDIS_URL if using Fly.io's Upstash Redis
        # Format: redis://user:pass@host:port/db
        from urllib.parse import urlparse
        parsed = urlparse(REDIS_URL)
        RQ_QUEUES = {
            "default": {
                "HOST": parsed.hostname,
                "PORT": parsed.port or 6379,
                "DB": int(parsed.path.lstrip('/')) if parsed.path else 0,
                "PASSWORD": parsed.password,
                "DEFAULT_TIMEOUT": 600
            }
        }
else:
    # Redis not available - disable RQ
    print("⚠️  Redis not configured - RQ worker functionality disabled")
    # RQ_QUEUES = {}
    # Remove django_rq from INSTALLED_APPS if it's there
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_rq"]


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
