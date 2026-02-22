# hr_access/tests/test_tokens.py

import pytest

from hr_access.tokens.account_signup import (
    AccountSignupToken,
    generate_account_signup_token,
    verify_account_signup_token,
)
from hr_access.tokens.email_change import (
    EmailChangeToken,
    generate_email_change_token,
    verify_email_change_token,
)


@pytest.mark.parametrize(
    "token_cls,payload",
    [
        (AccountSignupToken, {"user_id": "7", "email": "  USER@Example.COM "}),
        (EmailChangeToken, {"user_id": "7", "email": "  USER@Example.COM "}),
    ],
)
def test_token_from_payload_normalizes_and_coerces(token_cls, payload):
    token = token_cls.from_payload(payload)

    assert token is not None
    assert token.user_id == 7
    assert token.email == "user@example.com"


@pytest.mark.parametrize(
    "token_cls,payload",
    [
        (AccountSignupToken, None),
        (AccountSignupToken, "bad"),
        (AccountSignupToken, {"user_id": 1}),
        (AccountSignupToken, {"email": "x@example.com"}),
        (AccountSignupToken, {"user_id": 0, "email": "x@example.com"}),
        (AccountSignupToken, {"user_id": "abc", "email": "x@example.com"}),
        (AccountSignupToken, {"user_id": 1, "email": "   "}),
        (EmailChangeToken, None),
        (EmailChangeToken, "bad"),
        (EmailChangeToken, {"user_id": 1}),
        (EmailChangeToken, {"email": "x@example.com"}),
        (EmailChangeToken, {"user_id": 0, "email": "x@example.com"}),
        (EmailChangeToken, {"user_id": "abc", "email": "x@example.com"}),
        (EmailChangeToken, {"user_id": 1, "email": "   "}),
    ],
)
def test_token_from_payload_rejects_invalid_shapes(token_cls, payload):
    assert token_cls.from_payload(payload) is None


def test_account_signup_token_round_trip_and_expiry():
    signed = generate_account_signup_token(user_id=5, email="  USER@Example.COM ")

    token = verify_account_signup_token(signed)
    assert token is not None
    assert token.user_id == 5
    assert token.email == "user@example.com"

    assert verify_account_signup_token(signed, max_age=-1) is None


def test_email_change_token_round_trip_and_expiry():
    signed = generate_email_change_token(user_id=9, new_email="  NEW@Example.COM ")

    token = verify_email_change_token(signed)
    assert token is not None
    assert token.user_id == 9
    assert token.email == "new@example.com"

    assert verify_email_change_token(signed, max_age=-1) is None
