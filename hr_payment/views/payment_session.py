# hr_payment/views/payment_session.py

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.db import transaction
from django.http import JsonResponse

from hr_common.utils.unified_logging import log_event
from hr_core.utils.urls import build_external_absolute_url
from hr_payment.models import PaymentAttempt, PaymentAttemptStatus
from hr_shop.models import Order, PaymentStatus
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token

logger = logging.getLogger(__name__)


def _should_attach_stripe_customer(request) -> bool:
    if getattr(request, "user", None) and request.user.is_authenticated:
        return True
    return request.session.get("wants_saved_info") is True


def _get_or_create_stripe_customer_id(*, customer, email: str) -> str:
    if customer.stripe_customer_id:
        return customer.stripe_customer_id

    stripe_customer = stripe.Customer.create(email=email, name=(customer.full_name or None), metadata={"hr_customer_id": str(customer.id)})

    customer.stripe_customer_id = stripe_customer["id"]
    customer.save(update_fields=["stripe_customer_id", "updated_at"])
    return stripe_customer["id"]


def _stripe_return_url(request, *, token: str) -> str:
    """
    Post-payment return target. We keep it lightweight:
      - land on "/"
      - trigger modal bootstrap via query params
      - token is used server-side to look up order
    """
    return build_external_absolute_url(
        request, "/", query={"handoff": "order_payment_result", "modal": "order_payment_result", "t": token}
    ) + "#parallax-section-shows"


def _stripe_session_raw_snapshot(sess: dict) -> dict:
    """Extract the fields we persist from a Stripe session object."""
    return {
        "id":             sess["id"],
        "livemode":       sess["livemode"],
        "amount_total":   sess["amount_total"],
        "currency":       sess["currency"],
        "status":         sess["status"],
        "payment_status": sess["payment_status"],
        "expires_at":     sess["expires_at"],
        "customer_email": sess["customer_email"],
        "ui_mode":        sess["ui_mode"],
        "return_url":     sess["return_url"],
    }


def _build_stripe_session_kwargs(*, order: Order, attempt: PaymentAttempt,
                                 amount_cents: int, return_url: str,
                                 attach_customer: bool) -> dict:
    kwargs = {
        "ui_mode": "embedded",
        "mode": "payment",
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Hella Reptilian Order #{order.id}"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        "metadata": {
            "order_id": str(order.id),
            "payment_attempt_id": str(attempt.id),
        },
        "payment_intent_data": {
            "metadata": {
                "order_id": str(order.id),
                "payment_attempt_id": str(attempt.id)
            }
        },
        "return_url": return_url
    }

    if attach_customer:
        stripe_customer_id = _get_or_create_stripe_customer_id(
            customer=order.customer, email=order.email
        )
        kwargs["customer"] = stripe_customer_id
        kwargs["customer_update"] = {"address": "auto", "shipping": "auto"}
    else:
        kwargs["customer_email"] = order.email

    return kwargs


def _try_reuse_stripe_session(order: Order) -> JsonResponse | None:
    """
    If there's an existing open Stripe session for this order, refresh it in the
    DB and return a clientSecret response. Returns None if no reusable session exists.
    """
    existing_attempt = (
        PaymentAttempt.objects
        .filter(order=order, status__in=[PaymentAttemptStatus.CREATED, PaymentAttemptStatus.PENDING])
        .order_by("-created_at")
        .first()
    )

    if not existing_attempt or not existing_attempt.provider_session_id:
        return None

    try:
        sess = stripe.checkout.Session.retrieve(existing_attempt.provider_session_id)
    except stripe.error.StripeError as exc:
        log_event(logger, logging.WARNING, "payment.checkout.session_reuse_failed",
                  order_id=order.id, session_id=existing_attempt.provider_session_id, error=str(exc))
        return None

    if not (sess and sess.get("status") == "open" and sess.get("client_secret")):
        return None

    dirty = False
    if existing_attempt.client_secret != sess.get("client_secret"):
        existing_attempt.client_secret = sess.get("client_secret")
        dirty = True
    if existing_attempt.status != PaymentAttemptStatus.PENDING:
        existing_attempt.status = PaymentAttemptStatus.PENDING
        dirty = True

    existing_attempt.raw = _stripe_session_raw_snapshot(sess)
    if dirty:
        existing_attempt.save(update_fields=["client_secret", "raw", "status", "updated_at"])

    log_event(logger, logging.INFO, "payment.checkout.session_reused",
              order_id=order.id, session_id=existing_attempt.provider_session_id)

    return JsonResponse({"clientSecret": sess["client_secret"], "sessionId": sess["id"]})


def _create_stripe_session(request, order: Order) -> JsonResponse:
    """
    Creates a new PaymentAttempt and Stripe Checkout session atomically.
    """
    amount_cents = int(
        (order.total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    attach_customer = _should_attach_stripe_customer(request)

    with transaction.atomic():
        attempt = PaymentAttempt.objects.create(
            order=order,
            provider="stripe",
            status=PaymentAttemptStatus.CREATED,
            amount_cents=amount_cents,
            currency="usd",
        )

        receipt_token = generate_order_receipt_token(order_id=order.id, email=order.email or "")
        return_url = _stripe_return_url(request, token=receipt_token)

        session_kwargs = _build_stripe_session_kwargs(
            order=order, attempt=attempt, amount_cents=amount_cents,
            return_url=return_url, attach_customer=attach_customer
        )

        try:
            sess = stripe.checkout.Session.create(**session_kwargs)
        except stripe.error.StripeError as exc:
            log_event(logger, logging.ERROR, "payment.checkout.session_create_failed",
                      order_id=order.id, attempt_id=attempt.id, attach_customer=attach_customer,
                      error=str(exc), error_type=type(exc).__name__,
                      customer_id=getattr(order, "customer_id", None))
            return JsonResponse({"error": "Payment session could not be created."}, status=500)

        attempt.provider_session_id = sess.get("id")
        attempt.client_secret = sess.get("client_secret")
        attempt.raw = _stripe_session_raw_snapshot(sess)
        attempt.status = PaymentAttemptStatus.PENDING
        attempt.save(update_fields=["provider_session_id", "client_secret", "raw", "status", "updated_at"])

        order.stripe_checkout_session_id = sess.get("id")
        if order.payment_status != PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.PENDING
        order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

    log_event(logger, logging.INFO, "payment.checkout.session_created",
              order_id=order.id, attempt_id=attempt.id,
              session_id=sess.get("id"), attach_customer=attach_customer)

    return JsonResponse({"clientSecret": sess.get("client_secret"), "sessionId": sess.get("id"), "reused": False})
