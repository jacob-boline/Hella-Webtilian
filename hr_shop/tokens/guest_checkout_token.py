# hr_shop/tokens/guest_checkout_token.py
from __future__ import annotations

from dataclasses import dataclass

from hr_common.security.signing import generate_token, verify_token

CHECKOUT_CTX_SALT = "checkout-context"
CHECKOUT_CTX_MAX_AGE = 60 * 30


@dataclass(frozen=True, slots=True)
class GuestCheckoutToken:
    customer_id: int
    draft_id: int
    order_id: int

    def __post_init__(self):
        object.__setattr__(self, "customer_id", int(self.customer_id))
        object.__setattr__(self, "draft_id", int(self.draft_id))
        object.__setattr__(self, "order_id", int(self.order_id))
        if self.customer_id <= 0 or self.draft_id <= 0 or self.order_id <= 0:
            raise ValueError("IDs must be positive")

    def to_payload(self) -> dict:
        return {"customer_id": self.customer_id, "draft_id": self.draft_id, "order_id": self.order_id}

    @classmethod
    def from_payload(cls, payload: dict) -> GuestCheckoutToken | None:
        if not isinstance(payload, dict):
            return None
        if "customer_id" not in payload or "draft_id" not in payload or "order_id" not in payload:
            return None

        try:
            customer_id = int(payload["customer_id"])
            draft_id = int(payload["draft_id"])
            order_id = int(payload["order_id"])
        except (TypeError, ValueError, KeyError):
            return None

        if customer_id <= 0 or draft_id <= 0 or order_id <= 0:
            return None

        return cls(customer_id=customer_id, draft_id=draft_id, order_id=order_id)


def generate_guest_checkout_token(customer_id: int, draft_id: int, order_id: int) -> str:
    token = GuestCheckoutToken(customer_id=customer_id, draft_id=draft_id, order_id=order_id)
    return generate_token(token.to_payload(), salt=CHECKOUT_CTX_SALT)


def verify_guest_checkout_token(token: str) -> GuestCheckoutToken | None:
    try:
        payload = verify_token(token, salt=CHECKOUT_CTX_SALT, max_age=CHECKOUT_CTX_MAX_AGE)
    except Exception:
        return None
    return GuestCheckoutToken.from_payload(payload) if payload else None
