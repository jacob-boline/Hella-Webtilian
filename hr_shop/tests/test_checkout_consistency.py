from datetime import timedelta
from importlib import import_module

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from hr_shop.models import CheckoutDraft, Customer, Order, PaymentStatus
from hr_shop.views.checkout_helpers import _get_or_create_active_draft, _get_or_create_customer
from tests.factories import AddressFactory, CustomerFactory

normalize_shop_text_fields = import_module("hr_shop.migrations.0003_normalize_notes_and_stripe_ids").normalize_shop_text_fields


@pytest.mark.django_db
def test_order_empty_note_stores_empty_string():
    customer = CustomerFactory()
    order = Order.objects.create(
        customer=customer,
        email=customer.email,
        total="0.00",
        payment_status=PaymentStatus.UNPAID,
        note="",
    )

    order.refresh_from_db()
    assert order.note == ""


@pytest.mark.django_db
def test_checkout_draft_empty_note_stores_and_reuses_empty_string():
    customer = CustomerFactory()
    address = AddressFactory()

    draft = CheckoutDraft.objects.create(
        customer=customer,
        email=customer.email,
        address=address,
        cart=[],
        expires_at=timezone.now() + timedelta(hours=1),
    )
    draft.refresh_from_db()
    assert draft.note == ""

    updated = _get_or_create_active_draft(
        customer=customer,
        email=customer.email,
        address=address,
        note=None,
        cart_payload=[],
    )
    updated.refresh_from_db()
    assert updated.note == ""


@pytest.mark.django_db
def test_migration_normalizes_empty_stripe_ids_to_null():
    c = CustomerFactory(stripe_customer_id="")
    o = Order.objects.create(
        customer=c,
        email=c.email,
        total="0.00",
        payment_status=PaymentStatus.UNPAID,
        stripe_checkout_session_id="",
        stripe_payment_intent_id="",
    )

    normalize_shop_text_fields(apps=apps, schema_editor=None)

    c.refresh_from_db()
    o.refresh_from_db()
    assert c.stripe_customer_id is None
    assert o.stripe_checkout_session_id is None
    assert o.stripe_payment_intent_id is None


@pytest.mark.django_db
def test_stripe_customer_id_unique_only_when_non_null():
    Customer.objects.create(email="a@example.com")
    Customer.objects.create(email="b@example.com")

    Customer.objects.create(email="c@example.com", stripe_customer_id="cus_123")
    with pytest.raises(IntegrityError):
        Customer.objects.create(email="d@example.com", stripe_customer_id="cus_123")


@pytest.mark.django_db
def test_get_or_create_customer_uses_empty_strings_for_middle_and_suffix():
    User = get_user_model()
    user = User.objects.create_user(username="checkout-user", email="checkout@example.com", password="x")

    class DummyForm:
        cleaned_data = {
            "first_name": "Test",
            "middle_initial": "",
            "last_name": "Customer",
            "suffix": "",
            "phone": "",
            "wants_saved_info": False,
        }

    customer = _get_or_create_customer("checkout@example.com", user, DummyForm())

    assert customer.middle_initial == ""
    assert customer.suffix == ""
