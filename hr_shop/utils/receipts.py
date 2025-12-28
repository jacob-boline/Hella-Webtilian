# hr_shop/utils/receipts.py


from django.core import signing

from hr_core.utils.email import normalize_email

RECEIPT_TOKEN_SALT = 'hr_shop.order_receipt'
RECEIPT_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 Days


def make_order_receipt_token(*, order_id: int, email: str) -> str:
    payload = {
        'order_id': int(order_id),
        'email': normalize_email(email or "")
    }
    return signing.dumps(payload, salt=RECEIPT_TOKEN_SALT)


def verify_order_receipt_token(token: str, *, order_id: int, email: str) -> bool:
    if not token:
        return False

    try:
        payload = signing.loads(
            token,
            salt=RECEIPT_TOKEN_SALT,
            max_age=RECEIPT_TOKEN_MAX_AGE_SECONDS
        )
    except signing.BadSignature:
        return False

    if int(payload.get('order_id', -1)) != int(order_id):
        return False

    token_email = normalize_email(payload.get('email') or "")
    real_email = normalize_email(email or "")
    return token_email == real_email
