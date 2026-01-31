# hr_access/tokens/email_change.py
from __future__ import annotations

from dataclasses import dataclass

from hr_common.security.signing import generate_token, verify_token
from hr_common.utils.email import normalize_email

EMAIL_CHANGE_SALT = "account-email-change"
EMAIL_CHANGE_MAX_AGE = 60 * 60 * 24  # 24h


@dataclass(frozen=True, slots=True)
class EmailChangeToken:
    user_id: int
    email: str

    def __post_init__(self):
        object.__setattr__(self, "user_id", int(self.user_id))
        object.__setattr__(self, "email", normalize_email(self.email))
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if not self.email:
            raise ValueError("email is required")

    def to_payload(self) -> dict:
        return {"user_id": self.user_id, "email": self.email}

    @classmethod
    def from_payload(cls, payload: dict) -> EmailChangeToken | None:
        if not isinstance(payload, dict):
            return None
        if "user_id" not in payload or "email" not in payload:
            return None
        try:
            user_id = int(payload["user_id"])
            email = normalize_email(payload["email"])
        except (TypeError, ValueError):
            return None
        if user_id <= 0 or not email:
            return None
        return cls(user_id=user_id, email=email)


def generate_email_change_token(*, user_id: int, new_email: str) -> str:
    tok = EmailChangeToken(user_id=user_id, email=new_email)
    return generate_token(tok.to_payload(), salt=EMAIL_CHANGE_SALT)


def verify_email_change_token(token: str, *, max_age: int = EMAIL_CHANGE_MAX_AGE) -> EmailChangeToken | None:
    payload = verify_token(token, salt=EMAIL_CHANGE_SALT, max_age=max_age)
    return EmailChangeToken.from_payload(payload) if payload else None
