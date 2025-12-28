# hr_core/utils/tokens.py

"""
Secure token generation and verification for email- and receipt-based flows.

Uses Django's signing module for stateless, tamper-proof, expiring tokens.
Multiple token intents are separated by salts.
"""

from django.core import signing

from hr_core.utils.email import normalize_email


# ============================================================
# Salts (token intent separation)
# ============================================================

CHECKOUT_EMAIL_SALT = "checkout-email-confirm"
ORDER_RECEIPT_SALT = "order-receipt"


# ============================================================
# Expiry windows (seconds)
# ============================================================

DEFAULT_CHECKOUT_TOKEN_MAX_AGE = 60 * 60           # 1 hour
DEFAULT_RECEIPT_TOKEN_MAX_AGE = 60 * 60 * 24 * 14  # 14 days

ACCOUNT_SIGNUP_SALT = 'account-signup-confirmation'
DEFAULT_ACCOUNT_SIGNUP_TOKEN_MAX_AGE = 60 * 60 * 24


# ============================================================
# Internal helpers (shared engine)
# ============================================================

def _generate_token(payload: dict, *, salt: str) -> str:
    """
    Generate a signed, URL-safe token with the given salt.
    """
    return signing.dumps(payload, salt=salt)


def _verify_token(token: str, *, salt: str, max_age: int) -> dict | None:
    """
    Verify and decode a signed token.
    Returns decoded payload or None if invalid/expired.
    """
    try:
        return signing.loads(token, salt=salt, max_age=max_age)
    except signing.BadSignature:
        return None


# ============================================================
# Checkout email confirmation tokens
# ============================================================


def generate_account_signup_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": int(user_id),
        "email": normalize_email(email),
    }
    return _generate_token(payload, salt=ACCOUNT_SIGNUP_SALT)


def verify_account_signup_token(
    token: str,
    max_age: int = DEFAULT_ACCOUNT_SIGNUP_TOKEN_MAX_AGE,
) -> dict | None:
    data = _verify_token(
        token,
        salt=ACCOUNT_SIGNUP_SALT,
        max_age=max_age,
    )
    if not data:
        return None
    if "user_id" not in data or "email" not in data:
        return None
    return data



def generate_checkout_email_token(email: str, draft_id: int) -> str:
    """
    Generate a signed token for checkout email confirmation.

    Payload:
        {
            email: normalized email,
            draft_id: draft order ID
        }
    """
    payload = {
        "email": normalize_email(email),
        "draft_id": int(draft_id),
    }
    return _generate_token(payload, salt=CHECKOUT_EMAIL_SALT)


def verify_checkout_email_token(
    token: str,
    max_age: int = DEFAULT_CHECKOUT_TOKEN_MAX_AGE,
) -> dict | None:
    """
    Verify and decode a checkout email confirmation token.

    Returns payload dict or None if invalid/expired.
    """
    return _verify_token(
        token,
        salt=CHECKOUT_EMAIL_SALT,
        max_age=max_age,
    )


# ============================================================
# Guest order receipt tokens
# ============================================================

def generate_order_receipt_token(order_id: int, email: str) -> str:
    """
    Generate a signed token granting temporary access to a single order.

    Payload:
        {
            order_id: order primary key,
            email: normalized email
        }
    """
    payload = {
        "order_id": int(order_id),
        "email": normalize_email(email),
    }
    return _generate_token(payload, salt=ORDER_RECEIPT_SALT)


def verify_order_receipt_token(
    token: str,
    max_age: int = DEFAULT_RECEIPT_TOKEN_MAX_AGE,
) -> dict | None:
    """
    Verify and decode a guest order receipt token.

    Returns payload dict with keys:
        - order_id
        - email

    Returns None if invalid, expired, or malformed.
    """
    data = _verify_token(
        token,
        salt=ORDER_RECEIPT_SALT,
        max_age=max_age,
    )

    if not data:
        return None

    # Defensive sanity check
    if "order_id" not in data or "email" not in data:
        return None

    return data
