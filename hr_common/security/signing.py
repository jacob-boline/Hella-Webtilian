# hr_common/security/signing.py

from django.core import signing


def generate_token(payload: dict, *, salt: str) -> str:
    """
    Generate a signed, URL-safe token with the given salt.
    """
    return signing.dumps(payload, salt=salt)


def verify_token(token: str, *, salt: str, max_age: int) -> dict | None:
    """
    Verify and decode a signed token.
    Returns decoded payload or None if invalid/expired.
    """
    try:
        return signing.loads(token, salt=salt, max_age=max_age)
    except (signing.BadSignature, signing.SignatureExpired):
        return None
