# hr_payment/providers/mock_stripe.py

import uuid
from typing import Dict, Any
from django.urls import reverse

from hr_shop.models import Order, PaymentStatus
from hr_payment.models import PaymentAttempt, PaymentAttemptStatus
from .base import PaymentProvider


class MockStripePaymentProvider(PaymentProvider):
    def create_checkout_session(self, order: Order) -> Dict[str, Any]:
        fake_id = f"cs_test_mock_{uuid.uuid4().hex[:24]}"

        amount_cents = int((order.total or 0) * 100)

        attempt = PaymentAttempt.objects.create(
            order=order,
            provider="mock_stripe",
            amount_cents=amount_cents,
            currency="usd",
            provider_session_id=fake_id,
            raw={"mock": True, "session_id": fake_id},
        )
        attempt.mark_final(PaymentAttemptStatus.SUCCEEDED)

        # pretend webhook: mark paid
        order.stripe_checkout_session_id = fake_id
        order.payment_status = PaymentStatus.PAID
        order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

        return {
            "id": fake_id,
            "status": "complete",
            "client_secret": "cs_mock_secret",
            "url": reverse("hr_shop:order_thank_you", args=[order.id]),
        }
