# hr_core/utils/tokens.py


"""
Secure token generation and verification for email confirmation flows.
Uses Django's signing module for stateless, tamper-proof tokens.
"""

from django.core import signing

from hr_core.utils.email import normalize_email

# Salt for checkout email confirmation tokens
CHECKOUT_EMAIL_SALT = 'checkout-email-confirm'

# Default token expiry: 1 hour
DEFAULT_TOKEN_MAX_AGE = 60 * 60


def generate_checkout_email_token(
        email: str,
        customer_id: int = None,
        address_id: int = None,
        note: str = None
) -> str:
    """
    Generate a signed token for email confirmation during checkout.
    The token embeds all checkout state so it can be restored if the
    user's session expires before they confirm.

    Args:
        email: The email address to confirm
        customer_id: Optional customer record ID
        address_id: Optional shipping address ID
        note: Optional order note

    Returns:
        A URL-safe signed token string
    """

    payload = {
        'email': normalize_email(email)
    }

    if customer_id is not None:
        payload['cid'] = customer_id

    if address_id is not None:
        payload['aid'] = address_id

    if note:
        payload['note'] = note

    return signing.dumps(payload, salt=CHECKOUT_EMAIL_SALT)


def verify_checkout_email_token(
        token: str,
        max_age: int = DEFAULT_TOKEN_MAX_AGE,
) -> dict | None:
    """
    Verify and decode a checkout email confirmation token.

    Args:
        token: The token string to verify
        max_age: Maximum age in seconds (default 1 hour)

    Returns:
        Decoded payload dict with keys: email, cid, aid, note
        Returns None if token is invalid or expired
    """

    try:
        return signing.loads(token, salt=CHECKOUT_EMAIL_SALT, max_age=max_age)

    except signing.BadSignature:
        return None
