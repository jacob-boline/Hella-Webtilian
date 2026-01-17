# hr_email/provider_settings.py

"""
Email provider configuration.

Goal: the rest of the app asks "who is the provider?" and sends through one
unified service layer, instead of mixing SMTP/REST calls everywhere.
"""

from __future__ import annotations

from typing import Dict, Optional

from django.conf import settings


PROVIDER_DEFAULTS: Dict[str, Dict[str, object]] = {
    # Mailjet: prefer REST for sending; SMTP config still exists as a fallback option.
    "mailjet": {
        "smtp_backend": "django.core.mail.backends.smtp.EmailBackend",
        "smtp_host": "in-v3.mailjet.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False,
        "send_via": "rest",  # "rest" or "smtp"
    },

    # Example future provider; keep for when you re-enable Zoho:
    # "zoho": {
    #     "smtp_backend": "django.core.mail.backends.smtp.EmailBackend",
    #     "smtp_host": "smtp.zoho.com",
    #     "smtp_port": 465,
    #     "smtp_use_tls": False,
    #     "smtp_use_ssl": True,
    #     "send_via": "smtp",
    # },
}

AVAILABLE_PROVIDERS = tuple(PROVIDER_DEFAULTS.keys())


def get_provider(provider_override: Optional[str] = None) -> str:
    provider = (provider_override or getattr(settings, "EMAIL_PROVIDER", None) or "mailjet").strip().lower()
    return provider if provider in PROVIDER_DEFAULTS else "mailjet"


def get_provider_send_mode(provider_override: Optional[str] = None) -> str:
    """
    Returns "rest" or "smtp" based on provider defaults (and optional override in settings).
    """
    provider = get_provider(provider_override)
    # Allow explicit override in settings if you ever need it:
    # EMAIL_SEND_MODE="smtp" to force SMTP even for mailjet.
    forced = getattr(settings, "EMAIL_SEND_MODE", None)
    if forced:
        forced = str(forced).strip().lower()
        if forced in {"rest", "smtp"}:
            return forced
    return str(PROVIDER_DEFAULTS[provider].get("send_via", "smtp")).strip().lower()


def get_smtp_email_config(provider_override: Optional[str] = None) -> dict:
    """
    SMTP config used by Django's email system for SMTP-based providers,
    and as a fallback for providers that support both.

    Settings can override host/port/tls/ssl/backend if you want.
    """
    provider = get_provider(provider_override)
    defaults = PROVIDER_DEFAULTS[provider]

    backend = getattr(settings, "EMAIL_BACKEND", defaults["smtp_backend"])
    host = getattr(settings, "EMAIL_HOST", defaults["smtp_host"])
    port = getattr(settings, "EMAIL_PORT", defaults["smtp_port"])
    use_tls = getattr(settings, "EMAIL_USE_TLS", defaults["smtp_use_tls"])
    use_ssl = getattr(settings, "EMAIL_USE_SSL", defaults["smtp_use_ssl"])

    return {
        "provider": provider,
        "backend": backend,
        "host": host,
        "port": port,
        "use_tls": use_tls,
        "use_ssl": use_ssl,
        "user": getattr(settings, "EMAIL_HOST_USER", None),
        "password": getattr(settings, "EMAIL_HOST_PASSWORD", None),
        "from_email": getattr(settings, "DEFAULT_FROM_EMAIL", None),
    }


def get_mailjet_rest_enabled() -> bool:
    api_key = getattr(settings, "MAILJET_API_KEY", None)
    api_secret = getattr(settings, "MAILJET_API_SECRET", None)
    return bool(api_key and api_secret)
