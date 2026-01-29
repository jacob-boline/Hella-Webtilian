# hr_access/tokens/account_signup.py
from __future__ import annotations

from dataclasses import dataclass

from hr_common.security.signing import generate_token, verify_token
from hr_common.utils.email import normalize_email

ACCOUNT_SIGNUP_SALT = "account-signup-confirmation"
ACCOUNT_SIGNUP_MAX_AGE = 60 * 60 * 24  # 24h


@dataclass(frozen=True, slots=True)
class AccountSignupToken:
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
    def from_payload(cls, payload: dict) -> AccountSignupToken | None:
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


def generate_account_signup_token(*, user_id: int, email: str) -> str:
    tok = AccountSignupToken(user_id=user_id, email=email)
    return generate_token(tok.to_payload(), salt=ACCOUNT_SIGNUP_SALT)


def verify_account_signup_token(token: str, *, max_age: int = ACCOUNT_SIGNUP_MAX_AGE) -> AccountSignupToken | None:
    payload = verify_token(token, salt=ACCOUNT_SIGNUP_SALT, max_age=max_age)
    return AccountSignupToken.from_payload(payload) if payload else None
