# hr_shop/services/email_confirmation.py

"""
Email confirmation service for checkout flow.
Handles sending confirmation emails and rate limiting.
"""

import logging
import os

from django.core.cache import cache
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from hr_common.utils.email import normalize_email
from hr_common.utils.unified_logging import log_event
from hr_core.utils.urls import build_external_absolute_url
from hr_email.service import EmailProviderError, send_app_email
from hr_shop.exceptions import RateLimitExceeded, EmailSendError
from hr_shop.models import ConfirmedEmail
from hr_shop.tokens import generate_checkout_email_token

logger = logging.getLogger(__name__)

EXTERNAL_BASE_URL = os.getenv('EXTERNAL_BASE_URL', '').rstrip('/')

RATE_LIMIT_MAX_EMAILS = 3
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour

SENT_AT_KEY = 'checkout_confirm_sent_at:{email}'
SENT_AT_TTL = RATE_LIMIT_WINDOW_SECONDS


def is_email_confirmed_for_checkout(request, email: str) -> bool:
    normalized = normalize_email(email)
    user = getattr(request, "user", None)

    if user and user.is_authenticated and user.email:
        if normalize_email(user.email) == normalized:
            return True

    return ConfirmedEmail.is_confirmed(normalized)


def can_send_confirmation_email(email: str) -> bool:
    key = f"checkout_email_count:{normalize_email(email)}"
    count = cache.get(key, 0)
    return count < RATE_LIMIT_MAX_EMAILS


def increment_email_send_count(email: str) -> int:
    key = f"checkout_email_count:{normalize_email(email)}"
    count = cache.get(key, 0)
    new_count = count + 1
    cache.set(key, new_count, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return new_count


def send_checkout_confirmation_email(request, email: str, draft_id: int) -> str:
    normalized_email = normalize_email(email)

    if not can_send_confirmation_email(normalized_email):
        log_event(logger, logging.WARNING, "checkout_email.rate_limit_exceeded", email=normalized_email)
        raise RateLimitExceeded("Too many confirmation emails sent. Please check your inbox or try again later.")

    token = generate_checkout_email_token(email=normalized_email, draft_id=draft_id)
    confirm_url = build_external_absolute_url(request, reverse("hr_shop:email_confirmation_process_response"), query={"t": token})
    subject = "Confirm your email to complete your order - Hella Reptilian"

    plain_message = f"""
Please confirm your email address to continue with your order.

Click here to confirm: {confirm_url}
This link expires in 1 hour.

If you didn't request this, you can safely ignore this email.

---

Hella Reptilian
""".strip()

    html_message = render_to_string(
        "hr_shop/emails/guest_checkout_email_confirmation.html",
        {"confirm_url": confirm_url, "email": normalized_email, "year": timezone.now().year}
    )

    try:
        result = send_app_email(
            to_emails=[normalized_email],
            subject=subject,
            text_body=plain_message,
            html_body=html_message,
            custom_id=f"checkout_confirm_{draft_id}"
        )
        log_event(logger, logging.INFO, "checkout_email.send_result", email=normalized_email, result=result)

    except EmailProviderError as exc:
        log_event(logger, logging.ERROR, "checkout_email.send_failed", email=normalized_email, error=str(exc))
        raise EmailSendError("Could not send confirmation email. Please try again.") from exc

    increment_email_send_count(normalized_email)
    cache.set(SENT_AT_KEY.format(email=normalized_email), timezone.now(), timeout=SENT_AT_TTL)
    log_event(logger, logging.INFO, "checkout_email.sent", email=normalized_email, draft_id=draft_id)

    return confirm_url


def get_rate_limit_status(email: str) -> dict:
    key = f"checkout_email_count:{normalize_email(email)}"
    count = cache.get(key, 0)
    return {"count": count, "limit": RATE_LIMIT_MAX_EMAILS, "can_send": count < RATE_LIMIT_MAX_EMAILS}
