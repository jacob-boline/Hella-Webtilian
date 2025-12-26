# hr_payment/providers/stripe.py

from __future__ import annotations

from typing import Dict, Any
from decimal import Decimal

from django.conf import settings
from django.urls import reverse

import stripe

from hr_shop.models import Order
from hr_payment.models import PaymentAttempt, PaymentAttemptStatus
from hr_payment.providers.base import PaymentProvider


class StripeEmbeddedCheckoutProvider(PaymentProvider):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_checkout_session(self, order: Order) -> Dict[str, Any]:
        amount_cents = int((order.total or Decimal("0.00")) * 100)
        if amount_cents <= 0:
            raise ValueError("Order total must be > 0 to create a Stripe Checkout session.")

        return_url = settings.SITE_URL + reverse("hr_shop:order_thank_you", args=[order.id])

        attempt = PaymentAttempt.objects.create(
            order=order,
            provider="stripe",
            amount_cents=amount_cents,
            currency="usd",
            status=PaymentAttemptStatus.CREATED,
        )

        session = stripe.checkout.Session.create(
            ui_mode="embedded",
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"Hella Reptilian Order #{order.id}"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "order_id": str(order.id),
                "payment_attempt_id": str(attempt.id),
            },
            return_url=return_url,
        )

        attempt.provider_session_id = session["id"]
        attempt.client_secret = session.get("client_secret")
        attempt.status = PaymentAttemptStatus.PENDING
        attempt.raw = session  # stripe python returns dict-like; JSONField can take it
        attempt.save(update_fields=["provider_session_id", "client_secret", "status", "raw", "updated_at"])

        # convenience pointer on the order
        order.stripe_checkout_session_id = session["id"]
        order.save(update_fields=["stripe_checkout_session_id", "updated_at"])

        return {
            "id": session["id"],
            "status": session.get("status", "open"),
            "client_secret": session.get("client_secret"),
            "url": session.get("url"),
        }
