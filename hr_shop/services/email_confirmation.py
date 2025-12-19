# hr_shop/services/email_confirmation.py

"""
Email confirmation service for checkout flow.
Handles sending confirmation emails and rate limiting.
"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import generate_checkout_email_token
from hr_shop.exceptions import RateLimitExceeded, EmailSendError
from hr_shop.models import ConfirmedEmail

logger = logging.getLogger(__name__)

# Rate limiting settings

RATE_LIMIT_MAX_EMAILS = 3
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour


def is_email_confirmed_for_checkout(request, email: str) -> bool:
    """
    Check if the given email is confirmed for checkout.
    An email is considered confirmed if:
    1. The user is authenticated and the email matches their account email
    2. The email exists in the ConfirmedEmail table

    Args:
        request: The HTTP request object
        email: The email address to check

    Returns:
        True if confirmed, False otherwise
    """

    normalized = normalize_email(email)
    user = getattr(request, 'user', None)

    # Authenticated users with matching email are always confirmed
    if user and user.is_authenticated and user.email:
        if normalize_email(user.email) == normalized:
            return True

    # Check database for permanent confirmation
    return ConfirmedEmail.is_confirmed(normalized)


def can_send_confirmation_email(email: str) -> bool:
    """
    Check if we can send another confirmation email (rate limiting).

    Args:
        email: The email address to check

    Returns:
        True if under rate limit, False if limit exceeded
    """

    key = f'checkout_email_count:{normalize_email(email)}'
    count = cache.get(key, 0)

    return count < RATE_LIMIT_MAX_EMAILS


def increment_email_send_count(email: str) -> int:
    """
    Increment the send count for rate limiting.

    Args:
        email: The email address

    Returns:
        The new count after incrementing
    """

    key = f'checkout_email_count:{normalize_email(email)}'
    count = cache.get(key, 0)
    new_count = count + 1
    cache.set(key, new_count, timeout=RATE_LIMIT_WINDOW_SECONDS)

    return new_count


def send_checkout_confirmation_email(
        request,
        email: str,
        draft_id: int
) -> str:
    """
    Send a confirmation email with a secure link.

    Args:
        request: The HTTP request object (for building absolute URLs)
        email: The email address to send to
        draft_id: The CheckoutDraft record ID to embed in token
        customer_id: Optional customer record ID to embed in token
        address_id: Optional address record ID to embed in token
        note: Optional order note to embed in token

    Returns:
        The confirmation URL that was sent

    Raises:
        RateLimitExceeded: If too many emails have been sent recently
        EmailSendError: If the email fails to send
    """

    normalized_email = normalize_email(email)

    # Check rate limit
    if not can_send_confirmation_email(normalized_email):
        logger.warning(f"Rate limit exceeded for email: {normalized_email}")

        raise RateLimitExceeded(
            "Too many confirmation emails sent. Please check your inbox or try again later."
        )

    # Generate token with all checkout state
    token = generate_checkout_email_token(
        email=normalized_email,
        draft_id=draft_id
    )

    # Build confirmation URL
    confirm_path = reverse('hr_shop:confirm_checkout_email', args=[token])
    confirm_url = request.build_absolute_uri(confirm_path)

    # Email content
    subject = 'Confirm your email to complete your order - Hella Reptilian'

    # Plain text version
    plain_message = f"""
Please confirm your email address to continue with your order.

Click here to confirm: {confirm_url}
This link expires in 1 hour.

If you didn't request this, you can safely ignore this email.

---

Hella Reptilian

"""

    # HTML version
    html_message = render_to_string(
        'hr_shop/emails/confirm_checkout_email.html',
        {
            'confirm_url': confirm_url,
            'email':       normalized_email,
            'year':        timezone.now().year,
        }
    )

    # Send the email
    try:
        send_mail(
            subject=subject,
            message=plain_message.strip(),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hellareptilian.com'),
            recipient_list=[normalized_email],
            html_message=html_message,
            fail_silently=False
        )

    except Exception as e:
        logger.error(f"Failed to send confirmation email to {normalized_email}: {e}")
        raise EmailSendError(
            "Could not send confirmation email. Please try again."
        ) from e

    # Increment rate limit counter after successful send
    increment_email_send_count(normalized_email)
    logger.info(f"Confirmation email sent to {normalized_email}")

    return confirm_url


def get_rate_limit_status(email: str) -> dict:
    """
    Get the current rate limit status for an email.

    Args:
        email: The email address to check

    Returns:
        Dict with 'count', 'limit', and 'can_send' keys
    """

    key = f'checkout_email_count:{normalize_email(email)}'
    count = cache.get(key, 0)

    return {
        'count':    count,
        'limit':    RATE_LIMIT_MAX_EMAILS,
        'can_send': count < RATE_LIMIT_MAX_EMAILS,
    }
