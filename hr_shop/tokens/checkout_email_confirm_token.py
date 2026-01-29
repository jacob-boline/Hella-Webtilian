# hr_shop/tokens/checkout_email_confirm_token.py
from __future__ import annotations

from dataclasses import dataclass

from hr_common.security.signing import generate_token, verify_token
from hr_common.utils.email import normalize_email

CHECKOUT_EMAIL_SALT = "checkout-email-confirm"
CHECKOUT_EMAIL_MAX_AGE = 60 * 60  # 1h


@dataclass(frozen=True, slots=True)
class CheckoutEmailConfirmToken:
    email: str
    draft_id: int

    def __post_init__(self):
        object.__setattr__(self, "email", normalize_email(self.email))
        object.__setattr__(self, "draft_id", int(self.draft_id))
        if not self.email:
            raise ValueError("email is required")
        if self.draft_id <= 0:
            raise ValueError("draft_id must be positive")

    def to_payload(self) -> dict:
        return {"email": self.email, "draft_id": self.draft_id}

    @classmethod
    def from_payload(cls, payload: dict) -> CheckoutEmailConfirmToken | None:
        if not isinstance(payload, dict):
            return None
        if "email" not in payload or "draft_id" not in payload:
            return None
        try:
            email = normalize_email(payload["email"])
            draft_id = int(payload["draft_id"])
        except (TypeError, ValueError):
            return None
        if not email or draft_id <= 0:
            return None
        return cls(email=email, draft_id=draft_id)


def generate_checkout_email_token(*, email: str, draft_id: int) -> str:
    tok = CheckoutEmailConfirmToken(email=email, draft_id=draft_id)
    return generate_token(tok.to_payload(), salt=CHECKOUT_EMAIL_SALT)


def verify_checkout_email_token(token: str, *, max_age: int = CHECKOUT_EMAIL_MAX_AGE) -> CheckoutEmailConfirmToken | None:
    payload = verify_token(token, salt=CHECKOUT_EMAIL_SALT, max_age=max_age)
    return CheckoutEmailConfirmToken.from_payload(payload) if payload else None
