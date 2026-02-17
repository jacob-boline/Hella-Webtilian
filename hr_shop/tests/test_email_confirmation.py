# hr_shop/tests/test_email_confirmation.py

# Tests for:
#   - hr_shop/services/email_confirmation.py  (service layer)
#   - ConfirmedEmail model class methods
#   - CheckoutDraft.is_valid()
#
# Strategy:
#   - send_checkout_confirmation_email is tested by mocking send_app_email —
#     we never send a real email.
#   - Rate limiting uses Django's cache framework; we use the locmem cache
#     backend (set in test settings) and clear it between tests via the
#     `cache` fixture.
#   - Token generation (generate_checkout_email_token) is also mocked so
#     tests don't depend on signing keys being present.

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache as django_cache
from django.utils import timezone

from hr_shop.exceptions import EmailSendError, RateLimitExceeded
from hr_shop.models import ConfirmedEmail
from hr_shop.services.email_confirmation import (can_send_confirmation_email, get_rate_limit_status, increment_email_send_count,
                                                 is_email_confirmed_for_checkout, RATE_LIMIT_MAX_EMAILS, send_checkout_confirmation_email)
from tests.factories import CheckoutDraftFactory

SEND_APP_EMAIL = "hr_shop.services.email_confirmation.send_app_email"
GENERATE_TOKEN = "hr_shop.services.email_confirmation.generate_checkout_email_token"


@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the cache before each test so rate limit counts don't bleed between tests."""
    django_cache.clear()
    yield
    django_cache.clear()


# ---------------------------------------------------------------------------
# ConfirmedEmail model methods
# ---------------------------------------------------------------------------

class TestConfirmedEmail:
    def test_is_confirmed_returns_false_for_unknown_email(self, db):
        assert ConfirmedEmail.is_confirmed("nobody@example.com") is False

    def test_is_confirmed_returns_true_after_mark_confirmed(self, db):
        ConfirmedEmail.mark_confirmed("test@example.com")
        assert ConfirmedEmail.is_confirmed("test@example.com") is True

    def test_mark_confirmed_is_idempotent(self, db):
        ConfirmedEmail.mark_confirmed("test@example.com")
        ConfirmedEmail.mark_confirmed("test@example.com")  # second call should not raise
        assert ConfirmedEmail.objects.filter(email="test@example.com").count() == 1

    def test_is_confirmed_is_case_insensitive(self, db):
        ConfirmedEmail.mark_confirmed("Test@Example.COM")
        assert ConfirmedEmail.is_confirmed("test@example.com") is True


# ---------------------------------------------------------------------------
# CheckoutDraft.is_valid()
# ---------------------------------------------------------------------------

class TestCheckoutDraftIsValid:
    def test_fresh_draft_is_valid(self, db):
        draft = CheckoutDraftFactory(
            expires_at=timezone.now() + timedelta(hours=1),
            used_at=None,
        )
        assert draft.is_valid() is True

    def test_expired_draft_is_not_valid(self, db):
        draft = CheckoutDraftFactory(
            expires_at=timezone.now() - timedelta(seconds=1),
            used_at=None,
        )
        assert draft.is_valid() is False

    def test_used_draft_is_not_valid(self, db):
        draft = CheckoutDraftFactory(
            expires_at=timezone.now() + timedelta(hours=1),
            used_at=timezone.now(),
        )
        assert draft.is_valid() is False

    def test_expired_and_used_draft_is_not_valid(self, db):
        draft = CheckoutDraftFactory(
            expires_at=timezone.now() - timedelta(hours=1),
            used_at=timezone.now() - timedelta(minutes=30),
        )
        assert draft.is_valid() is False


# ---------------------------------------------------------------------------
# is_email_confirmed_for_checkout()
# ---------------------------------------------------------------------------

