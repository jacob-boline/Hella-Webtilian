# hr_payment/views.py
#
# NOTE: This is your “single provider” Stripe-only views.py as pasted,
# with one targeted improvement:
# - amount_cents uses Decimal-safe quantization to avoid rounding edge cases.
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from hr_payment.models import PaymentAttempt, PaymentAttemptStatus
from hr_payment.models import WebhookEvent
from hr_shop.models import Order, PaymentStatus
from hr_shop.utils.receipts import make_order_receipt_token


def _make_order_receipt_token(order: Order) -> str:
    return make_order_receipt_token(order_id=order.id, email=order.email)


@require_POST
def checkout_stripe_session(request, order_id: int):
    """
    Called by JS to get a client secret for Embedded Checkout.

    Idempotent:
      - If an existing open session exists for this order, reuse it.
      - Otherwise create a new PaymentAttempt and a new embedded Checkout session.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    order = get_object_or_404(Order, pk=order_id)

    if order.payment_status == PaymentStatus.PAID:
        return JsonResponse({"error": "Order already paid."}, status=409)

    if not order.total or order.total <= 0:
        return JsonResponse({"error": "Order total must be > 0."}, status=400)

    # 1) Reuse existing open session from the latest non-final attempt if possible
    existing_attempt = (
        PaymentAttempt.objects
        .filter(order=order, status__in=[PaymentAttemptStatus.CREATED, PaymentAttemptStatus.PENDING])
        .order_by("-created_at")
        .first()
    )

    if existing_attempt and existing_attempt.provider_session_id:
        try:
            sess = stripe.checkout.Session.retrieve(existing_attempt.provider_session_id)
            if sess and sess.get("status") == "open" and sess.get("client_secret"):
                if existing_attempt.client_secret != sess.get("client_secret"):
                    existing_attempt.client_secret = sess.get("client_secret")
                    existing_attempt.raw = sess
                    existing_attempt.status = PaymentAttemptStatus.PENDING
                    existing_attempt.save(update_fields=["client_secret", "raw", "status", "updated_at"])

                if order.stripe_checkout_session_id != sess.get("id"):
                    order.stripe_checkout_session_id = sess.get("id")
                    if order.payment_status != PaymentStatus.PENDING:
                        order.payment_status = PaymentStatus.PENDING
                    order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

                return JsonResponse({
                    "clientSecret": sess["client_secret"],
                    "sessionId": sess["id"],
                    "reused": True,
                })
        except Exception:
            pass

    # 2) Create a new attempt + session (atomic so attempt exists for webhook mapping)
    amount_cents = int((order.total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    attach_customer = False
    if getattr(request, "user", None) and request.user.is_authenticated:
        attach_customer = True
    if request.session.get("wants_saved_info") is True:
        attach_customer = True

    with transaction.atomic():
        attempt = PaymentAttempt.objects.create(
            order=order,
            provider="stripe",
            status=PaymentAttemptStatus.CREATED,
            amount_cents=amount_cents,
            currency="usd",
        )

        # quote token for URL-escaped characters
        token = quote(_make_order_receipt_token(order))
        # token passed back from stripe payment endpoint and used to look up order and open thank you page
        return_url = (
            settings.SITE_URL +
            f"/?modal=order_payment_result&order_id={order.id}&t={token}" +
            "#parallax-section-shows"
        )

        session_kwargs = {
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
            "return_url": return_url,
        }

        if attach_customer:
            stripe_customer_id = _get_or_create_stripe_customer_id(customer=order.customer, email=order.email)
            session_kwargs["customer"] = stripe_customer_id
            session_kwargs["customer_update"] = {"address": "auto", "shipping": "auto"}
        else:
            session_kwargs["customer_email"] = order.email

        sess = stripe.checkout.Session.create(**session_kwargs)

        attempt.provider_session_id = sess.get("id")
        attempt.client_secret = sess.get("client_secret")
        attempt.raw = sess
        attempt.status = PaymentAttemptStatus.PENDING
        attempt.save(update_fields=["provider_session_id", "client_secret", "raw", "status", "updated_at"])

        order.stripe_checkout_session_id = sess.get("id")
        if order.payment_status != PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.PENDING
        order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

        return JsonResponse({
            "clientSecret": sess.get("client_secret"),
            "sessionId": sess.get("id"),
            "reused": False,
        })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        return HttpResponse(status=400)

    # idempotency/audit
    obj, created = WebhookEvent.objects.get_or_create(
        event_id=event["id"],
        defaults={
            "type":    event.get("type", ""),
            "payload": event,
        },
    )
    if not created and obj.ok:
        return HttpResponse(status=200)

    try:
        with transaction.atomic():
            _process_stripe_event(event)

        obj.ok = True
        obj.processed_at = timezone.now()
        obj.error = None
        obj.save(update_fields=["ok", "processed_at", "error"])
    except Exception as e:
        obj.ok = False
        obj.processed_at = timezone.now()
        obj.error = str(e)
        obj.save(update_fields=["ok", "processed_at", "error"])
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def _get_or_create_stripe_customer_id(*, customer, email: str) -> str:
    if customer.stripe_customer_id:
        return customer.stripe_customer_id

    stripe_customer = stripe.Customer.create(
        email=email,
        name=(customer.full_name or None),
        metadata={'hr_customer_id': str(customer.id)}
    )

    customer.stripe_customer_id = stripe_customer['id']
    customer.save(update_fields=['stripe_customer_id', 'updated_at'])
    return stripe_customer['id']


def _process_stripe_event(event: dict) -> None:
    etype = event.get("type")
    data_obj = (event.get("data") or {}).get("object") or {}

    if etype == "checkout.session.completed":
        _handle_checkout_session_completed(data_obj)
        return

    if etype == "checkout.session.expired":
        _handle_checkout_session_expired(data_obj)
        return

    if etype == "payment_intent.succeeded":
        _handle_payment_intent_succeeded(data_obj)
        return

    if etype == "payment_intent.payment_failed":
        _handle_payment_intent_failed(data_obj)
        return

    if etype == "payment_intent.canceled":
        _handle_payment_intent_canceled(data_obj)
        return

    # ignore others for now


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

    sid = session.get("id")
    pi = session.get("payment_intent")

    if sid:
        order.stripe_checkout_session_id = sid
    if pi:
        order.stripe_payment_intent_id = pi

    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=[
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "payment_status",
        "updated_at",
    ])

    attempt = _find_attempt_for_session(session)
    if attempt:
        if sid:
            attempt.provider_session_id = sid
        if pi:
            attempt.provider_payment_intent_id = pi
        attempt.client_secret = session.get("client_secret") or attempt.client_secret
        attempt.raw = session
        attempt.save(update_fields=["provider_session_id", "provider_payment_intent_id", "client_secret", "raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.SUCCEEDED)


def _handle_checkout_session_expired(session: dict) -> None:
    attempt = _find_attempt_for_session(session)
    if attempt and attempt.status not in (PaymentAttemptStatus.SUCCEEDED, PaymentAttemptStatus.FAILED):
        attempt.raw = session
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.EXPIRED)
    # Do NOT update order.payment_status here.


def _handle_payment_intent_succeeded(pi: dict) -> None:
    pid = pi.get("id")
    if not pid:
        return

    attempt = PaymentAttempt.objects.select_for_update().filter(provider_payment_intent_id=pid).first()
    order = attempt.order if attempt else Order.objects.select_for_update().filter(stripe_payment_intent_id=pid).first()
    if not order:
        return

    order.stripe_payment_intent_id = pid
    order.payment_status = PaymentStatus.PAID
    order.save(update_fields=["stripe_payment_intent_id", "payment_status", "updated_at"])

    if attempt and attempt.status != PaymentAttemptStatus.SUCCEEDED:
        attempt.raw = pi
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.SUCCEEDED)


def _handle_payment_intent_failed(pi: dict) -> None:
    pid = pi.get("id")
    if not pid:
        return

    attempt = PaymentAttempt.objects.select_for_update().filter(provider_payment_intent_id=pid).first()
    order = attempt.order if attempt else Order.objects.select_for_update().filter(stripe_payment_intent_id=pid).first()
    if not order:
        return

    order.stripe_payment_intent_id = pid
    order.payment_status = PaymentStatus.FAILED
    order.save(update_fields=["stripe_payment_intent_id", "payment_status", "updated_at"])

    if attempt and attempt.status != PaymentAttemptStatus.SUCCEEDED:
        last_err = pi.get("last_payment_error") or {}
        attempt.raw = pi
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(
            PaymentAttemptStatus.FAILED,
            code=(last_err.get("code") or None),
            msg=(last_err.get("message") or None),
        )


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
        attempt.raw = pi
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.CANCELED)
