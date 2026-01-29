# hr_shop/tokens/tokens.py


from hr_common.security.signing import generate_token, verify_token
from hr_common.utils.email import normalize_email

# ============================================================
# Salts (token intent separation)
# ============================================================
CHECKOUT_EMAIL_SALT = "checkout-email-confirm"
ORDER_RECEIPT_SALT = "order-receipt"

# ============================================================
# Expiry windows (seconds)
# ============================================================
DEFAULT_CHECKOUT_TOKEN_MAX_AGE = 60 * 60  # 1 hour
DEFAULT_RECEIPT_TOKEN_MAX_AGE = 60 * 60 * 24 * 14  # 14 days


def generate_checkout_email_token(email: str, draft_id: int) -> str:
    """ Generate a signed token for checkout email confirmation. """
    payload = {"email": normalize_email(email), "draft_id": int(draft_id)}
    return generate_token(payload, salt=CHECKOUT_EMAIL_SALT)


def verify_checkout_email_token(token: str, max_age: int = DEFAULT_CHECKOUT_TOKEN_MAX_AGE) -> dict | None:
    """
    Verify and decode a checkout email confirmation token.

    Returns payload dict or None if invalid/expired.
    """
    return verify_token(token, salt=CHECKOUT_EMAIL_SALT, max_age=max_age)


# ============================================================
# Guest order receipt tokens
# ============================================================


def generate_order_receipt_token(order_id: int, email: str) -> str:
    """ Generate a signed token granting temporary access to a single order. """
    payload = {"order_id": int(order_id), "email": normalize_email(email)}
    return generate_token(payload, salt=ORDER_RECEIPT_SALT)


def verify_order_receipt_token(token: str, max_age: int = DEFAULT_RECEIPT_TOKEN_MAX_AGE) -> dict | None:
    """
    Verify and decode a guest order receipt token.

    Returns payload dict with keys:
        - order_id
        - email

    Returns None if invalid, expired, or malformed.
    """
    data = verify_token(token, salt=ORDER_RECEIPT_SALT, max_age=max_age)

    if not data:
        return None

    # Defensive sanity check
    if "order_id" not in data or "email" not in data:
        return None

    return data
