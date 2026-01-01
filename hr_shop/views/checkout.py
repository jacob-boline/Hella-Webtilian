# hr_shop/views/checkout.py

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string

from hr_common.models import Address
from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import (
    generate_order_receipt_token,
    verify_checkout_email_token,
    verify_order_receipt_token,
)
from hr_shop.cart import get_cart, Cart, CART_SESSION_KEY
from hr_shop.exceptions import EmailSendError, RateLimitExceeded
from hr_shop.forms import CheckoutDetailsForm
from hr_shop.models import (
    Customer, Order, OrderItem, ProductVariant,
    ConfirmedEmail, CheckoutDraft, CustomerAddress,
    PaymentStatus, OrderStatus
)
from hr_shop.services.email_confirmation import (
    is_email_confirmed_for_checkout,
    send_checkout_confirmation_email,
)
from hr_shop.views.cart import view_cart
from hr_email.service import EmailProviderError, send_app_email

logger = logging.getLogger(__name__)

_RECEIPT_RESEND_COOLDOWN_SECONDS = 30


class StripePaymentResult(str, Enum):
    PAID = "paid"
    PENDING = "pending"     # session open / still processing / temporary Stripe issue
    FAILED = "failed"       # user action required / payment rejected
    CANCELED = "canceled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StripePaymentOutcome:
    result: StripePaymentResult
    failure_reason: Optional[str] = None
    failure_code: Optional[str] = None

    def as_tuple(self) -> Tuple[str, Optional[str], Optional[str]]:
        return self.result.value, self.failure_reason, self.failure_code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_checkout_context(request) -> dict | None:
    customer_id = request.session.get("checkout_customer_id")
    address_id = request.session.get("checkout_address_id")
    if not customer_id or not address_id:
        return None

    try:
        customer = Customer.objects.get(pk=customer_id)
        address = Address.objects.get(pk=address_id)
    except (Customer.DoesNotExist, Address.DoesNotExist):
        return None

    return {"customer": customer, "address": address, "note": request.session.get("checkout_note", "")}


def _rate_limit_ok(request, *, key: str, cooldown_s: int) -> bool:
    now = int(time.time())
    last = int(request.session.get(key) or 0)
    if last and (now - last) < cooldown_s:
        return False
    request.session[key] = now
    request.session.modified = True
    return True


def _cart_snapshot(request):
    cart = Cart(request)
    snap = []
    for line in cart:
        snap.append({
            "variant_id": line["variant"].id,
            "qty": int(line["quantity"]),
            "unit_price": str(line["unit_price"]),
        })
    return snap


def _get_existing_customer_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'customer', None)


def _get_or_create_customer(email: str, user, form: CheckoutDetailsForm) -> Customer:
    customer, created = Customer.objects.get_or_create(
        email=normalize_email(email),
        defaults={
            "user": user if user and user.is_authenticated else None,
            "first_name": form.cleaned_data["first_name"].strip(),
            "middle_initial": form.cleaned_data.get("middle_initial", "").strip() or None,
            "last_name": form.cleaned_data["last_name"].strip(),
            "suffix": form.cleaned_data.get("suffix", "").strip() or None,
            "phone": form.cleaned_data.get("phone") or None,
            "wants_saved_info": form.cleaned_data["save_info_for_next_time"]
        },
    )

    if not created:
        updated_fields = []

        first_name = form.cleaned_data["first_name"].strip()
        middle_initial = form.cleaned_data.get("middle_initial", "").strip() or None
        last_name = form.cleaned_data["last_name"].strip()
        suffix = form.cleaned_data.get("suffix", "").strip() or None
        phone = form.cleaned_data.get("phone", "") or None

        if first_name and customer.first_name != first_name:
            customer.first_name = first_name
            updated_fields.append("first_name")
        if middle_initial is not None and customer.middle_initial != middle_initial:
            customer.middle_initial = middle_initial
            updated_fields.append("middle_initial")
        if last_name and customer.last_name != last_name:
            customer.last_name = last_name
            updated_fields.append("last_name")
        if suffix is not None and customer.suffix != suffix:
            customer.suffix = suffix
            updated_fields.append("suffix")
        if phone is not None and customer.phone != phone:
            customer.phone = phone
            updated_fields.append("phone")
        if user and user.is_authenticated and customer.user_id is None:
            customer.user = user
            updated_fields.append("user")

        if updated_fields:
            customer.save(update_fields=updated_fields + ["updated_at"])

    return customer


