# hr_payments/providers/mock_stripe.py

import uuid
from typing import Dict, Any

from django.urls import reverse

from hr_shop.models import Order
from .base import PaymentProvider


class MockStripePaymentProvider(PaymentProvider):
    """
    Dumb predictable fake Stripe:
    - Generates a fake checkout session id
    - Immediately marks the order as paid
    - “Redirects” to a local thank-you page
    """

    def create_checkout_session(self, order: Order) -> Dict[str, Any]:
        fake_id = f"cs_test_mock_{uuid.uuid4().hex[:24]}"

        order.stripe_checkout_session_id = fake_id
        order.status = "paid"
        order.save(update_fields=["stripe_checkout_session_id", "status", "updated_at"])

        return {
            "id": fake_id,
            "status": "complete",
            "url": reverse("hr_shop:order_thank_you", args=[order.id]),
        }
