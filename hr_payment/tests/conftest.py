# hr_payment/tests/conftest.py

# Fixtures scoped to the payment app.
# Cross-cutting model factories (Customer, Order, Address, etc.) live in
# tests/factories.py at the project root — import from there, don't redefine.

from datetime import timedelta

import factory
import pytest
from django.utils import timezone

from hr_payment.models import PaymentAttempt, PaymentAttemptStatus, WebhookEvent
from hr_shop.models import PaymentStatus
from tests.factories import CheckoutDraftFactory, CustomerFactory, OrderFactory

# Re-export for other tests in app
__all__ = [
    "CustomerFactory",
    "OrderFactory",
    "CheckoutDraftFactory",
    "PaymentAttemptFactory",
    "WebhookEventFactory"
]


# ---------------------------------------------------------------------------
# Payment-specific factories
# ---------------------------------------------------------------------------

class PaymentAttemptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentAttempt

    order = factory.SubFactory(OrderFactory)
    provider = "stripe"
    status = PaymentAttemptStatus.PENDING
    amount_cents = 2999
    currency = "usd"
    provider_session_id = factory.Sequence(lambda n: f"cs_test_fake_{n}")
    client_secret = factory.Sequence(lambda n: f"cs_test_fake_{n}_secret_abc123")


class WebhookEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEvent

    event_id = factory.Sequence(lambda n: f"evt_test_{n:06d}")
    type = "checkout.session.completed"
    payload = factory.LazyFunction(dict)
    ok = False


# ---------------------------------------------------------------------------
# Stripe event payload builders
#
# Plain functions, not fixtures — call them directly in tests with whatever
# arguments each test needs. See test_webhook_notes.md for why.
# ---------------------------------------------------------------------------

def make_checkout_session_event(
    *,
    event_type="checkout.session.completed",
    event_id="evt_test_session_001",
    session_id="cs_test_abc123",
    payment_intent_id="pi_test_abc123",
    order_id: int,
    attempt_id: int,
    payment_status="paid",
    status="complete",
    amount_total=2999,
    customer_email="customer@example.com",
    livemode=False
) -> dict:
    """Build a checkout.session.completed or .expired event payload."""
    return {
        "id": event_id,
        "type": event_type,
        "data": {
            "object": {
                "id": session_id,
                "object": "checkout.session",
                "livemode": livemode,
                "status": status,
                "payment_status": payment_status,
                "payment_intent": payment_intent_id,
                "amount_total": amount_total,
                "currency": "usd",
                "customer_email": customer_email,
                "ui_mode": "embedded",
                "return_url": "https://example.com/?handoff=order_payment_result",
                "expires_at": int((timezone.now() + timedelta(hours=1)).timestamp()),
                "metadata": {
                    "order_id": str(order_id),
                    "payment_attempt_id": str(attempt_id)
                }
            }
        }
    }


def make_payment_intent_event(
    *,
    event_type="payment_intent.payment_failed",
    event_id="evt_test_pi_001",
    payment_intent_id="pi_test_abc123",
    status="requires_payment_method",
    amount=2999,
    livemode=False,
    last_payment_error: dict | None = None
) -> dict:
    """Build a payment_intent.* event payload."""
    obj = {
        "id": payment_intent_id,
        "object": "payment_intent",
        "livemode": livemode,
        "status": status,
        "amount": amount,
        "currency": "usd"
    }
    if last_payment_error is not None:
        obj["last_payment_error"] = last_payment_error

    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": obj}
    }


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def unpaid_order(db):
    """An order in UNPAID state, ready to enter the payment flow."""
    return OrderFactory(payment_status=PaymentStatus.UNPAID)


@pytest.fixture
def pending_attempt(db, unpaid_order):
    """A PENDING PaymentAttempt tied to unpaid_order, as if a session was just created."""
    attempt = PaymentAttemptFactory(order=unpaid_order)
    unpaid_order.stripe_checkout_session_id = attempt.provider_session_id
    unpaid_order.payment_status = PaymentStatus.PENDING
    unpaid_order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])
    return attempt


@pytest.fixture
def checkout_draft(db, unpaid_order):
    """An active CheckoutDraft linked to unpaid_order's customer."""
    return CheckoutDraftFactory(
        customer=unpaid_order.customer,
        email=unpaid_order.email,
        order=unpaid_order
    )


@pytest.fixture
def customer(db):
    return CustomerFactory()


@pytest.fixture
def webhook_client(client):
    """
    Django test client pre-configured for webhook POST requests.
    Stripe webhooks are csrf_exempt, raw body, no session cookie needed.
    """
    import json

    def post_webhook(payload: dict, signature: str = "t=1,v1=fake_sig"):
        return client.post(
            "/payments/webhooks/stripe/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature
        )
    return post_webhook