def _get_most_recent_address_for_customer(customer: Customer):
    if not customer:
        return None
    last_order = (
        Order.objects
        .filter(customer=customer, shipping_address__isnull=False)
        .order_by("-created_at")
        .select_related("shipping_address")
        .first()
    )
    return last_order.shipping_address if last_order else None


def _get_or_create_address_from_form(form: CheckoutDetailsForm) -> Address:
    components = dict(
        street_address=form.cleaned_data["street_address"].strip(),
        street_address_line2=(form.cleaned_data.get("street_address_line2", "").strip() or None),
        building_type=form.cleaned_data["building_type"],
        unit=(form.cleaned_data.get("unit", "").strip() or None),
        city=form.cleaned_data["city"].strip(),
        subdivision=form.cleaned_data["subdivision"].strip(),
        postal_code=form.cleaned_data["postal_code"].strip(),
        country="United States",
    )
    # Requires AddressManager.get_or_create_by_components + fingerprint field on Address
    address, _created = Address.objects.get_or_create_by_components(**components)
    return address


def _get_or_create_active_draft(*, customer, email, address, note, cart_payload):
    now = timezone.now()
    defaults = {
        "email": email,
        "address": address,
        "note": note or "",
        "cart": cart_payload,
        "expires_at": now + timedelta(hours=1),
    }
    try:
        with transaction.atomic():
            draft, _created = CheckoutDraft.objects.update_or_create(
                customer=customer,
                used_at__isnull=True,
                defaults=defaults,
            )
            return draft
    except IntegrityError:
        # Rare race: two requests create at the same time, one loses.
        # Just fetch the winner and update it.
        with transaction.atomic():
            draft = CheckoutDraft.objects.select_for_update().get(
                customer=customer,
                used_at__isnull=True,
            )
            for k, v in defaults.items():
                setattr(draft, k, v)
            draft.save(update_fields=list(defaults.keys()))
            return draft


def _latest_draft_for_customer(customer: Customer) -> CheckoutDraft | None:
    if not customer:
        return None
    return (
        CheckoutDraft.objects
        .filter(customer=customer)
        .select_related('order')
        .order_by('-created_at')
        .first()
    )


def _restore_cart_from_draft(request, draft: CheckoutDraft):
    request.session[CART_SESSION_KEY] = {}

    variant_ids = [x["variant_id"] for x in (draft.cart or [])]
    existing = set(ProductVariant.objects.filter(id__in=variant_ids).values_list("id", flat=True))

    for item in (draft.cart or []):
        vid = item.get("variant_id")
        if vid not in existing:
            continue
        request.session[CART_SESSION_KEY][str(vid)] = {
            "quantity": int(item.get("qty", 1)),
            "unit_price": str(item.get("unit_price", "0.00")),
        }

    request.session.modified = True


def _render_checkout_awaiting_confirmation(request, *, email: str, message: str, rate_limited: bool = False, sent_at=None, error: bool = False):
    # Check cache for last-known timestamp if caller didn't pass sent_at
    if sent_at is None and not error:
        sent_at = _get_last_confirmation_sent_at(email)

    return render(request, 'hr_shop/checkout/_checkout_awaiting_confirmation.html', {
        'email': email,
        'message': message,
        'rate_limited': bool(rate_limited),
        'sent_at': sent_at,
        'error': bool(error)
    })


def _get_last_confirmation_sent_at(email: str):
    return cache.get(("checkout_confirm_sent_at", normalize_email(email)))


