# hr_core/services/payments/stripe_mock.py
import json, uuid, time
from django.urls import reverse
from .base import PaymentGateway, CheckoutSession


class MockGateway(PaymentGateway):
    def __init__(self, signer=None):
        self.signer = signer  # optional

    def create_checkout_session(self, *, line_items, success_url, cancel_url, customer_email=None, metadata=None):
        session_id = f"fake_cs_{uuid.uuid4().hex[:24]}"
        # Point to a local “mock checkout” page that imitates Stripe’s redirect
        url = reverse("mock_checkout") + f"?sid={session_id}"
        return CheckoutSession(session_id, url)

    def verify_webhook(self, request):
        # Accept any JSON for dev; or require a local header key
        return json.loads(request.body.decode("utf-8"))
