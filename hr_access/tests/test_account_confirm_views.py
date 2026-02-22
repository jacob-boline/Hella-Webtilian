# hr_access/tests/test_account_confirm_views.py

import json

import pytest
from django.urls import reverse

from hr_access.models import User
from hr_access.tokens.account_signup import AccountSignupToken, generate_account_signup_token
from hr_access.tokens.email_change import EmailChangeToken, generate_email_change_token


@pytest.mark.django_db
def test_account_signup_confirm_invalid_token_returns_400(client):
    resp = client.get(reverse("hr_access:account_signup_confirm"), {"t": "bad"})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_signup_confirm_email_mismatch_returns_400(client):
    user = User.objects.create_user(email="user@example.com", username="signupuser", password="StrongPass123!")
    token = generate_account_signup_token(user_id=user.id, email="other@example.com")

    resp = client.get(reverse("hr_access:account_signup_confirm"), {"t": token})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_signup_confirm_user_mismatch_returns_400(client, monkeypatch):
    user = User.objects.create_user(email="user@example.com", username="signupuser", password="StrongPass123!")

    def fake_verify(_raw):
        return AccountSignupToken(user_id=user.id, email=user.email)

    def fake_get_object_or_404(_model, pk):
        other = User.objects.create_user(email="other@example.com", username="otheruser", password="StrongPass123!")
        assert int(pk) == user.id
        return other

    monkeypatch.setattr("hr_access.views.account.verify_account_signup_token", fake_verify)
    monkeypatch.setattr("hr_access.views.account.get_object_or_404", fake_get_object_or_404)

    resp = client.get(reverse("hr_access:account_signup_confirm"), {"t": "anything"})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_signup_confirm_activates_logs_in_and_triggers(client):
    user = User.objects.create_user(
        email="user@example.com",
        username="signupuser",
        password="StrongPass123!",
        is_active=False,
    )
    token = generate_account_signup_token(user_id=user.id, email=user.email)

    resp = client.get(reverse("hr_access:account_signup_confirm"), {"t": token})

    assert resp.status_code == 204
    payload = json.loads(resp["HX-Trigger"])
    assert "accessChanged" in payload
    assert payload["showMessage"]["text"] == "Email confirmed. You are now signed in."

    user.refresh_from_db()
    assert user.is_active is True
    assert str(user.id) == client.session.get("_auth_user_id")


@pytest.mark.django_db
def test_account_change_email_confirm_invalid_token_returns_400(client):
    user = User.objects.create_user(email="old@example.com", username="emailuser", password="StrongPass123!")

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": "bad"})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_change_email_confirm_rejects_inactive_user(client):
    user = User.objects.create_user(
        email="old@example.com",
        username="emailuser",
        password="StrongPass123!",
        is_active=False,
    )
    token = generate_email_change_token(user_id=user.id, new_email="new@example.com")

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": token})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_change_email_confirm_rejects_duplicate_email(client):
    user = User.objects.create_user(email="old@example.com", username="emailuser", password="StrongPass123!")
    User.objects.create_user(email="new@example.com", username="existinguser", password="StrongPass123!")
    token = generate_email_change_token(user_id=user.id, new_email="new@example.com")

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": token})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_change_email_confirm_user_mismatch_returns_400(client):
    user = User.objects.create_user(email="old@example.com", username="emailuser", password="StrongPass123!")
    token = generate_email_change_token(user_id=user.id + 1, new_email="new@example.com")

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": token})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_change_email_confirm_updates_email_and_redirects(client):
    user = User.objects.create_user(email="old@example.com", username="emailuser", password="StrongPass123!")
    token = generate_email_change_token(user_id=user.id, new_email="NEW@Example.com")

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": token})

    assert resp.status_code == 302
    assert "handoff=email_change" in resp["Location"]
    assert "modal_url=" in resp["Location"]

    user.refresh_from_db()
    assert user.email == "new@example.com"


@pytest.mark.django_db
def test_account_change_email_confirm_accepts_token_object_contract(client, monkeypatch):
    user = User.objects.create_user(email="old@example.com", username="emailuser", password="StrongPass123!")

    monkeypatch.setattr(
        "hr_access.views.account.verify_email_change_token",
        lambda _raw: EmailChangeToken(user_id=user.id, email="newobj@example.com"),
    )

    resp = client.get(reverse("hr_access:account_change_email_confirm"), {"u": user.id, "t": "object-token"})

    assert resp.status_code == 302
    user.refresh_from_db()
    assert user.email == "newobj@example.com"
