# hr_access/tests/test_post_purchase.py

import pytest
from django.urls import reverse

from hr_access.models import User
from hr_access.services.post_purchase import build_post_purchase_form, create_post_purchase_account
from tests.factories import CustomerFactory, OrderFactory


@pytest.mark.django_db
def test_build_post_purchase_form_locks_email():
    order = OrderFactory(email="buyer@example.com")

    form = build_post_purchase_form(order, {"email": "wrong@example.com", "username": "freshuser", "password": "StrongPass123!"})

    assert form.is_valid() is True
    assert form.cleaned_data["email"] == "buyer@example.com"


@pytest.mark.django_db
def test_create_post_purchase_account_links_order_and_customer_and_returns_other_orders():
    customer = CustomerFactory(email="buyer@example.com", user=None)
    order = OrderFactory(customer=customer, email="buyer@example.com", user=None)
    other = OrderFactory(customer=customer, email="buyer@example.com", user=None)

    result = create_post_purchase_account(
        order,
        {"email": "buyer@example.com", "username": "freshuser", "password": "StrongPass123!"},
    )

    assert result is not None
    user, other_orders = result
    assert isinstance(user, User)
    assert [o.id for o in other_orders] == [other.id]

    order.refresh_from_db()
    customer.refresh_from_db()
    assert order.user_id == user.id
    assert customer.user_id == user.id


@pytest.mark.django_db
def test_create_post_purchase_account_returns_none_for_invalid_form():
    order = OrderFactory(email="buyer@example.com", user=None)

    result = create_post_purchase_account(order, {"email": "buyer@example.com", "username": "x", "password": "short"})

    assert result is None


@pytest.mark.django_db
def test_account_submit_post_purchase_claim_orders_requires_auth(client):
    order = OrderFactory(email="guest@example.com", user=None)

    resp = client.post(reverse("hr_access:account_submit_post_purchase_claim_orders", args=[order.id]))

    assert resp.status_code == 401


@pytest.mark.django_db
def test_account_submit_post_purchase_claim_orders_rejects_email_mismatch(client):
    user = User.objects.create_user(email="owner@example.com", username="owneruser", password="StrongPass123!")
    order = OrderFactory(email="guest@example.com", user=None)
    client.force_login(user)

    resp = client.post(reverse("hr_access:account_submit_post_purchase_claim_orders", args=[order.id]))

    assert resp.status_code == 403


@pytest.mark.django_db
def test_account_submit_post_purchase_claim_orders_renders_unclaimed_orders_for_matching_email(client):
    user = User.objects.create_user(email="guest@example.com", username="owneruser", password="StrongPass123!")
    base_customer = CustomerFactory(email="guest@example.com", user=None)
    order = OrderFactory(customer=base_customer, email="guest@example.com", user=None)
    unclaimed = OrderFactory(customer=base_customer, email="guest@example.com", user=None)

    client.force_login(user)
    resp = client.post(reverse("hr_access:account_submit_post_purchase_claim_orders", args=[order.id]))

    assert resp.status_code == 200
    assert str(unclaimed.id) in resp.content.decode("utf-8")


@pytest.mark.django_db
def test_account_submit_post_purchase_create_account_logs_in_and_returns_success_fragment(client):
    customer = CustomerFactory(email="buyer@example.com", user=None)
    order = OrderFactory(customer=customer, email="buyer@example.com", user=None)

    resp = client.post(
        reverse("hr_access:account_submit_post_purchase_create_account", args=[order.id]),
        {"email": "buyer@example.com", "username": "newbuyer", "password": "StrongPass123!"},
    )

    assert resp.status_code == 200
    order.refresh_from_db()
    assert order.user_id is not None
    
