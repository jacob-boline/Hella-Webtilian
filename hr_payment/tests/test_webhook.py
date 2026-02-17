# hr_payment/tests/test_webhook.py

# Tests for the stripe_webhook view and its downstream handlers.
#
# Strategy:
#   - stripe.Webhook.construct_event is patched in every test — we never
#     hit the real Stripe signature verification. The patch returns a pre-built
#     event dict so we control exactly what the handlers receive.
#   - No other Stripe SDK calls are made by the webhook path, so no other
#     stripe patches are needed here.
#   - All tests use the `db` fixture (via the fixtures in conftest.py), so
#     real DB writes happen and we assert on actual model state.

from unittest.mock import patch

from hr_payment.models import PaymentAttemptStatus, WebhookEvent
from hr_payment.tests.conftest import make_checkout_session_event, make_payment_intent_event
from hr_shop.models import PaymentStatus

WEBHOOK_URL = "/payments/webhooks/stripe/"
CONSTRUCT_EVENT = "stripe.Webhook.construct_event"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def post_webhook(client, payload: dict, signature: str = "t=1,v1=fake_sig"):
    """POST a JSON payload to the webhook endpoint with a fake Stripe signature."""
    import json
    return client.post(
        WEBHOOK_URL,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=signature
    )


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

class TestSignatureVerification:
    def test_invalid_signature_returns_400(self, client, db):
        """
        If Stripe signature verification fails, the view must return 400
        and write nothing to the DB.
        """
        import stripe

        with patch(CONSTRUCT_EVENT, side_effect=stripe.error.SignatureVerificationError("bad sig", "t=1")):
            resp = client.post(
                WEBHOOK_URL,
                data=b'{"id": "evt_bad"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=badsig"
            )

        assert resp.status_code == 400
        assert WebhookEvent.objects.count() == 0

    def test_missing_signature_header_returns_400(self, client, db):
        """No Stripe-Signature header at all should also fail verification."""
        import stripe

        with patch(CONSTRUCT_EVENT, side_effect=stripe.error.SignatureVerificationError("no sig", "")):
            resp = client.post(
                WEBHOOK_URL,
                data=b'{"id": "evt_bad"}',
                content_type="application/json"
            )

        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_duplicate_event_is_ignored(self, client, pending_attempt, checkout_draft):
        """
        A second delivery of the same event_id must short-circuit after the
        first is processed. DB state should not change on the second delivery.
        """
        order = pending_attempt.order
        event = make_checkout_session_event(
            order_id=order.id,
            attempt_id=pending_attempt.id,
            session_id=pending_attempt.provider_session_id
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp1 = post_webhook(client, event)
        assert resp1.status_code == 200

        # Capture state after first delivery
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.PAID

        # Manually flip order back to simulate what a second delivery would
        # incorrectly do if idempotency broke — then confirm it doesn't
        order.payment_status = PaymentStatus.UNPAID
        order.save(update_fields=["payment_status", "updated_at"])

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp2 = post_webhook(client, event)
        assert resp2.status_code == 200

        # Order should still be UNPAID — second webhook was a no-op
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.UNPAID

        # Only one WebhookEvent row, not two
        assert WebhookEvent.objects.filter(event_id=event["id"]).count() == 1

    def test_duplicate_event_already_ok_does_not_reprocess(self, client, pending_attempt, checkout_draft):
        """
        WebhookEvent with ok=True should short-circuit immediately.
        Confirm by checking processed_at doesn't change on second hit.
        """
        from hr_payment.tests.conftest import WebhookEventFactory
        order = pending_attempt.order
        event = make_checkout_session_event(
            order_id=order.id,
            attempt_id=pending_attempt.id,
            session_id=pending_attempt.provider_session_id
        )

        # Pre-seed an already-processed WebhookEvent
        we = WebhookEventFactory(event_id=event["id"], type=event["type"], ok=True)
        original_processed_at = we.processed_at

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200
        we.refresh_from_db()
        assert we.processed_at == original_processed_at


# ---------------------------------------------------------------------------
# checkout.session.completed
# ---------------------------------------------------------------------------

class TestCheckoutSessionCompleted:
    def test_happy_path_marks_order_paid(self, client, pending_attempt, checkout_draft):
        """
        The core success path: order moves to PAID, attempt moves to SUCCEEDED,
        checkout draft is marked used, WebhookEvent is saved with ok=True.
        """
        order = pending_attempt.order
        event = make_checkout_session_event(
            order_id=order.id,
            attempt_id=pending_attempt.id,
            session_id=pending_attempt.provider_session_id,
            payment_intent_id="pi_test_happy"
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200

        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.PAID
        assert order.stripe_payment_intent_id == "pi_test_happy"

        pending_attempt.refresh_from_db()
        assert pending_attempt.status == PaymentAttemptStatus.SUCCEEDED
        assert pending_attempt.finalized_at is not None

        checkout_draft.refresh_from_db()
        assert checkout_draft.used_at is not None

        we = WebhookEvent.objects.get(event_id=event["id"])
        assert we.ok is True
        assert we.error is None
        assert we.processed_at is not None

    def test_attempt_found_by_session_id_fallback(self, client, pending_attempt, checkout_draft):
        """
        _find_attempt_for_session falls back to looking up by provider_session_id
        when payment_attempt_id is absent from metadata.
        """
        order = pending_attempt.order
        event = make_checkout_session_event(
            order_id=order.id,
            attempt_id=pending_attempt.id,
            session_id=pending_attempt.provider_session_id
        )
        # Remove attempt_id from metadata to force the fallback path
        event["data"]["object"]["metadata"].pop("payment_attempt_id")

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200
        pending_attempt.refresh_from_db()
        assert pending_attempt.status == PaymentAttemptStatus.SUCCEEDED

    def test_missing_order_id_in_metadata_is_noop(self, client, db):
        """
        If metadata.order_id is absent the handler should return early without
        raising — the webhook view should still return 200.
        """
        event = make_checkout_session_event(order_id=999, attempt_id=1)
        event["data"]["object"]["metadata"] = {}  # wipe metadata entirely

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200

    def test_webhook_event_saved_with_error_on_processing_exception(self, client, db):
        """
        If _process_stripe_event raises, the WebhookEvent row must be saved
        with ok=False and error populated, and the view must return 500.
        """
        # Use a real-looking event but point at a non-existent order so the
        # handler raises Order.DoesNotExist inside the atomic block.
        event = make_checkout_session_event(order_id=99999, attempt_id=1)

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 500

        we = WebhookEvent.objects.get(event_id=event["id"])
        assert we.ok is False
        assert we.error is not None
        assert we.processed_at is not None


# ---------------------------------------------------------------------------
# checkout.session.expired
# ---------------------------------------------------------------------------

class TestCheckoutSessionExpired:
    def test_expires_pending_attempt(self, client, pending_attempt, checkout_draft):
        """
        An expired session should move the attempt to EXPIRED.
        The order payment_status should NOT change (still PENDING).
        """
        order = pending_attempt.order
        event = make_checkout_session_event(
            event_type="checkout.session.expired",
            event_id="evt_test_expired_001",
            order_id=order.id,
            attempt_id=pending_attempt.id,
            session_id=pending_attempt.provider_session_id,
            status="expired",
            payment_status="unpaid"
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200

        pending_attempt.refresh_from_db()
        assert pending_attempt.status == PaymentAttemptStatus.EXPIRED
        assert pending_attempt.finalized_at is not None

        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.PENDING

    def test_already_succeeded_attempt_is_not_expired(self, client, db):
        """
        An attempt that already SUCCEEDED must not be moved to EXPIRED
        even if an expired event arrives late (e.g. race condition).
        """
        from hr_payment.tests.conftest import PaymentAttemptFactory, OrderFactory
        order = OrderFactory(payment_status=PaymentStatus.PAID)
        attempt = PaymentAttemptFactory(
            order=order,
            status=PaymentAttemptStatus.SUCCEEDED
        )

        event = make_checkout_session_event(
            event_type="checkout.session.expired",
            event_id="evt_test_expired_002",
            order_id=order.id,
            attempt_id=attempt.id,
            session_id=attempt.provider_session_id,
            status="expired",
            payment_status="unpaid"
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200
        attempt.refresh_from_db()
        assert attempt.status == PaymentAttemptStatus.SUCCEEDED  # unchanged


# ---------------------------------------------------------------------------
# payment_intent.payment_failed
# ---------------------------------------------------------------------------

class TestPaymentIntentFailed:
    def test_marks_order_failed_and_attempt_failed(self, client, db):
        """
        A payment_intent.payment_failed event should move the order to FAILED
        and the attempt to FAILED with the error code and message populated.
        """
        from hr_payment.tests.conftest import PaymentAttemptFactory, OrderFactory
        order = OrderFactory(payment_status=PaymentStatus.PENDING)
        attempt = PaymentAttemptFactory(
            order=order,
            status=PaymentAttemptStatus.PENDING,
            provider_payment_intent_id="pi_test_failed_001"
        )

        event = make_payment_intent_event(
            event_type="payment_intent.payment_failed",
            event_id="evt_test_pi_failed_001",
            payment_intent_id="pi_test_failed_001",
            status="requires_payment_method",
            last_payment_error={
                "code": "card_declined",
                "message": "Your card was declined."
            }
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200

        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.FAILED

        attempt.refresh_from_db()
        assert attempt.status == PaymentAttemptStatus.FAILED
        assert attempt.failure_code == "card_declined"
        assert attempt.failure_message == "Your card was declined."
        assert attempt.finalized_at is not None

    def test_already_succeeded_attempt_is_not_failed(self, client, db):
        """
        A succeeded attempt must not be moved to FAILED even if a late
        payment_intent.payment_failed event arrives.
        """
        from hr_payment.tests.conftest import PaymentAttemptFactory, OrderFactory
        order = OrderFactory(payment_status=PaymentStatus.PAID)
        attempt = PaymentAttemptFactory(
            order=order,
            status=PaymentAttemptStatus.SUCCEEDED,
            provider_payment_intent_id="pi_test_race_001"
        )

        event = make_payment_intent_event(
            event_type="payment_intent.payment_failed",
            event_id="evt_test_pi_race_001",
            payment_intent_id="pi_test_race_001",
            status="requires_payment_method"
        )

        with patch(CONSTRUCT_EVENT, return_value=event):
            resp = post_webhook(client, event)

        assert resp.status_code == 200
        attempt.refresh_from_db()
        assert attempt.status == PaymentAttemptStatus.SUCCEEDED  # unchanged
