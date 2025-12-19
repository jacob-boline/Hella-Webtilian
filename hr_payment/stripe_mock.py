# Lightweight Stripe mock used for local/dev testing.
# Provides the subset of the Stripe API that hr_payment.views relies on.
import json
import uuid


class MockSignatureVerificationError(Exception):
    """Mirror of stripe.error.SignatureVerificationError for mocks."""


class _Customers:
    _store = {}

    @classmethod
    def create(cls, email=None, **kwargs):
        customer_id = f"cus_mock_{uuid.uuid4().hex[:24]}"
        data = {"id": customer_id, "email": email}
        cls._store[customer_id] = data
        return data

    @classmethod
    def retrieve(cls, customer_id):
        return cls._store.get(customer_id, {"id": customer_id, "email": None})


class _PaymentIntents:
    @classmethod
    def create(cls, **kwargs):
        intent_id = f"pi_mock_{uuid.uuid4().hex[:24]}"
        return {
            "id": intent_id,
            "status": "succeeded",
            "client_secret": f"{intent_id}_secret",
            "customer": kwargs.get("customer"),
            "metadata": kwargs.get("metadata") or {},
        }


class _CheckoutSessions:
    _sessions = {}

    @classmethod
    def create(cls, **kwargs):
        session_id = f"cs_mock_{uuid.uuid4().hex[:24]}"
        line_items = kwargs.get("line_items") or [{"price": {"id": "price_mock"}}]
        data = {
            "id": session_id,
            "url": kwargs.get("success_url") or kwargs.get("cancel_url") or "/",
            "customer_details": {"email": kwargs.get("customer_email")},
            "line_items": line_items,
        }
        cls._sessions[session_id] = data
        return data

    @classmethod
    def list_line_items(cls, session_id):
        session = cls._sessions.get(session_id, {})
        return {"data": session.get("line_items", [])}


class _CheckoutNamespace:
    Session = _CheckoutSessions


class _Webhook:
    @staticmethod
    def construct_event(payload, sig_header, secret):
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        return json.loads(payload)


class MockStripeClient:
    """
    Minimal, stateful mock that mirrors the Stripe Python client surface
    used by hr_payment.views.
    """

    error = type("error", (), {"SignatureVerificationError": MockSignatureVerificationError})
    Customer = _Customers
    PaymentIntent = _PaymentIntents
    checkout = _CheckoutNamespace()
    Webhook = _Webhook

    def __init__(self):
        # API is attribute-based; no initialization required.
        self.api_key = "mock"