def _render_checkout_review(request, *, ctx: dict):
    items = list(_iter_cart_items_for_order(request))
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    customer = ctx["customer"]
    address = ctx["address"]
    note = ctx.get("note", "")

    subtotal = sum((line["unit_price"] * line["quantity"] for line in items), Decimal("0.00"))
    tax = Decimal("0.00")
    shipping = Decimal("0.00")
    total = subtotal + tax + shipping

    return render(request, "hr_shop/checkout/_checkout_review.html", {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "total": total,
        "customer": customer,
        "address": address,
        "note": note,
    })


def _iter_cart_items_for_order(request):
    cart = get_cart(request)
    for item in cart:
        variant = item.get("variant")
        if variant is None:
            continue

        quantity = int(item.get("quantity", 1))

        price_source = item.get('unit_price')
        if price_source is None:
            price_source = variant.price

        unit_price = Decimal(str(price_source)).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        yield {
            "variant": variant,
            "quantity": quantity,
            "unit_price": unit_price,
        }


def _stripe_session_payment_intent_id(session_id: str) -> str | None:
    if not session_id:
        return None

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        sess = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        return None

    # Stripe uses "payment_intent" (not "payment_intent_id")
    return sess.get("payment_intent")


def _user_is_authorized_for_payment_result(request, order, token) -> bool:

    if request.user.is_authenticated and getattr(order, 'user_id', None) == request.user.id:
        return True

    if not token:
        return False

    claims = verify_order_receipt_token(token)
    if not claims:
        return False

    # versioning/tampering safety net for token
    try:
        token_order_id = int(claims.get("order_id", -1))
    except (TypeError, ValueError):
        return False

    if token_order_id != int(order.id):
        return False

    return normalize_email(claims.get('email', '')) == normalize_email(order.email or '')


