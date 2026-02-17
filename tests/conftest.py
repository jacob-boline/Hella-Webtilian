# tests/conftest.py


import pytest


@pytest.fixture(autouse=True)
def mock_secrets(monkeypatch):
    """Prevent read_secret() from touching the filesystem/env in any test."""
    fake = {
        "STRIPE_SECRET_KEY": "sk_test_fake",
        "STRIPE_WEBHOOK_SECRET": "whsec_fake",
        "MAILJET_API_KEY": "fake_mj_key",
        "MAILJET_SECRET_KEY": "fake_mj_secret",
    }
    monkeypatch.setattr(
        "hr_common.security.secrets.read_secret",
        lambda name, **kwargs: fake.get(name, "fake_secret"),
    )


@pytest.fixture(autouse=True)
def test_settings(settings):
    """Ensure dangerous external integrations are always disabled in tests."""
    settings.STRIPE_LIVE_MODE = False
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
