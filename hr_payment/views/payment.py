# hr_payment/views/payment.py

from __future__ import annotations

import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from hr_common.security import secrets
from hr_common.utils.http.htmx import hx_trigger
from hr_common.utils.unified_logging import log_event
from hr_payment.models import WebhookEvent
from hr_payment.views.payment_session import _create_stripe_session, _try_reuse_stripe_session
from hr_payment.views.webhook_handlers import _process_stripe_event
from hr_shop.models import Order, PaymentStatus
from hr_shop.views.checkout_helpers import _validate_guest_checkout

logger = logging.getLogger(__name__)


def _authorize_checkout_session_request(request, order: Order) -> HttpResponse | None:
    """
    Validates that the requester is allowed to initiate payment for this order.
    Returns an error HttpResponse if unauthorized, None if authorized.
    """
    user = getattr(request, "user", None)

    if user and user.is_authenticated:
        if getattr(order, "user_id", None) != user.id:
            log_event(logger, logging.WARNING, "payment.checkout.forbidden.not_owner", order_id=order.id)
            raise Http404()
        return None

    guest_ctx, error_response = _validate_guest_checkout(request, order.id)

    if error_response:
        if isinstance(error_response, HttpResponse) and error_response.status_code in (403, 401):
            return hx_trigger({"showMessage": {"text": "Not authorized. Please restart checkout."}}, status=403)
        return hx_trigger({"showMessage": {"text": "Checkout session invalid. Please restart checkout."}}, status=403)

    log_event(logger, logging.INFO, "payment.checkout.guest_authorized",
              order_id=order.id, customer_id=guest_ctx.customer.id, draft_id=guest_ctx.draft.id)
    return None


@require_POST
def checkout_stripe_session(request, order_id: int):
    if getattr(settings, "DEBUG_TOKENS", False):
        log_event(logger, logging.DEBUG, "checkout.token.debug",
                  header_token=bool(request.headers.get("X-Checkout-Token")),
                  cookie_token=bool(request.COOKIES.get("guest_checkout_token")),
                  header_keys=list(request.headers.keys()))

    stripe.api_key = secrets.read_secret("STRIPE_SECRET_KEY")

    order = get_object_or_404(Order, pk=int(order_id))

    error = _authorize_checkout_session_request(request, order)
    if error:
        return error

    if order.payment_status == PaymentStatus.PAID:
        log_event(logger, logging.INFO, "payment.checkout.session_already_paid", order_id=order.id)
        return JsonResponse({"error": "Order already paid."}, status=409)

    if not order.total or order.total <= 0:
        log_event(logger, logging.WARNING, "payment.checkout.invalid_total", order_id=order.id, total=str(order.total or 0))
        return JsonResponse({"error": "Order total must be > 0."}, status=400)

    reused = _try_reuse_stripe_session(order)
    if reused:
        return reused

    return _create_stripe_session(request, order)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe.api_key = secrets.read_secret('STRIPE_SECRET_KEY')
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=secrets.read_secret('STRIPE_WEBHOOK_SECRET')
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
