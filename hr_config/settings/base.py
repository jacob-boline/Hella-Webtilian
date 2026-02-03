# hr_config/settings/base.py

import os

from django.core.management.utils import get_random_secret_key
from django.urls import reverse_lazy

from hr_config.settings.common import BASE_DIR

# TODO - In Docker, it will be safer to move SECRET_KEY to the environment.
#        Otherwise, if the file is recreated below, sessions/tokens = invalid.
ENV_SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
SECRET_FILE = BASE_DIR / ".django_secret"

if ENV_SECRET_KEY:
    SECRET_KEY = ENV_SECRET_KEY
else:
    if SECRET_FILE.exists():
        SECRET_KEY = SECRET_FILE.read_text().strip()
    else:
        SECRET_KEY = get_random_secret_key()
        SECRET_FILE.write_text(SECRET_KEY)
        SECRET_FILE.chmod(0o600)

CSRF_FAILURE_VIEW = "hr_common.utils.htmx_responses.csrf_failure"

DJANGO_CORE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages"
]

STATIC_HANDLING_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles"
]

PROJECT_APPS = [
    "hr_core",
    "hr_about.apps.AboutConfig",
    "hr_access",
    "hr_bulletin.apps.BulletinConfig",
    "hr_common",
    "hr_email",
    "hr_live",
    "hr_payment",
    "hr_shop.apps.ShopConfig",
    "hr_storage"
]

THIRD_PARTY_APPS = [
    "phonenumber_field",
    "imagekit",
    "django_vite",
    "django_rq"
]

INSTALLED_APPS = DJANGO_CORE_APPS + STATIC_HANDLING_APPS + PROJECT_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "hr_core.middleware.request_id.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "hr_common.middleware.logging_context.RequestUserContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "hr_core.middleware.htmx_exception.HtmxExceptionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]

ROOT_URLCONF = "hr_django.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "hr_shop.context_processors.cart_context"
            ]
        }
    }
]

WSGI_APPLICATION = "hr_django.wsgi.application"

AUTHENTICATION_BACKENDS = ["hr_access.auth_backend.CustomBackend"]
AUTH_USER_MODEL = "hr_access.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = reverse_lazy("hr_access:auth_login")
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATIC_SOURCE_ROOT = BASE_DIR / "hr_core" / "static_src" / "images"
STATIC_VARIANTS_ROOT = BASE_DIR / "hr_core" / "static" / "hr_core" / "generated"

REPO_STATIC_ROOT = BASE_DIR / "hr_core" / "static"

STORAGES = {
    "default":     {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
}

STATICFILES_DIRS = [BASE_DIR / "hr_core" / "static"]

# -----------------------------
# RQ (background jobs)
# -----------------------------
RQ_QUEUES = {
    "default": {
        "HOST": os.getenv("REDIS_HOST", "127.0.0.1"),
        "PORT": int(os.getenv("REDIS_PORT", "6379")),
        "DB": 0,
        "DEFAULT_TIMEOUT": 600
    }
}

# -----------------------------
# i18n / tz
# -----------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


from hr_config.settings.logging import *  # noqa
from hr_config.settings.mailjet import *  # noqa
from hr_config.settings.stripe import *  # noqa
from hr_config.settings.vite import *  # noqa
