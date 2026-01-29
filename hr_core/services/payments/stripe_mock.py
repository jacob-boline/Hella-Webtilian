# hr_core/services/payments/stripe_mock.py
import json
import logging
import uuid

from django.urls import reverse

from hr_common.utils.unified_logging import log_event
from .base import CheckoutSession, PaymentGateway

logger = logging.getLogger(__name__)


class MockGateway(PaymentGateway):
    def __init__(self, signer=None):
        self.signer = signer  # optional

    def create_checkout_session(self, *, line_items, success_url, cancel_url, customer_email=None, metadata=None):
        session_id = f"fake_cs_{uuid.uuid4().hex[:24]}"
        # Point to a local “mock checkout” page that imitates Stripe’s redirect
        url = reverse("mock_checkout") + f"?sid={session_id}"
        log_event(logger, logging.INFO, "payments.mock.checkout_session.created", session_id=session_id, has_customer_email=bool(customer_email))
        return CheckoutSession(session_id, url)

    def verify_webhook(self, request):
        # Accept any JSON for dev; or require a local header key
        event = json.loads(request.body.decode("utf-8"))
        log_event(logger, logging.INFO, "payments.mock.webhook.verified", event_id=event.get("id"), event_type=event.get("type"))
        return event
