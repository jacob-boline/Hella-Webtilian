# hr_access/tests/test_account_email_rate_limit.py

import pytest
from django.core.cache import cache
from django.test import RequestFactory

from hr_access.models import User
from hr_access.views.account import (
    _can_send_email_change,
    _can_send_signup_email,
    _get_last_email_change_sent_at,
    _get_last_signup_confirmation_sent_at,
    _increment_email_change_email_count,
    _increment_signup_email_count,
    send_account_verify_email,
    send_email_change_verification,
)
from hr_email.service import EmailProviderError
from hr_shop.exceptions import EmailSendError, RateLimitExceeded


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_signup_rate_limit_helpers_write_counts_and_sent_at(monkeypatch):
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    sent_calls = []

    def fake_send(**kwargs):
        sent_calls.append(kwargs)

    monkeypatch.setattr("hr_access.views.account.send_app_email", fake_send)

    assert _can_send_signup_email(user.email) is True
    assert _increment_signup_email_count(user.email) == 1

    send_account_verify_email(req, user)

    assert len(sent_calls) == 1
    assert _get_last_signup_confirmation_sent_at(user.email) is not None


@pytest.mark.django_db
def test_send_account_verify_email_raises_rate_limit_when_limit_reached():
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    for _ in range(3):
        _increment_signup_email_count(user.email)

    assert _can_send_signup_email(user.email) is False
    with pytest.raises(RateLimitExceeded):
        send_account_verify_email(req, user)


@pytest.mark.django_db
def test_send_account_verify_email_maps_provider_error(monkeypatch):
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    def explode(**_kwargs):
        raise EmailProviderError("provider down")

    monkeypatch.setattr("hr_access.views.account.send_app_email", explode)

    with pytest.raises(EmailSendError):
        send_account_verify_email(req, user)


@pytest.mark.django_db
def test_email_change_rate_limit_helpers_write_counts_and_sent_at(monkeypatch):
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    sent_calls = []

    def fake_send(**kwargs):
        sent_calls.append(kwargs)

    monkeypatch.setattr("hr_access.views.account.send_app_email", fake_send)

    assert _can_send_email_change(user.id) is True
    assert _increment_email_change_email_count(user.id) == 1

    send_email_change_verification(req, user, "new@example.com")

    assert len(sent_calls) == 1
    assert _get_last_email_change_sent_at(user.id) is not None


@pytest.mark.django_db
def test_send_email_change_verification_raises_rate_limit_when_limit_reached():
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    for _ in range(3):
        _increment_email_change_email_count(user.id)

    assert _can_send_email_change(user.id) is False
    with pytest.raises(RateLimitExceeded):
        send_email_change_verification(req, user, "new@example.com")


@pytest.mark.django_db
def test_send_email_change_verification_maps_provider_error(monkeypatch):
    user = User.objects.create_user(email="rate@example.com", username="rateuser", password="StrongPass123!")
    rf = RequestFactory()
    req = rf.get("/")

    def explode(**_kwargs):
        raise EmailProviderError("provider down")

    monkeypatch.setattr("hr_access.views.account.send_app_email", explode)

    with pytest.raises(EmailSendError):
        send_email_change_verification(req, user, "new@example.com")
