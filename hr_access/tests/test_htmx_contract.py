# hr_access/tests/test_htmx_contract.py

import json

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from hr_access.models import User
from hr_common.utils.htmx_responses import csrf_failure


def _hx(resp):
    return json.loads(resp["HX-Trigger"])


def test_hx_login_required_uses_trigger_contract(client):
    resp = client.get("/user/account/settings/", HTTP_HX_REQUEST="true")

    assert resp.status_code == 401
    payload = _hx(resp)
    assert payload["closeModal"] is None
    assert payload["authRequired"]["open_drawer"] is True
    assert payload["authRequired"]["focus"] == "#id_username"


def test_account_signup_confirm_invalid_token_returns_hx_message(client):
    resp = client.get("/user/account_signup/confirm/?t=invalid-token", HTTP_HX_REQUEST="true")

    assert resp.status_code == 400
    payload = _hx(resp)
    assert payload["closeModal"] is None
    assert payload["showMessage"]["text"] == "Invalid or expired confirmation link."


def test_account_email_change_confirm_invalid_token_returns_hx_message(client, db):
    user = User.objects.create_user(email="u1@example.com", username="user01", password="x")

    resp = client.get(
        f"/user/account/email/change/confirm/?u={user.id}&t=invalid-token",
        HTTP_HX_REQUEST="true",
    )

    assert resp.status_code == 400
    payload = _hx(resp)
    assert payload["closeModal"] is None
    assert payload["showMessage"]["text"] == "Invalid or expired confirmation link."


def test_csrf_failure_session_expired_payload_uses_show_message_shape():
    rf = RequestFactory()
    request = rf.post("/user/login/", HTTP_HX_REQUEST="true")
    request.user = AnonymousUser()
    request.COOKIES["sessionid"] = "expired-session-id"

    resp = csrf_failure(request, reason="bad csrf")

    assert resp.status_code == 403
    payload = _hx(resp)
    assert payload["closeModal"] is None
    assert payload["showMessage"]["text"] == "Your session expired. Please sign in again."
    assert payload["authRequired"]["open_drawer"] is True
