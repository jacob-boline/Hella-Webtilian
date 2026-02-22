# hr_access/tests/test_orders_claim.py

import json

import pytest
from django.urls import reverse

from hr_access.models import User
from tests.factories import CustomerFactory, OrderFactory


@pytest.mark.django_db
def test_account_submit_claim_unclaimed_orders_missing_email_returns_400(client):
    user = User.objects.create_user(email="has@example.com", username="claimuser", password="StrongPass123!")
    user.email = ""
    user.save(update_fields=["email"])
    client.force_login(user)

    resp = client.post(reverse("hr_access:account_submit_claim_unclaimed_orders"), {"order_ids": ["1"]})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_submit_claim_unclaimed_orders_empty_selection_returns_400(client):
    user = User.objects.create_user(email="claim@example.com", username="claimuser", password="StrongPass123!")
    client.force_login(user)

    resp = client.post(reverse("hr_access:account_submit_claim_unclaimed_orders"), {})

    assert resp.status_code == 400


@pytest.mark.django_db
def test_account_submit_claim_unclaimed_orders_claims_only_eligible_ids(client):
    user = User.objects.create_user(email="claim@example.com", username="claimuser", password="StrongPass123!")
    other_user = User.objects.create_user(email="other@example.com", username="otheruser", password="StrongPass123!")
    customer = CustomerFactory(email="claim@example.com")

    eligible = OrderFactory(customer=customer, email="claim@example.com", user=None)
    wrong_email = OrderFactory(customer=customer, email="other@example.com", user=None)
    already_claimed = OrderFactory(customer=customer, email="claim@example.com", user=other_user)

    client.force_login(user)
    resp = client.post(
        reverse("hr_access:account_submit_claim_unclaimed_orders"),
        {"order_ids": [str(eligible.id), str(wrong_email.id), str(already_claimed.id), "abc"]},
    )

    assert resp.status_code == 204
    payload = json.loads(resp["HX-Trigger"])
    assert payload["unclaimedOrdersClaimed"]["ids"] == [eligible.id]
    assert payload["unclaimedOrdersClaimed"]["count"] == 1

    eligible.refresh_from_db()
    wrong_email.refresh_from_db()
    already_claimed.refresh_from_db()

    assert eligible.user_id == user.id
    assert wrong_email.user_id is None
    assert already_claimed.user_id == other_user.id
    