class TestIsEmailConfirmedForCheckout:
    def test_unconfirmed_email_with_anonymous_user_returns_false(self, db, rf):
        """rf is pytest-django's RequestFactory fixture."""
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=False)

        assert is_email_confirmed_for_checkout(request, "guest@example.com") is False

    def test_confirmed_email_with_anonymous_user_returns_true(self, db, rf):
        ConfirmedEmail.mark_confirmed("guest@example.com")
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=False)

        assert is_email_confirmed_for_checkout(request, "guest@example.com") is True

    def test_authenticated_user_with_matching_email_returns_true(self, db, rf):
        """
        An authenticated user whose email matches is considered confirmed
        without needing a ConfirmedEmail row.
        """
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=True, email="auth@example.com")

        assert is_email_confirmed_for_checkout(request, "auth@example.com") is True

    def test_authenticated_user_with_different_email_falls_back_to_db(self, db, rf):
        """
        If the auth user's email doesn't match, fall through to ConfirmedEmail check.
        """
        request = rf.get("/")
        request.user = MagicMock(is_authenticated=True, email="other@example.com")

        assert is_email_confirmed_for_checkout(request, "guest@example.com") is False


# ---------------------------------------------------------------------------
# Rate limiting helpers
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_can_send_when_count_is_zero(self, db):
        assert can_send_confirmation_email("new@example.com") is True

    def test_cannot_send_when_limit_reached(self, db):
        for _ in range(RATE_LIMIT_MAX_EMAILS):
            increment_email_send_count("limited@example.com")

        assert can_send_confirmation_email("limited@example.com") is False

    def test_increment_increases_count(self, db):
        increment_email_send_count("counter@example.com")
        status = get_rate_limit_status("counter@example.com")
        assert status["count"] == 1

    def test_get_rate_limit_status_shape(self, db):
        status = get_rate_limit_status("fresh@example.com")
        assert status["count"] == 0
        assert status["limit"] == RATE_LIMIT_MAX_EMAILS
        assert status["can_send"] is True


# ---------------------------------------------------------------------------
# send_checkout_confirmation_email()
# ---------------------------------------------------------------------------

class TestSendCheckoutConfirmationEmail:
    def test_happy_path_calls_send_app_email(self, db, rf):
        """
        The happy path should call send_app_email once with the right recipient
        and increment the rate limit counter.
        """
        request = rf.get("/")
        draft = CheckoutDraftFactory()

        with patch(GENERATE_TOKEN, return_value="fake-token-abc"):
            with patch(SEND_APP_EMAIL, return_value={"success": True}) as mock_send:
                send_checkout_confirmation_email(request, draft.email, draft.id)

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args.kwargs
        assert draft.email in call_kwargs["to_emails"]

        # Counter was incremented
        status = get_rate_limit_status(draft.email)
        assert status["count"] == 1

    def test_raises_rate_limit_exceeded_when_limit_hit(self, db, rf):
        request = rf.get("/")
        draft = CheckoutDraftFactory()

        for _ in range(RATE_LIMIT_MAX_EMAILS):
            increment_email_send_count(draft.email)

        with pytest.raises(RateLimitExceeded):
            with patch(GENERATE_TOKEN, return_value="fake-token"):
                with patch(SEND_APP_EMAIL, return_value={}):
                    send_checkout_confirmation_email(request, draft.email, draft.id)

    def test_raises_email_send_error_on_provider_failure(self, db, rf):
        """
        If send_app_email raises EmailProviderError, the service should
        wrap it in EmailSendError and not increment the counter.
        """
        from hr_email.service import EmailProviderError

        request = rf.get("/")
        draft = CheckoutDraftFactory()

        with pytest.raises(EmailSendError):
            with patch(GENERATE_TOKEN, return_value="fake-token"):
                with patch(SEND_APP_EMAIL, side_effect=EmailProviderError("mailjet down")):
                    send_checkout_confirmation_email(request, draft.email, draft.id)

        # Counter must NOT have been incremented — send failed
        status = get_rate_limit_status(draft.email)
        assert status["count"] == 0

    def test_send_does_not_hit_real_email_provider(self, db, rf):
        """
        Sanity check: confirm no real network call is made. If the mock isn't
        in place this test will raise because send_app_email needs real credentials.
        """
        request = rf.get("/")
        draft = CheckoutDraftFactory()

        with patch(GENERATE_TOKEN, return_value="fake-token"):
            with patch(SEND_APP_EMAIL, return_value={}) as mock_send:
                send_checkout_confirmation_email(request, draft.email, draft.id)

        assert mock_send.called