def _stripe_session_result(session_id: str | None) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Returns: (payment_result, failure_reason, failure_code)

    payment_result in:
      - "paid"
      - "pending"   (session open / still processing OR temporary Stripe issue)
      - "failed"
      - "canceled"
      - "expired"
      - "unknown"
    """
    if not session_id:
        return StripePaymentOutcome(
            StripePaymentResult.UNKNOWN,
            "Missing checkout session id for this order.",
            "missing_session_id",
        ).as_tuple()

    stripe.api_key = settings.STRIPE_SECRET_KEY

    InvalidRequestError = stripe.error.InvalidRequestError
    AuthenticationError = stripe.error.AuthenticationError
    StripePermissionError = stripe.error.PermissionError
    APIConnectionError = stripe.error.APIConnectionError
    RateLimitError = stripe.error.RateLimitError
    StripeError = stripe.error.StripeError

    def _temporary(where: str, err: Exception) -> StripePaymentOutcome:
        logger.info("Stripe temporary issue (%s) session=%s: %s", where, session_id, err)
        return StripePaymentOutcome(StripePaymentResult.PENDING)

    def _hard_auth(where: str, err: Exception) -> StripePaymentOutcome:
        logger.critical("Stripe auth/permission issue (%s) session=%s: %s", where, session_id, err)
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Payment configuration error.", "stripe_auth_error")

    def _generic(where: str, err: Exception) -> StripePaymentOutcome:
        logger.exception("Stripe error (%s) session=%s: %s", where, session_id, err)
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Payment processor error.", "stripe_error")

    # ---- retrieve session
    try:
        sess = stripe.checkout.Session.retrieve(session_id)
    except InvalidRequestError as e:
        logger.warning("Invalid checkout session %s: %s", session_id, e)
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Invalid checkout session.", "invalid_session").as_tuple()
    except (APIConnectionError, RateLimitError) as e:
        return _temporary("retrieve_session", e).as_tuple()
    except (AuthenticationError, StripePermissionError) as e:
        return _hard_auth("retrieve_session", e).as_tuple()
    except StripeError as e:
        return _generic("retrieve_session", e).as_tuple()

    sess_status = (sess.get("status") or "").lower()            # open, complete, expired
    pay_status = (sess.get("payment_status") or "").lower()     # paid, unpaid, no_payment_required
    pi_id = sess.get("payment_intent")

    # ---- table-driven interpretation of session states
    SESSION_RULES: dict[tuple[str, str], StripePaymentOutcome] = {
        ("complete", "paid"):               StripePaymentOutcome(StripePaymentResult.PAID),

        ("open", "paid"):                   StripePaymentOutcome(StripePaymentResult.PAID),  # rare, but safe
        ("open", "unpaid"):                 StripePaymentOutcome(StripePaymentResult.PENDING),
        ("open", "no_payment_required"):    StripePaymentOutcome(StripePaymentResult.PAID),

        ("expired", "paid"):                StripePaymentOutcome(StripePaymentResult.PAID),  # weird but trust paid
        ("expired", "unpaid"):              StripePaymentOutcome(
            StripePaymentResult.EXPIRED,
            "The checkout session expired before payment completed.",
            "session_expired",
        ),
        ("expired", "no_payment_required"): StripePaymentOutcome(StripePaymentResult.EXPIRED),
    }

    direct = SESSION_RULES.get((sess_status, pay_status))
    if direct:
        return direct.as_tuple()

    if pay_status == "paid":
        return StripePaymentOutcome(StripePaymentResult.PAID).as_tuple()

    if sess_status == "open":
        return StripePaymentOutcome(StripePaymentResult.PENDING).as_tuple()

    if sess_status == "expired":
        return StripePaymentOutcome(
            StripePaymentResult.EXPIRED,
            "The checkout session expired before payment completed.",
            "session_expired",
        ).as_tuple()

    # ---- fallthrough: complete but unpaid/unknown -> consult PaymentIntent
    if not pi_id:
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN).as_tuple()

    try:
        pi = stripe.PaymentIntent.retrieve(pi_id)
    except InvalidRequestError as e:
        logger.warning("Invalid PaymentIntent %s for session=%s: %s", pi_id, session_id, e)
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Invalid payment intent.", "invalid_payment_intent").as_tuple()
    except (APIConnectionError, RateLimitError) as e:
        return _temporary("retrieve_payment_intent", e).as_tuple()
    except (AuthenticationError, StripePermissionError) as e:
        return _hard_auth("retrieve_payment_intent", e).as_tuple()
    except StripeError as e:
        return _generic("retrieve_payment_intent", e).as_tuple()

    pi_status = (pi.get("status") or "").lower()

    PI_RULES: dict[str, StripePaymentOutcome] = {
        "succeeded":               StripePaymentOutcome(StripePaymentResult.PAID),
        "canceled":                StripePaymentOutcome(StripePaymentResult.CANCELED, "The payment was canceled.", "payment_intent_canceled"),

        "requires_payment_method": StripePaymentOutcome(StripePaymentResult.FAILED),
        "requires_action":         StripePaymentOutcome(StripePaymentResult.FAILED),
        "requires_confirmation":   StripePaymentOutcome(StripePaymentResult.FAILED),

        "processing":              StripePaymentOutcome(StripePaymentResult.PENDING),
        "requires_capture":        StripePaymentOutcome(StripePaymentResult.PENDING),
    }

    mapped = PI_RULES.get(pi_status)
    if mapped:
        if mapped.result == StripePaymentResult.FAILED:
            last_err = (pi.get("last_payment_error") or {})
            reason = last_err.get("message") or None
            code = last_err.get("code") or None
            return StripePaymentOutcome(StripePaymentResult.FAILED, reason, code or pi_status).as_tuple()
        return mapped.as_tuple()

    last_err = (pi.get("last_payment_error") or {})
    reason = last_err.get("message") or None
    code = last_err.get("code") or None
    return StripePaymentOutcome(StripePaymentResult.UNKNOWN, reason, code).as_tuple()


def _is_allowed_to_email_receipt(request, order: Order) -> bool:
    # 1) Logged-in owner can always resend
    user = getattr(request, "user", None)
    if user and user.is_authenticated and getattr(order, "user_id", None) == user.id:
        return True

    # 2) Guest flow: must have a valid signed receipt token
    token = (request.POST.get("t") or request.GET.get("t") or "").strip()
    if not token:
        return False

    claims = verify_order_receipt_token(token)
    if not isinstance(claims, dict):
        return False

    # 3) Validate order_id from claims without exceptions
    oid = claims.get("order_id")

    if isinstance(oid, int):
        claim_order_id = oid
    elif isinstance(oid, str) and oid.isdigit():
        claim_order_id = int(oid)
    else:
        return False

    if claim_order_id != int(order.id):
        return False

    # 4) Email must match exactly (normalized)
    claim_email = normalize_email(claims.get("email") or "")
    order_email = normalize_email(order.email or "")

    return bool(claim_email) and claim_email == order_email


def _clear_cart(request) -> None:
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


@require_GET
def _render_order_payment_result_modal(request, order: Order, token: str):
    # Determine payment result:
    if order.payment_status == PaymentStatus.PAID:
        payment_result, failure_reason, failure_code = "paid", None, None
    else:
        payment_result, failure_reason, failure_code = _stripe_session_result(
            getattr(order, "stripe_checkout_session_id", None)
        )

        # If Stripe says paid but webhook lagged, persist here.
        if payment_result == "paid":
            Order.objects.filter(pk=order.pk).update(payment_status=PaymentStatus.PAID)
            order.payment_status = PaymentStatus.PAID

    # Clear cart/session only once actually paid
    cart_was_cleared = False
    if order.payment_status == PaymentStatus.PAID:
        _clear_cart(request)
        for k in ("checkout_customer_id", "checkout_address_id", "checkout_auto"):
            request.session.pop(k, None)
        request.session.modified = True
        cart_was_cleared = True

    items = list(order.items.select_related("variant", "variant__product").all())
    is_guest = not (request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id)

    cta_key = f"pp_cta_dismissed:{order.id}"
    cta_dismissed = bool(request.session.get(cta_key))

    response = render(request, "hr_shop/checkout/_order_payment_result.html", {
        "order": order,
        "items": items,
        "customer": getattr(order, "customer", None),
        "address": getattr(order, "shipping_address", None),
        "is_guest": is_guest,

        "payment_result": payment_result,
        "payment_failure_reason": failure_reason,
        "payment_failure_code": failure_code,

        "receipt_token": token,
        "cta_dismissed": cta_dismissed,
    })

    if cart_was_cleared:
        response.headers["HX-Trigger"] = json.dumps({"updateCart": {"count": 0}})

    return response


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@require_GET
def checkout_details(request):

    ctx = _get_checkout_context(request)
    customer = None
    addr = None
    note = ""

    if ctx:
        customer = ctx["customer"]
        addr = ctx["address"]
        note = ctx.get("note") or ""

    else:
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            customer = _get_existing_customer_for_user(user)
            addr = _get_most_recent_address_for_customer(customer)

    initial: Dict[str, Any] = {
        "email": (getattr(customer, "email", None) or getattr(getattr(request, "user", None), "email", "") or ""),
        "phone": getattr(customer, "phone", "") or "",
        "first_name": (getattr(customer, "first_name", None) or getattr(getattr(request, "user", None), "first_name", "") or ""),
        "middle_initial": getattr(customer, "middle_initial", "") or "",
        "last_name": (getattr(customer, "last_name", None) or getattr(getattr(request, "user", None), "last_name", "") or ""),
        "suffix": getattr(customer, "suffix", "") or "",
        "street_address": getattr(addr, "street_address", "") or "",
        "street_address_line2": getattr(addr, "street_address_line2", "") or "",
        "building_type": getattr(addr, "building_type", None) or "single_family",
        "unit": getattr(addr, "unit", "") or "",
        "city": getattr(addr, "city", "") or "",
        "subdivision": getattr(addr, "subdivision", "") or "",
        "postal_code": getattr(addr, "postal_code", "") or "",
        "note": note
    }

    form = CheckoutDetailsForm(initial=initial)
    return render(request, "hr_shop/checkout/_checkout_details.html", {"form": form})


@require_POST
def checkout_details_submit(request):
    form = CheckoutDetailsForm(request.POST)
    if not form.is_valid():
        return render(request, "hr_shop/checkout/_checkout_details.html", {"form": form})

    user = getattr(request, "user", None)
    email = form.cleaned_data["email"].strip()

    if user and user.is_authenticated:
        if normalize_email(email) != normalize_email(user.email):
            form.add_error("email", "Please use the email address associated with your account.")
            return render(request, "hr_shop/checkout/_checkout_details.html", {"form": form})

    customer = _get_or_create_customer(email, user, form)
    address = _get_or_create_address_from_form(form)
    note = (form.cleaned_data.get("note") or "").strip()

    # Save checkout context in session
    request.session["checkout_customer_id"] = customer.id
    request.session["checkout_address_id"] = address.id
    request.session["checkout_note"] = note
    request.session["wants_saved_info"] = customer.wants_saved_info
    request.session.modified = True

    ctx = {"customer": customer, "address": address, "note": note}

    # Update customer default shipping link atomically
    with transaction.atomic():
        CustomerAddress.objects.select_for_update().filter(customer=customer)
        CustomerAddress.objects.filter(customer=customer, is_default_shipping=True).update(is_default_shipping=False)
        CustomerAddress.objects.update_or_create(
            customer=customer,
            address=address,
            defaults={"is_default_shipping": True},
        )

    # Create/update an active draft
    draft = _get_or_create_active_draft(
        customer=customer,
        email=customer.email,
        address=address,
        note=note,
        cart_payload=_cart_snapshot(request),
    )

    if is_email_confirmed_for_checkout(request, email):
        return _render_checkout_review(request, ctx=ctx)

    try:
        send_checkout_confirmation_email(
            request=request,
            email=email,
            draft_id=draft.id,  # requires token/service support
        )
    except RateLimitExceeded:
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": email,
            "message": "Too many confirmation emails sent. Please check your inbox (including spam folder) or try again in an hour.",
            "rate_limited": True,
            "sent_at": None,
        })
    except EmailSendError:
        messages.error(request, "Could not send confirmation email. Please try again.")
        return render(request, "hr_shop/checkout/_checkout_details.html", {"form": form})

    return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
        "email": email,
        "message": "We've sent a confirmation link to your email. Please check your inbox and click the link to continue.",
        "rate_limited": False,
        "sent_at": timezone.now()
    })


@require_GET
def checkout_resume(request):
    cart = get_cart(request)
    if not cart or len(cart) == 0:
        return view_cart(request)

    ctx = _get_checkout_context(request)
    if not ctx:
        return checkout_details(request)

    customer = ctx["customer"]
    email = customer.email
    latest_draft = _latest_draft_for_customer(customer)

    if latest_draft and latest_draft.order_id:
        order = (
            Order.objects
            .select_related("customer", "shipping_address")
            .filter(pk=latest_draft.order_id)
            .first()
        )

        if order:
            # owner -> token optional; everyone else -> sign
            token = ""
            if not (request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id):
                token = generate_order_receipt_token(order.id, order.email or "")

            # IMPORTANT: return fragment, not redirect
            return _render_order_payment_result_modal(request, order, token)

    if not is_email_confirmed_for_checkout(request, email):
        return _render_checkout_awaiting_confirmation(
            request,
            email=email,
            message="Please confirm your email to continue.",
            rate_limited=False,
            sent_at=None,
            error=False,
        )

    return _render_checkout_review(request, ctx=ctx)


@require_GET
def order_payment_result(request, order_id: int):
    order = get_object_or_404(
        Order.objects.select_related("customer", "shipping_address"),
        pk=order_id,
    )

    token = (request.GET.get("t") or "").strip()

    if not _user_is_authorized_for_payment_result(request, order, token):
        return HttpResponse("Not authorized to view this receipt.", status=403)

    return _render_order_payment_result_modal(request, order, token)


@require_POST
def order_send_receipt_email(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    if not _is_allowed_to_email_receipt(request, order):
        return HttpResponse(status=403)

    if not order.email:
        return HttpResponse(status=400, headers={
            'HX-Trigger': json.dumps({'showMessage': 'No email address is associated with this order.'})
        })

    rl_key = f"receipt_resend:{order.id}"
    if not _rate_limit_ok(request, key=rl_key, cooldown_s=_RECEIPT_RESEND_COOLDOWN_SECONDS):
        return HttpResponse(status=429, headers={
            'HX-Trigger': json.dumps({'showMessage': "Please wait a moment before resending the receipt."})
        })

    receipt_token = generate_order_receipt_token(order.id, order.email)
    receipt_url = (
        settings.SITE_URL +
        f"/?modal=order_payment_result&order_id={order.id}&t={quote(receipt_token)}#parallax-section-shows"
    )

    subject = f"Hella Reptilian Order #{order.id} receipt"
    html_body = render_to_string("hr_shop/emails/order_receipt.html", {
        "order": order,
        "receipt_url": receipt_url,
    })

    try:
        send_app_email(
            to_emails=[order.email],
            subject=subject,
            html_body=html_body,
            custom_id=f"order_receipt_{order.id}",
        )
        logger.info("Receipt email sent for order %s to %s", order_id, order.email)

        return HttpResponse(status=204, headers={
            'HX-Trigger': json.dumps({'showMessage': 'Receipt email sent.'})
        })

    except EmailProviderError as exc:
        logger.exception("Failed sending receipt for order %s: %s", order.id, exc)
        return HttpResponse(status=500, headers={
            'HX-Trigger': json.dumps({'showMessage': 'Receipt email failed to send. Try again shortly.'})
        })

    except Exception as e:
        logger.exception("Failed sending receipt for order %s: %s", order.id, e)
        return HttpResponse(status=500, headers={
            'HX-Trigger': json.dumps({'showMessage': 'Receipt email failed to send. Try again shortly.'})
        })


@require_GET
def email_confirmation_status(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        return render(request, "hr_shop/checkout/_checkout_session_expired.html")

    # Use the same rules as checkout (authenticated users count too)
    if is_email_confirmed_for_checkout(request, ctx["customer"].email):
        return _render_checkout_review(request, ctx=ctx)

    return HttpResponse(status=204)


@require_GET
def email_confirmation_process_response(request, token: str):
    payload = verify_checkout_email_token(token)
    if not payload:
        messages.error(request, "This confirmation link is invalid or has expired.")
        return redirect("hr_shop:checkout_details")

    email = payload.get("email")
    draft_id = payload.get("draft_id")
    if not email or not draft_id:
        messages.error(request, "Invalid confirmation link.")
        return redirect("hr_shop:checkout_details")

    now = timezone.now()
    norm_email = normalize_email(email)

    with transaction.atomic():
        draft = (
            CheckoutDraft.objects
            .select_for_update()
            .select_related("customer", "address", "order")
            .filter(id=draft_id)
            .first()
        )

        if not draft:
            messages.warning(request, "That checkout session no longer exists. Please restart checkout.")
            return redirect("hr_shop:checkout_details")

        if normalize_email(draft.email) != norm_email:
            messages.error(request, "This confirmation link does not match your checkout email.")
            return redirect("hr_shop:checkout_details")

        if not draft.is_valid():
            # If an order already exists, don't block: take them to receipt.
            if draft.order_id:
                return redirect("hr_shop:order_payment_result", order_id=draft.order_id)

            messages.warning(request, "This checkout link expired. Please restart checkout.")
            return redirect("hr_shop:checkout_details")

        # Mark confirmed AFTER we know draft is legit and email matches it
        ConfirmedEmail.mark_confirmed(norm_email)

        # Idempotent mark-used
        if draft.used_at is None:
            draft.used_at = now
            draft.save(update_fields=["used_at"])

        # If they already made an order, this click should just send them there.
        if draft.order_id:
            return redirect("hr_shop:order_payment_result", order_id=draft.order_id)

        # Restore session context
        request.session["checkout_customer_id"] = draft.customer_id
        request.session["checkout_address_id"] = draft.address_id
        request.session["checkout_note"] = draft.note or ""
        request.session.modified = True

        # Restore cart only if empty
        existing_cart = request.session.get(CART_SESSION_KEY) or {}
        if not existing_cart:
            _restore_cart_from_draft(request, draft)

    success_url = reverse('hr_shop:email_confirmation_success')
    url = reverse('index')
    return redirect(f'{url}?modal=email_confirmed&handoff=email_confirmed&modal_url={success_url}#parallax-section-merch')


def email_confirmation_success(request):
    return render(request, 'hr_shop/checkout/_email_confirmation_success.html')


@require_POST
def email_confirmation_resend(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect("hr_shop:checkout_details")

    customer = ctx["customer"]

    cart_payload = _cart_snapshot(request)

    draft = _get_or_create_active_draft(
        customer=customer,
        email=customer.email,
        address=ctx["address"],
        note=ctx["note"],
        cart_payload=cart_payload,
    )

    try:
        send_checkout_confirmation_email(
            request=request,
            email=customer.email,
            draft_id=draft.id,
        )
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "We've sent another confirmation link. Please check your inbox.",
            "rate_limited": False,
            "sent_at": timezone.now(),
        })

    except RateLimitExceeded:
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "Too many emails sent. Please check your inbox (including spam folder) or try again later.",
            "rate_limited": True,
            "sent_at": None,
        })

    except EmailSendError:
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "Could not send email. Please try again.",
            "rate_limited": False,
            "sent_at": None,
            "error": True,
        })


@require_GET
def checkout_review(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect("hr_shop:checkout_details")

    if not is_email_confirmed_for_checkout(request, ctx["customer"].email):
        messages.warning(request, "Please confirm your email address to continue.")
        return redirect("hr_shop:checkout_details")

    return _render_checkout_review(request, ctx=ctx)


@require_POST
def checkout_create_order(request):
    items = list(_iter_cart_items_for_order(request))
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect("hr_shop:checkout_details")

    customer = ctx["customer"]
    shipping_address = ctx["address"]
    note = ctx["note"]

    if not is_email_confirmed_for_checkout(request, customer.email):
        messages.error(request, "Please confirm your email address before placing an order.")
        return redirect("hr_shop:checkout_review")

    with transaction.atomic():
        # Lock the most recent usable draft for this customer
        draft = (
            CheckoutDraft.objects
            .select_for_update()
            .select_related("order")
            .filter(
                customer=customer,
                used_at__isnull=True,
                expires_at__gt=timezone.now()
            )
            .order_by("-created_at")
            .first()
        )

        if draft and draft.order_id:
            redirect_url = reverse("hr_shop:order_payment_result", args=[draft.order_id])
            return HttpResponse(status=204, headers={"HX-Redirect": redirect_url})

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer=customer,
            email=normalize_email(customer.email),
            shipping_address=shipping_address,
            total=Decimal("0.00"),
            order_status=OrderStatus.RECEIVED,
            payment_status=PaymentStatus.UNPAID,
            note=note or None,
        )

        subtotal = Decimal("0.00")
        for line in items:
            variant = line["variant"]
            quantity = int(line["quantity"])
            unit_price = Decimal(str(line["unit_price"]))
            line_total = unit_price * quantity

            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price,
            )
            subtotal += line_total

        tax = Decimal("0.00")
        shipping = Decimal("0.00")
        order.total = subtotal + tax + shipping
        order.save(update_fields=["total", "updated_at"])

        # Link the draft to the order for idempotency
        if draft:
            draft.order = order
            draft.used_at = timezone.now()
            draft.save(update_fields=["order", "used_at"])

    # IMPORTANT: Do NOT create Stripe sessions here.
    # Embedded Checkout session creation is driven by the pay UI via:
    #   POST hr_payment:checkout_stripe_session(order.id)

    pay_url = reverse('hr_shop:checkout_pay', args=[order.id])

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'hr_shop/checkout/_checkout_pay.html', {
            'order': order,
            'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
            'client_secret': ''
        })
    return redirect(pay_url, order.id)


@require_GET
def checkout_pay(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    return render(request, 'hr_shop/checkout/_checkout_pay.html', {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': ''
    })


@require_POST
def dismiss_post_purchase_cta(request, order_id: int):
    request.session[f"pp_cta_dismissed:{order_id}"] = True
    return HttpResponse("")
