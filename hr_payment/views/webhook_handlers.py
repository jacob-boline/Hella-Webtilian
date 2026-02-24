# hr_payment/views/webhook_handlers.py

from __future__ import annotations

import logging

from hr_common.utils.unified_logging import log_event
from hr_payment.models import PaymentAttempt, PaymentAttemptStatus
from hr_payment.services.payment_state import mark_checkout_draft_used
from hr_payment.views.payment_session import _stripe_session_raw_snapshot
from hr_shop.models import Order, PaymentStatus
from hr_shop.services.order_receipt import send_order_receipt_email

logger = logging.getLogger(__name__)


def _send_initial_receipt_email(order: Order) -> None:
    if not order.email:
        log_event(logger, logging.WARNING, "payment.receipt.skipped_missing_email", order_id=order.id)
        return

    log_event(logger, logging.INFO, "payment.receipt.initial_email_attempt", order_id=order.id, email=order.email)

    try:
        send_order_receipt_email(order=order, request=None)
        log_event(logger, logging.INFO, "payment.receipt.sent", order_id=order.id, email=order.email)
    except Exception as exc:
        log_event(logger, logging.ERROR, "payment.receipt.send_failed",
            order_id=order.id, email=order.email, error=str(exc), exc_info=True,
        )


def _find_attempt_for_session(session: dict) -> PaymentAttempt | None:
    metadata = session.get("metadata") or {}
    attempt_id = metadata.get("payment_attempt_id")

    if attempt_id:
        a = PaymentAttempt.objects.select_for_update().filter(pk=int(attempt_id)).first()
        if a:
            return a

    sid = session.get("id")
    if sid:
        return PaymentAttempt.objects.select_for_update().filter(provider_session_id=sid).first()

    return None


def _handle_checkout_session_completed(session: dict) -> None:
    metadata = session.get("metadata") or {}
    order_id = metadata.get("order_id")

    if not order_id:
        return

    order = Order.objects.select_for_update().get(pk=int(order_id))
    was_paid = order.payment_status == PaymentStatus.PAID
    sid = session.get("id")
    pi = session.get("payment_intent")

    if sid:
        order.stripe_checkout_session_id = sid
    if pi:
        order.stripe_payment_intent_id = pi

    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=["stripe_checkout_session_id", "stripe_payment_intent_id", "payment_status", "updated_at"])
    mark_checkout_draft_used(order.id)

    if not was_paid:
        _send_initial_receipt_email(order)

    attempt = _find_attempt_for_session(session)
    if attempt:
        if sid:
            attempt.provider_session_id = sid
        if pi:
            attempt.provider_payment_intent_id = pi

        attempt.client_secret = session.get("client_secret") or attempt.client_secret
        attempt.raw = _stripe_session_raw_snapshot(session)
        attempt.save(update_fields=["provider_session_id", "provider_payment_intent_id", "client_secret", "raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.SUCCEEDED)


def _handle_checkout_session_expired(session: dict) -> None:
    attempt = _find_attempt_for_session(session)
    if attempt and attempt.status not in (PaymentAttemptStatus.SUCCEEDED, PaymentAttemptStatus.FAILED):
        attempt.raw = _stripe_session_raw_snapshot(session)
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.EXPIRED)


def _handle_payment_intent_succeeded(pi: dict) -> None:
    pid = pi.get("id")
    if not pid:
        return

    attempt = PaymentAttempt.objects.select_for_update().filter(provider_payment_intent_id=pid).first()
    order = attempt.order if attempt else Order.objects.select_for_update().filter(stripe_payment_intent_id=pid).first()
    if not order:
        return

    was_paid = order.payment_status == PaymentStatus.PAID

    order.stripe_payment_intent_id = pid
    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=["stripe_payment_intent_id", "payment_status", "updated_at"])
    mark_checkout_draft_used(order.id)

    if not was_paid:
        _send_initial_receipt_email(order)

    if attempt and attempt.status != PaymentAttemptStatus.SUCCEEDED:
        attempt.raw = {
            "id":       pi.get("id"),
            "livemode": pi.get("livemode"),
            "amount":   pi.get("amount"),
            "currency": pi.get("currency"),
            "status":   pi.get("status")
        }
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.SUCCEEDED)


def _handle_charge_succeeded(charge: dict) -> None:
    payment_intent_id = charge.get("payment_intent")
    if not payment_intent_id:
        return

    _handle_payment_intent_succeeded({
        "id": payment_intent_id,
        "livemode": charge.get("livemode"),
        "amount": charge.get("amount"),
        "currency": charge.get("currency"),
        "status": charge.get("status")
    })


def _handle_payment_intent_failed(pi: dict) -> None:
    pid = pi.get("id")
    if not pid:
        return

    attempt = PaymentAttempt.objects.select_for_update().filter(provider_payment_intent_id=pid).first()
    order = attempt.order if attempt \
        else Order.objects.select_for_update().filter(stripe_payment_intent_id=pid).first()
    if not order:
        return

    order.stripe_payment_intent_id = pid
    order.payment_status = PaymentStatus.FAILED
    order.save(update_fields=["stripe_payment_intent_id", "payment_status", "updated_at"])

    if attempt and attempt.status != PaymentAttemptStatus.SUCCEEDED:
        last_err = pi.get("last_payment_error") or {}
        attempt.raw = {
            "id":                 pi.get("id"),
            "livemode":           pi.get("livemode"),
            "amount":             pi.get("amount"),
            "currency":           pi.get("currency"),
            "status":             pi.get("status"),
            "last_payment_error": pi.get("last_payment_error")
        }
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.FAILED, code=(last_err.get("code") or None), msg=(last_err.get("message") or None))


def _handle_payment_intent_canceled(pi: dict) -> None:
    pid = pi.get("id")
    if not pid:
        return

    attempt = PaymentAttempt.objects.select_for_update().filter(provider_payment_intent_id=pid).first()
    order = attempt.order if attempt else Order.objects.select_for_update().filter(stripe_payment_intent_id=pid).first()
    if not order:
        return

    # Canceled is "not paid", but not "failed" either.
    if order.payment_status != PaymentStatus.PAID:
        order.payment_status = PaymentStatus.UNPAID
        order.save(update_fields=["payment_status", "updated_at"])

    if attempt and attempt.status not in (PaymentAttemptStatus.SUCCEEDED, PaymentAttemptStatus.FAILED):
        attempt.raw = {
            "id":       pi.get("id"),
            "livemode": pi.get("livemode"),
            "amount":   pi.get("amount"),
            "currency": pi.get("currency"),
            "status":   pi.get("status")
        }
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.CANCELED)


def _process_stripe_event(event: dict) -> None:
    etype = event.get("type")
    data_obj = (event.get("data") or {}).get("object") or {}

    _EVENT_HANDLERS = {
        "checkout.session.completed":    _handle_checkout_session_completed,
        "checkout.session.expired":      _handle_checkout_session_expired,
        "payment_intent.succeeded":      _handle_payment_intent_succeeded,
        "payment_intent.payment_failed": _handle_payment_intent_failed,
        "payment_intent.canceled":       _handle_payment_intent_canceled,
        "charge.succeeded":              _handle_charge_succeeded
    }

    handler = _EVENT_HANDLERS.get(etype)
    if handler:
        log_event(logger, logging.INFO, "payment.webhook.event_handled", event_type=etype)
        handler(data_obj)
    else:
        log_event(logger, logging.INFO, "payment.webhook.event_ignored", event_type=etype)
