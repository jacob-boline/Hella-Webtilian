# hr_config/settings/prod.py


import os  # noqa

from hr_config.settings import postgres as postgres_settings
from hr_config.settings.base import *  # noqa
from hr_config.settings.common import require
from hr_config.settings.mailjet import EMAIL_HOST_PASSWORD, EMAIL_HOST_USER

# ===============================================
#  Environment
# ===============================================
DEBUG = False
USE_S3_MEDIA = os.environ.get("USE_S3_MEDIA", "").lower() in ("true", "1", "yes")


# ===============================================
#  Network
# ===============================================
ALLOWED_HOSTS = ["hellareptilian.com", "www.hellareptilian.com"]  # add LAN hostname/IP for internal access
CSRF_TRUSTED_ORIGINS = ["https://hellareptilian.com"]
SITE_URL = "https://hellareptilian.com"


# ===============================================
#  Reverse Proxy (nginx)
# ===============================================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Enable these after nginx forwards proto correctly (avoid redirect loops)
# SECURE_SSL_REDIRECT = True
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True


# ===============================================
#  Database
# ===============================================
DATABASES = postgres_settings.DATABASES


# ===============================================
#  Guards
# ===============================================
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    raise RuntimeError("Email credentials must be set when DEBUG=False.")

require("DJANGO_SECRET_KEY")

if DEBUG is not False:
    raise RuntimeError("Prod settings must set DEBUG=False")

if USE_S3_MEDIA:
    from hr_storage.conf import *  # noqa

    STORAGES = {
        **STORAGES,
        "default": {"BACKEND": "hr_storage.storage_backends.PublicMediaStorage"},
    }
