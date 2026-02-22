# hr_access/tests/test_auth_backend.py

import pytest

from hr_access.auth_backend import CustomBackend
from hr_access.models import User


@pytest.mark.django_db
def test_auth_backend_authenticates_by_email_case_insensitive():
    user = User.objects.create_user(email="person@example.com", username="personname", password="StrongPass123!")

    out = CustomBackend().authenticate(None, username="PERSON@EXAMPLE.COM", password="StrongPass123!")

    assert out == user


@pytest.mark.django_db
def test_auth_backend_authenticates_by_username_casefold():
    user = User.objects.create_user(email="person2@example.com", username="CaseUser", password="StrongPass123!")

    out = CustomBackend().authenticate(None, username="caseuser", password="StrongPass123!")

    assert out == user


@pytest.mark.django_db
def test_auth_backend_rejects_inactive_user():
    User.objects.create_user(
        email="inactive@example.com",
        username="inactiveuser",
        password="StrongPass123!",
        is_active=False,
    )

    out = CustomBackend().authenticate(None, username="inactive@example.com", password="StrongPass123!")

    assert out is None


@pytest.mark.django_db
def test_auth_backend_missing_credentials_returns_none():
    backend = CustomBackend()

    assert backend.authenticate(None, username=None, password="x") is None
    assert backend.authenticate(None, username="name", password=None) is None
