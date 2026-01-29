# hr_payment/views.py

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from hr_common.utils.unified_logging import log_event
from hr_core.utils.urls import build_external_absolute_url
from hr_payment.models import PaymentAttempt, PaymentAttemptStatus, WebhookEvent
from hr_shop.models import CheckoutDraft, Order, PaymentStatus
from hr_shop.tokens.guest_checkout_token import verify_guest_checkout_token
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token

logger = logging.getLogger(__name__)

def _forbid_guest_payment(msg='Not authorized. Please restart checkout.', clear_cookie=False):
    resp = JsonResponse({'error': msg}, status=403)
    if clear_cookie:
        resp.delete_cookie('guest_checkout_token')
    return resp

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


def _extract_checkout_ctx_token(request) -> str:
    token = (request.headers.get("X-Checkout-Token") or "").strip()
    if token:
        return token

    return (request.COOKIES.get("guest_checkout_token") or "").strip()


@require_POST
def checkout_stripe_session(request, order_id: int):
    """
    Called by JS to get a client secret for Embedded Checkout.

    Auth users:
      - Must specify order_id and must own the order.

    Guests:
      - Must present a valid GuestCheckoutToken (X-Checkout-Token header preferred, cookie fallback).
      - Token binds (customer_id, draft_id, order_id).
      - Draft must be active+valid+email_confirmed and tied to the same order.

    Idempotent:
      - If an existing open session exists for this order, reuse it.
      - Otherwise create a new PaymentAttempt and a new embedded Checkout session.
    """

    if getattr(settings, "DEBUG_TOKENS", False):
        log_event(logger, logging.DEBUG, "checkout.token.debug",
            header_token=bool(request.headers.get("X-Checkout-Token")),
            cookie_token=bool(request.COOKIES.get("guest_checkout_token")),
            header_keys=list(request.headers.keys())
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    order = get_object_or_404(Order, pk=int(order_id))

    user = getattr(request, 'user', None)
    is_authed = bool(user and user.is_authenticated)

    guest_ctx = None

    if is_authed:
        if getattr(order, 'user_id', None) != user.id:
            log_event(logger, logging.WARNING, 'payment.checkout.forbidden.not_owner', order_id=order.id)
            raise Http404()

    # Guest Order
    else:
        raw_token = _extract_checkout_ctx_token(request)
        if not raw_token:
            return _forbid_guest_payment(clear_cookie=False)

        guest_ctx = verify_guest_checkout_token(raw_token)
        if not guest_ctx:
            return _forbid_guest_payment()

        if int(guest_ctx.order_id) != int(order.id):
            log_event(logger, logging.WARNING, 'payment.checkout.forbidden.guest_token_order_mismatch',
                  requested_order_id=order.id,
                  token_order_id=guest_ctx.order_id,
                  token_customer_id=guest_ctx.customer_id,
                  token_draft_id=guest_ctx.draft_id
            )
            return _forbid_guest_payment()

        draft = (
            CheckoutDraft.objects
            .only("id", "customer_id", "used_at", "expires_at", "order_id", "email_confirmed_at")
            .filter(pk=int(guest_ctx.draft_id), customer_id=int(guest_ctx.customer_id))
            .first()
        )

        if not draft:
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.guest_draft_missing",
                  order_id=order.id,
                  draft_id=guest_ctx.draft_id,
                  customer_id=guest_ctx.customer_id
            )
            return _forbid_guest_payment()

        if not draft.email_confirmed_at:
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.draft_email_not_verified",
                  order_id=order.id,
                  draft_id=guest_ctx.draft_id,
                  customer_id=guest_ctx.customer_id
            )
            return _forbid_guest_payment('Please confirm your email, then restart checkout.', clear_cookie=False)

        # Verify draft is not used or expired
        if not draft.is_valid():
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.guest_draft_invalid",
                order_id=order.id,
                draft_id=draft.id,
                used_at=str(draft.used_at) if draft.used_at else None,
                expires_at=str(draft.expires_at) if draft.expires_at else None,
                now=str(timezone.now())
            )
            return _forbid_guest_payment()

        # Verify draft and context have same customer
        if draft.customer_id != int(guest_ctx.customer_id):
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.guest_draft_customer_mismatch",
                order_id=order.id,
                draft_id=draft.id,
                token_customer_id=guest_ctx.customer_id,
                draft_customer_id=draft.customer_id
            )
            return _forbid_guest_payment()

        # Verify order and context have same customer
        if order.customer_id != int(guest_ctx.customer_id):
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.guest_order_customer_mismatch",
                order_id=order.id,
                token_customer_id=guest_ctx.customer_id,
                order_customer_id=getattr(order, "customer_id", None),
                draft_id=draft.id
            )
            return _forbid_guest_payment()

        # Successful Token Authentication
        log_event(logger, logging.INFO, "payment.checkout.guest_authorized", order_id=order.id, customer_id=guest_ctx.customer_id, draft_id=guest_ctx.draft_id)

    # -----------------------------
    # State sanity
    # -----------------------------
    if order.payment_status == PaymentStatus.PAID:
        log_event(logger, logging.INFO, "payment.checkout.session_already_paid", order_id=order.id)
        return JsonResponse({"error": "Order already paid."}, status=409)

    if not order.total or order.total <= 0:
        log_event(logger, logging.WARNING, "payment.checkout.invalid_total", order_id=order.id, total=str(order.total or 0))
        return JsonResponse({"error": "Order total must be > 0."}, status=400)

    # -----------------------------
    # 1) Reuse existing open session if possible
    # -----------------------------
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
                # Keep DB in sync
                dirty_attempt = False
                if existing_attempt.client_secret != sess.get("client_secret"):
                    existing_attempt.client_secret = sess.get("client_secret")
                    dirty_attempt = True

                existing_attempt.raw = sess
                if existing_attempt.status != PaymentAttemptStatus.PENDING:
                    existing_attempt.status = PaymentAttemptStatus.PENDING
                    dirty_attempt = True

                if dirty_attempt:
                    existing_attempt.save(update_fields=["client_secret", "raw", "status", "updated_at"])

                dirty_order = False
                if getattr(order, "stripe_checkout_session_id", None) != sess.get("id"):
                    order.stripe_checkout_session_id = sess.get("id")
                    dirty_order = True
                if order.payment_status != PaymentStatus.PENDING:
                    order.payment_status = PaymentStatus.PENDING
                    dirty_order = True
                if dirty_order:
                    order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

                log_event(logger, logging.INFO, "payment.checkout.session_reused", order_id=order.id, attempt_id=existing_attempt.id, session_id=sess.get("id"))

                return JsonResponse({"clientSecret": sess["client_secret"], "sessionId": sess["id"], "reused": True})

        except Exception as exc:
            log_event(logger, logging.WARNING, "payment.checkout.session_reuse_failed",
                order_id=order.id,
                attempt_id=getattr(existing_attempt, "id", None),
                session_id=existing_attempt.provider_session_id,
                error=str(exc),
                exc_info=True
            )
            # Continue to create a new session

    # -----------------------------
    # 2) Create a new attempt + session (atomic so attempt exists for webhook mapping)
    # -----------------------------
    amount_cents = int((order.total * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    attach_customer = False
    if getattr(request, "user", None) and request.user.is_authenticated:
        attach_customer = True
    if request.session.get("wants_saved_info") is True:
        attach_customer = True

    with transaction.atomic():
        attempt = PaymentAttempt.objects.create(order=order, provider="stripe", status=PaymentAttemptStatus.CREATED, amount_cents=amount_cents, currency="usd")

        # Token for post-payment “handoff” page/modal.
        receipt_token = generate_order_receipt_token(order_id=order.id, email=order.email or "")
        return_url = _stripe_return_url(request, token=receipt_token)

        session_kwargs = {
            "ui_mode": "embedded",
            "mode": "payment",
            "payment_method_types": ["card"],
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Hella Reptilian Order #{order.id}"},
                    "unit_amount": amount_cents
                },
                "quantity": 1
            }],
            "metadata": {
                "order_id": str(order.id),
                "payment_attempt_id": str(attempt.id)
            },
            "return_url": return_url
        }

        if attach_customer:
            stripe_customer_id = _get_or_create_stripe_customer_id(customer=order.customer, email=order.email)
            session_kwargs["customer"] = stripe_customer_id
            session_kwargs["customer_update"] = {"address": "auto", "shipping": "auto"}
        else:
            session_kwargs["customer_email"] = order.email

        try:
            sess = stripe.checkout.Session.create(**session_kwargs)
        except stripe.error.StripeError as exc:
            log_event(logger, logging.ERROR, "payment.checkout.session_create_failed",
                order_id=order.id,
                attempt_id=attempt.id,
                attach_customer=attach_customer,
                error=str(exc),
                error_type=getattr(exc, "__class__", type(exc)).__name__,
                user_id=getattr(user, "id", None),
                customer_id=getattr(order, "customer_id", None),
            )
            return JsonResponse({"error": "Payment session could not be created."}, status=502)

        attempt.provider_session_id = sess.get("id")
        attempt.client_secret = sess.get("client_secret")
        attempt.raw = sess
        attempt.status = PaymentAttemptStatus.PENDING
        attempt.save(update_fields=["provider_session_id", "client_secret", "raw", "status", "updated_at"])

        order.stripe_checkout_session_id = sess.get("id")
        if order.payment_status != PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.PENDING
        order.save(update_fields=["stripe_checkout_session_id", "payment_status", "updated_at"])

        log_event(logger, logging.INFO, "payment.checkout.session_created",
            order_id=order.id, attempt_id=attempt.id, session_id=sess.get("id"), attach_customer=attach_customer
        )

        return JsonResponse({"clientSecret": sess.get("client_secret"), "sessionId": sess.get("id"), "reused": False})


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
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        log_event(logger, logging.WARNING, "payment.webhook.invalid_signature", signature_present=bool(sig_header))
        return HttpResponse(status=400)

    # idempotency/audit
    obj, created = WebhookEvent.objects.get_or_create(
        event_id=event["id"],
        defaults={
            "type": event.get("type", ""),
            "payload": event
        }
    )
    if not created and obj.ok:
        log_event(logger, logging.INFO, "payment.webhook.duplicate", event_id=event.get("id"))
        return HttpResponse(status=200)

    try:
        with transaction.atomic():
            _process_stripe_event(event)
        obj.ok = True
        obj.processed_at = timezone.now()
        obj.error = None
        obj.save(update_fields=["ok", "processed_at", "error"])
    except Exception as e:
        log_event(logger, logging.ERROR, "payment.webhook.processing_failed", event_id=event.get("id"), error=str(e), exc_info=True)
        obj.ok = False
        obj.processed_at = timezone.now()
        obj.error = str(e)
        obj.save(update_fields=["ok", "processed_at", "error"])
        return HttpResponse(status=500)

    return HttpResponse(status=200)


def _get_or_create_stripe_customer_id(*, customer, email: str) -> str:
    if customer.stripe_customer_id:
        return customer.stripe_customer_id

    stripe_customer = stripe.Customer.create(email=email, name=(customer.full_name or None), metadata={"hr_customer_id": str(customer.id)})

    customer.stripe_customer_id = stripe_customer["id"]
    customer.save(update_fields=["stripe_customer_id", "updated_at"])
    return stripe_customer["id"]


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
    order.save(update_fields=["stripe_checkout_session_id", "stripe_payment_intent_id", "payment_status", "updated_at"])

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
        attempt.raw = pi
        attempt.save(update_fields=["raw", "updated_at"])
        attempt.mark_final(PaymentAttemptStatus.CANCELED)
