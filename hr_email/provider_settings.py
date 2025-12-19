"""
Helpers for deriving SMTP settings from the environment.

Originally designed for multiple providers.
"""

import os
from typing import Dict, Iterable, Optional
from django.conf import settings

# load_dotenv()
#
# DEFAULT_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# DEFAULT_SENDER = os.environ.get('DEFAULT_FROM_EMAIL')
# EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER')
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# DEBUG = os.environ.get('DEBUG').strip().lower() in {'1', 'true', 'yes', 'on'}
#
# if not DEBUG:
#     if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
#         raise RuntimeError('Email credentials must be set in production.')

PROVIDER_DEFAULTS: Dict[str, Dict[str, object]] = {
    "mailjet": {
        "backend": "django.core.mail.backends.smtp.EmailBackend",
        "host": "in-v3.mailjet.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "user": settings.EMAIL_HOST_USER,
        "password": settings.EMAIL_HOST_PASSWORD,
        "from_email": settings.DEFAULT_FROM_EMAIL,
    }
}

AVAILABLE_PROVIDERS = tuple(PROVIDER_DEFAULTS.keys())


def _first_env(keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_provider(provider_override: Optional[str] = None) -> str:
    provider = (provider_override or os.environ.get("EMAIL_PROVIDER") or "mailjet").strip().lower()
    return provider if provider in PROVIDER_DEFAULTS else "mailjet"


def get_email_config():
    return {
        "provider": getattr(settings, "EMAIL_PROVIDER", "mailjet"),
        "backend": settings.EMAIL_BACKEND,
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "use_tls": settings.EMAIL_USE_TLS,
        "use_ssl": getattr(settings, "EMAIL_USE_SSL", False),
        "user": settings.EMAIL_HOST_USER,
        "password": settings.EMAIL_HOST_PASSWORD,
        "from_email": settings.DEFAULT_FROM_EMAIL,
    }

# def get_email_config(provider_override: Optional[str] = None, prefer_provider_specific: bool = False) -> Dict[str, object]:
#     """
#     Build a Django email configuration dictionary.
#
#     provider_override: force a specific provider (mailjet/zoho)
#     prefer_provider_specific: check for PROVIDER_EMAIL_* variables before
#                               falling back to global EMAIL_* values.
#     """
#     provider = _resolve_provider(provider_override)
#     defaults = PROVIDER_DEFAULTS[provider]
#     prefix = provider.upper()
#
#     def env_keys(base: str):
#         keys = []
#         if prefer_provider_specific:
#             keys.append(f"{prefix}_EMAIL_{base}")
#         keys.append(f"EMAIL_{base}")
#         return keys
#
#     backend = _first_env(["EMAIL_BACKEND"]) or defaults["backend"]
#     host = _first_env(env_keys("HOST")) or defaults["host"]
#     port = _parse_int(_first_env(env_keys("PORT")), defaults["port"])
#     use_tls = _parse_bool(_first_env(env_keys("USE_TLS")), bool(defaults["use_tls"]))
#     use_ssl = _parse_bool(_first_env(env_keys("USE_SSL")), bool(defaults["use_ssl"]))
#     user = _first_env(env_keys("HOST_USER")) or defaults.get("user")
#     password = _first_env(env_keys("HOST_PASSWORD")) or defaults.get("password")
#     from_email = _first_env(["DEFAULT_FROM_EMAIL"]) or defaults.get("from_email") or DEFAULT_SENDER
#
#     return {
#         "provider": provider,
#         "backend": backend,
#         "host": host,
#         "port": port,
#         "use_tls": use_tls,
#         "use_ssl": use_ssl,
#         "user": user,
#         "password": password,
#         "from_email": from_email,
#     }
