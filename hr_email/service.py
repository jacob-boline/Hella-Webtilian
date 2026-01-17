# hr_email/service.py

from __future__ import annotations

import logging
from typing import Optional, Sequence

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

from hr_common.utils.unified_logging import log_event
from hr_email.mailjet import MailjetSendError, send_mailjet_email
from hr_email.provider_settings import (
    get_provider,
    get_provider_send_mode,
    get_smtp_email_config,
    get_mailjet_rest_enabled,
)

logger = logging.getLogger(__name__)


class EmailProviderError(RuntimeError):
    """Raised when provider sending fails or is misconfigured."""


def send_app_email(
    *,
    to_emails: Sequence[str],
    subject: str,
    text_body: Optional[str] = None,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    custom_id: Optional[str] = None,
    provider_override: Optional[str] = None,
) -> dict:
    """
    Unified app email sender.

    Returns a dict with details of what happened, e.g.
      {"provider": "mailjet", "mode": "rest", "result": {...}}
      {"provider": "zoho", "mode": "smtp", "result": {"sent": 1}}

    Design goals:
    - All app code calls this function.
    - Provider selection comes from settings (EMAIL_PROVIDER) unless overridden.
    - Mailjet uses REST by default; SMTP for others (or as a fallback if you want).
    """
    provider = get_provider(provider_override)
    mode = get_provider_send_mode(provider)

    if not to_emails:
        raise EmailProviderError("No recipients provided.")

    # Ensure we have at least a text part for SMTP providers.
    if not text_body and html_body:
        text_body = strip_tags(html_body)

    if mode == "rest":
        if provider != "mailjet":
            raise EmailProviderError(f"Provider '{provider}' is not configured for REST sending.")
        if not get_mailjet_rest_enabled():
            raise EmailProviderError("Mailjet REST is selected but MAILJET_API_KEY/MAILJET_API_SECRET are not set.")

        effective_from = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not effective_from:
            raise EmailProviderError("No From address available (DEFAULT_FROM_EMAIL not set and from_email not provided).")

        try:
            result = send_mailjet_email(
                to=[{"Email": e, "Name": e.split("@")[0]} for e in to_emails],
                subject=subject,
                text_part=text_body,
                html_part=html_body,
                custom_id=custom_id,
                from_email=_mailjet_address(effective_from),
                reply_to=_mailjet_address(reply_to) if reply_to else None,
            )
            return {"provider": provider, "mode": mode, "result": result}
        except MailjetSendError as exc:
            log_event(
                logger,
                logging.ERROR,
                "email.mailjet.send_failed",
                error=str(exc),
                exc_info=True,
            )
            raise EmailProviderError(str(exc)) from exc

    # SMTP path (default for non-mailjet providers, and optional for mailjet if forced)
    smtp_cfg = get_smtp_email_config(provider)

    missing = []
    if not smtp_cfg["from_email"] and not from_email:
        missing.append("DEFAULT_FROM_EMAIL (or pass from_email)")
    if not smtp_cfg["user"]:
        missing.append("EMAIL_HOST_USER")
    if not smtp_cfg["password"]:
        missing.append("EMAIL_HOST_PASSWORD")

    if missing:
        raise EmailProviderError(f"SMTP config missing: {', '.join(missing)}")

    connection = get_connection(
        backend=smtp_cfg["backend"],
        host=smtp_cfg["host"],
        port=smtp_cfg["port"],
        username=smtp_cfg["user"],
        password=smtp_cfg["password"],
        use_tls=smtp_cfg["use_tls"],
        use_ssl=smtp_cfg["use_ssl"],
    )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body or "",
        from_email=from_email or smtp_cfg["from_email"],
        to=list(to_emails),
        reply_to=[reply_to] if reply_to else None,
        connection=connection,
    )
    if html_body:
        msg.attach_alternative(html_body, "text/html")

    sent = msg.send(fail_silently=False)
    return {"provider": provider, "mode": "smtp", "result": {"sent": sent}}


def _mailjet_address(raw: Optional[str]) -> Optional[dict]:
    """
    Convert "Name <email@domain>" or "email@domain" to Mailjet dict format.
    If None, return None.
    """
    if not raw:
        return None
    raw = str(raw)
    if "<" in raw and ">" in raw:
        name, email = raw.split("<", 1)
        return {"Email": email.rstrip(">").strip(), "Name": name.strip()}
    return {"Email": raw, "Name": raw.split("@")[0]}
