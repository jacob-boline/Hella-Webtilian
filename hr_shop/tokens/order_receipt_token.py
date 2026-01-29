# hr_shop/tokens/order_receipt_token.py
from __future__ import annotations

from dataclasses import dataclass

from hr_common.security.signing import generate_token, verify_token
from hr_common.utils.email import normalize_email

ORDER_RECEIPT_SALT = "order-receipt"
ORDER_RECEIPT_MAX_AGE = 60 * 60 * 24 * 14  # 14d


@dataclass(frozen=True, slots=True)
class OrderReceiptToken:
    order_id: int
    email: str

    def __post_init__(self):
        object.__setattr__(self, "order_id", int(self.order_id))
        object.__setattr__(self, "email", normalize_email(self.email))
        if self.order_id <= 0:
            raise ValueError("order_id must be positive")
        if not self.email:
            raise ValueError("email is required")

    def to_payload(self) -> dict:
        return {"order_id": self.order_id, "email": self.email}

    @classmethod
    def from_payload(cls, payload: dict) -> OrderReceiptToken | None:
        if not isinstance(payload, dict):
            return None
        if "order_id" not in payload or "email" not in payload:
            return None
        try:
            order_id = int(payload["order_id"])
            email = normalize_email(payload["email"])
        except (TypeError, ValueError):
            return None
        if order_id <= 0 or not email:
            return None
        return cls(order_id=order_id, email=email)


def generate_order_receipt_token(*, order_id: int, email: str) -> str:
    tok = OrderReceiptToken(order_id=order_id, email=email)
    return generate_token(tok.to_payload(), salt=ORDER_RECEIPT_SALT)


def verify_order_receipt_token(token: str, *, max_age: int = ORDER_RECEIPT_MAX_AGE) -> OrderReceiptToken | None:
    payload = verify_token(token, salt=ORDER_RECEIPT_SALT, max_age=max_age)
    return OrderReceiptToken.from_payload(payload) if payload else None
