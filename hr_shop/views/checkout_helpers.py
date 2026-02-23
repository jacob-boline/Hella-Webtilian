# hr_shop/views/checkout_helpers.py

import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from hr_common.utils.email import normalize_email
from hr_common.utils.http.htmx import hx_load_modal, merge_hx_trigger_after_settle
from hr_common.utils.unified_logging import log_event
from hr_payment.services.payment_state import mark_checkout_draft_used
from hr_shop.cart import Cart, CART_SESSION_KEY, get_cart
from hr_shop.forms import CheckoutDetailsForm
from hr_shop.models import Address, CheckoutDraft, Customer, Order, PaymentStatus, ProductVariant
from hr_shop.services.email_confirmation import is_email_confirmed_for_checkout
from hr_shop.tokens.guest_checkout_token import CHECKOUT_CTX_MAX_AGE, generate_guest_checkout_token, GuestCheckoutToken, verify_guest_checkout_token
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token, verify_order_receipt_token
from hr_shop.views.checkout_stripe import _stripe_session_result

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuestCheckoutContext:
    order: Order
    draft: CheckoutDraft
    token: GuestCheckoutToken
    customer: Customer


#-----------------------------------------------------------------------------
#  Cart helpers
#-----------------------------------------------------------------------------

def _cart_snapshot(request):
    cart = Cart(request)
    snap = []
    for line in cart:
        snap.append({"variant_id": line["variant"].id, "qty": int(line["quantity"]), "unit_price": str(line["unit_price"])})
    return snap


def _iter_cart_items_for_order(request):
    cart = get_cart(request)
    for item in cart:
        variant = item.get("variant")
        if variant is None:
            continue

        quantity = int(item.get("quantity", 1))

        price_source = item.get("unit_price")
        if price_source is None:
            price_source = variant.price

        unit_price = Decimal(str(price_source)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        yield {"variant": variant, "quantity": quantity, "unit_price": unit_price}


def _clear_cart(request) -> None:
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


def _restore_cart_from_draft(request, draft: CheckoutDraft):
    request.session[CART_SESSION_KEY] = {}

    variant_ids = [x["variant_id"] for x in (draft.cart or [])]
    existing = set(ProductVariant.objects.filter(id__in=variant_ids).values_list("id", flat=True))

    for item in draft.cart or []:
        vid = item.get("variant_id")
        if vid not in existing:
            continue
        request.session[CART_SESSION_KEY][str(vid)] = {
            "quantity": int(item.get("qty", 1)),
            "unit_price": str(item.get("unit_price", "0.00"))
        }

    request.session.modified = True



#-----------------------------------------------------------------------------
#  Customer / address / order helpers
#-----------------------------------------------------------------------------

def _get_existing_customer_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "customer", None)


def _apply_customer_updates(customer: Customer, form: CheckoutDetailsForm, user) -> list[str]:
    """Apply form data to an existing customer. Returns list of updated field names."""
    updates: list[tuple[str, Any]] = [
        ("first_name",     form.cleaned_data["first_name"].strip()                      ),
        ("last_name",      form.cleaned_data["last_name"].strip()                       ),
        ("middle_initial", form.cleaned_data.get("middle_initial", "").strip() or None  ),
        ("suffix",         form.cleaned_data.get("suffix", "").strip() or None          ),
        ("phone",          form.cleaned_data.get("phone", "") or None                   )
    ]

    updated_fields = []
    for field, new_value in updates:
        if new_value is not None and getattr(customer, field) != new_value:
            setattr(customer, field, new_value)
            updated_fields.append(field)

    if user and user.is_authenticated and customer.user_id is None:
        customer.user = user
        updated_fields.append("user")

    return updated_fields


def _get_or_create_customer(email: str, user, form: CheckoutDetailsForm) -> Customer:
    customer, created = Customer.objects.get_or_create(
        email=email,
        defaults={
            "user":             user if user and user.is_authenticated else None,
            "first_name":       form.cleaned_data["first_name"].strip(),
            "middle_initial":   form.cleaned_data.get("middle_initial", "").strip() or None,
            "last_name":        form.cleaned_data["last_name"].strip(),
            "suffix":           form.cleaned_data.get("suffix", "").strip() or None,
            "phone":            form.cleaned_data.get("phone") or None,
            "wants_saved_info": form.cleaned_data["wants_saved_info"]
        }
    )

    if not created:
        updated_fields = _apply_customer_updates(customer, form, user)
        if updated_fields:
            customer.save(update_fields=updated_fields + ["updated_at"])

    return customer


def _resolve_checkout_prefill(request) -> tuple[Customer | None, Address | None, str]:
    """Determine the customer, address, and note to prefill the checkout form with."""
    ctx = _get_checkout_context(request)
    if ctx:
        return ctx["customer"], ctx["address"], ctx.get("note") or ""

    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        customer = _get_existing_customer_for_user(user)
        return customer, _get_most_recent_address_for_customer(customer), ""

    return None, None, ""


def _build_checkout_form_initial(customer: Customer | None, addr: Address | None, note: str, user) -> dict:
    def _customer(field: str) -> str:
        return getattr(customer, field, None) or ""

    def _user(field: str) -> str:
        return (getattr(user, field, "") if user and user.is_authenticated else "") or ""

    def _customer_or_user(field: str) -> str:
        return _customer(field) or _user(field)

    def _addr(field: str, default: str = "") -> str:
        return getattr(addr, field, None) or default

    return {
        "email":                _customer_or_user("email"),
        "phone":                _customer("phone"),
        "first_name":           _customer_or_user("first_name"),
        "middle_initial":       _customer("middle_initial"),
        "last_name":            _customer_or_user("last_name"),
        "suffix":               _customer("suffix"),
        "street_address":       _addr("street_address"),
        "street_address_line2": _addr("street_address_line2"),
        "building_type":        _addr("building_type", "single_family"),
        "unit":                 _addr("unit"),
        "city":                 _addr("city"),
        "subdivision":          _addr("subdivision"),
        "postal_code":          _addr("postal_code"),
        "note":                 note,
    }


def _get_most_recent_address_for_customer(customer: Customer) -> Address or None:
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
        street_address=       form.cleaned_data["street_address"].strip(),
        street_address_line2=(form.cleaned_data.get("street_address_line2", "").strip() or None),
        building_type=        form.cleaned_data["building_type"],
        unit=                (form.cleaned_data.get("unit", "").strip() or None),
        city=                 form.cleaned_data["city"].strip(),
        subdivision=          form.cleaned_data["subdivision"].strip(),
        postal_code=          form.cleaned_data["postal_code"].strip(),
        country=             "United States"
    )
    address, _created = Address.objects.get_or_create_by_components(**components)
    return address


def _get_or_create_active_draft(*, customer, email, address, note, cart_payload):
    now = timezone.now()
    defaults = {
        "email": email,
        "address": address,
        "note": note or "",
        "cart": cart_payload,
        "expires_at": now + timedelta(hours=1)
    }

    with transaction.atomic():
        existing = (
            CheckoutDraft.objects
            .select_for_update()
            .filter(customer=customer, used_at__isnull=True)
            .first()
        )
        if existing:
            for k, v in defaults.items():
                setattr(existing, k, v)
            existing.save(update_fields=list(defaults.keys()))
            return existing

        return CheckoutDraft.objects.create(customer=customer, **defaults)


def _latest_draft_for_customer(customer: Customer) -> CheckoutDraft | None:
    if not customer:
        return None
    return (
        CheckoutDraft.objects
        .filter(customer=customer, used_at__isnull=True)
        .select_related("order")
        .order_by("-created_at")
        .first()
    )



#-----------------------------------------------------------------------------
#  Session / guest token helpers
#-----------------------------------------------------------------------------

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


def _extract_checkout_ctx_token(request) -> str:
    token = (request.headers.get("X-Checkout-Token") or "").strip()
    if token:
        return token

    return (request.COOKIES.get("guest_checkout_token") or "").strip()


def _restore_checkout_context_from_guest_token(request) -> tuple[dict | None, bool]:
    """
    Returns: (ctx, should_clear_cookie)

    should_clear_cookie=True when a guest token/cookie was present but invalid/expired,
    so callers can clear the cookie on the response.
    """
    token_raw = _extract_checkout_ctx_token(request)
    if not token_raw:
        return None, False

    guest_checkout_token = verify_guest_checkout_token(token_raw)
    if not guest_checkout_token:
        return None, True

    # Claims are expected to include at least customer_id + draft_id.
    try:
        customer_id = int(guest_checkout_token.customer_id)
        draft_id = int(guest_checkout_token.draft_id)
        order_id = int(guest_checkout_token.order_id)
    except (TypeError, ValueError):
        return None, True

    draft = (
        CheckoutDraft.objects
        .select_related("customer", "address", "order")
        .filter(id=draft_id, customer_id=customer_id)
        .first()
    )
    if not draft or not draft.is_valid():
        return None, True

    if int(getattr(draft, 'order_id', 0) or 0) != order_id:
        return None, True

    # restore session context
    request.session["checkout_customer_id"] = draft.customer_id
    request.session["checkout_address_id"] = draft.address_id
    request.session["checkout_note"] = draft.note or ""
    request.session["wants_saved_info"] = bool(getattr(draft.customer, "wants_saved_info", False))
    request.session.modified = True

    # Restore cart only if empty
    existing_cart = request.session.get(CART_SESSION_KEY) or {}
    if not existing_cart:
        _restore_cart_from_draft(request, draft)

    return {
       "customer":     draft.customer,
       "address":      draft.address,
       "note":         draft.note or "",
       "_guest_token": guest_checkout_token,
       "_draft":       draft
   }, False


def _try_restore_guest_session(request) -> tuple[dict | None, bool]:
    """
    Attempt to get or restore checkout session context.
    Returns: (context, should_clear_cookie)
    """

    # First try session-based context
    ctx = _get_checkout_context(request)
    if ctx:
        return ctx, False

    # Fall back to token-based restoration
    return _restore_checkout_context_from_guest_token(request)



#-----------------------------------------------------------------------------
#  Authorization helpers
#-----------------------------------------------------------------------------

def _is_allowed_to_email_receipt(request, order: Order) -> bool:
    # 1) Logged-in owner can always resend
    user = getattr(request, "user", None)
    if user and user.is_authenticated and getattr(order, "user_id", None) == user.id:
        return True

    # 2) Guest flow: must have a valid signed receipt token
    raw_token = (request.POST.get("t") or request.GET.get("t") or "").strip()
    if not raw_token:
        return False

    order_receipt_token = verify_order_receipt_token(raw_token)
    if not order_receipt_token:
        return False

    return int(order_receipt_token.order_id) == int(order.id) and normalize_email(order_receipt_token.email) == normalize_email(order.email)


def _user_is_authorized_for_payment_result(request, order, token) -> bool:
    if request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id:
        return True

    if not token:
        return False

    order_receipt_token = verify_order_receipt_token(token)
    if not order_receipt_token:
        return False

    # versioning/tampering safety net for token
    try:
        token_order_id = order_receipt_token.order_id
    except (TypeError, ValueError):
        return False

    if token_order_id != int(order.id):
        return False

    return normalize_email(order_receipt_token.email) == order.email


def _validate_guest_checkout(request, order_id: int) -> tuple[GuestCheckoutContext | None, HttpResponse | None]:
    """
    Validates guest checkout token for an order.
    Returns: (context, error_response)
    - If valid: (GuestCheckoutContext, None)
    - If invalid: (None, HttpResponse with appropriate error)
    """
    order = get_object_or_404(Order, pk=int(order_id))

    # 1. Check token exists
    raw_token = _extract_checkout_ctx_token(request)
    if not raw_token:
        return None, hx_load_modal(reverse("hr_shop:checkout_resume"), after_settle={"showMessage": {"text": "Session expired. Please restart."}})

    # 2. Verify token
    token = verify_guest_checkout_token(raw_token)
    if not token:
        resp = hx_load_modal(reverse("hr_shop:checkout_resume"),  after_settle={"showMessage": {"text": "Session expired. Please restart."}})
        resp.delete_cookie("guest_checkout_token")
        return None, resp

    # 3. Check token.order_id matches
    if token.order_id != order.id:
        log_event(logger, logging.WARNING, "checkout.guest_token_order_mismatch", order_id=order.id, token_order_id=token.order_id)
        resp = hx_load_modal(reverse("hr_shop:checkout_resume"), after_settle={"showMessage": {"text": "Session out of date. Please restart."}})
        resp.delete_cookie("guest_checkout_token")
        return None, resp

    # 4. Fetch and validate draft
    draft = (
        CheckoutDraft.objects
        .select_related("customer", "address", "order")
        .filter(
            id=token.draft_id,
            customer_id=token.customer_id,
            order_id=order.id,
            used_at__isnull=True,
            expires_at__gt=timezone.now()
        )
        .first()
    )

    if not draft:
        log_event(logger, logging.WARNING, "checkout.guest_draft_invalid_or_missing", order_id=order.id)
        resp = hx_load_modal(reverse("hr_shop:checkout_resume"), after_settle={"showMessage": {"text": "Checkout expired. Please restart."}})
        resp.delete_cookie("guest_checkout_token")
        return None, resp

    # 5. Check email confirmed
    if not is_email_confirmed_for_checkout(request, draft.email):
        log_event(logger, logging.WARNING, "checkout.guest_email_not_verified", order_id=order.id)
        return None, _render_checkout_awaiting_confirmation(
            request, email=order.email, message="Please confirm your email to continue.", rate_limited=False, sent_at=None, error=False
        )

    # Success
    return GuestCheckoutContext(
        order=order,
        draft=draft,
        token=token,
        customer=draft.customer
    ), None



#-----------------------------------------------------------------------------
#  Rate limiting
#-----------------------------------------------------------------------------

def _get_last_confirmation_sent_at(email: str):
    return cache.get(("checkout_confirm_sent_at", email))


def _rate_limit_ok(request, *, key: str, cooldown_s: int) -> bool:
    now = int(time.time())
    last = int(request.session.get(key) or 0)
    if last and (now - last) < cooldown_s:
        return False
    request.session[key] = now
    request.session.modified = True
    return True



#-----------------------------------------------------------------------------
#  Order resume
#-----------------------------------------------------------------------------

def _find_order_for_resume(*, customer: Customer, guest_token, draft) -> Order | None:
    """
    Find the appropriate order to resume for a customer.

    Tries in order:
    1. Guest token order_id (most specific)
    2. Current draft's order_id
    3. Latest unused draft's order_id (fallback for recovery)

    Returns:
        Order if found, None otherwise
    """

    # 1. Prefer order from guest token if present
    if guest_token and getattr(guest_token, "order_id", None):
        order = (
            Order.objects
            .select_related("customer", "shipping_address")
            .filter(pk=int(guest_token.order_id))
            .first()
        )
        if order:
            log_event(logger, logging.DEBUG, "checkout.resume.order_from_token", order_id=order.id)
            return order

    # 2. Try current draft's order
    if draft and getattr(draft, "order_id", None):
        order = (
            Order.objects
            .select_related("customer", "shipping_address")
            .filter(pk=draft.order_id)
            .first()
        )
        if order:
            log_event(logger, logging.DEBUG, "checkout.resume.order_from_current_draft", order_id=order.id)
            return order

    # 3. Fallback: try latest unused draft (for recovery scenarios)
    latest_draft = _latest_draft_for_customer(customer)
    if latest_draft and latest_draft.order_id and latest_draft.is_valid():
        order = (
            Order.objects
            .select_related("customer", "shipping_address")
            .filter(pk=latest_draft.order_id)
            .first()
        )
        if order:
            log_event(logger, logging.DEBUG, "checkout.resume.order_from_latest_draft", order_id=order.id)
            return order

    return None

def _resume_redirect_to_pay(request, *, order: Order, draft: CheckoutDraft | None) -> HttpResponse:
    """Build the hx_load_modal redirect to the payment page, refreshing the guest cookie if needed."""
    pay_url = reverse("hr_shop:checkout_pay", args=[int(order.id)])
    resp = hx_load_modal(pay_url, after_settle={"showMessage": {"text": "Continue payment to complete your order."}})

    if not request.user.is_authenticated and draft:
        token = generate_guest_checkout_token(
            customer_id=int(draft.customer_id),
            draft_id=int(draft.id),
            order_id=int(order.id),
        )
        resp.set_cookie("guest_checkout_token", token, max_age=CHECKOUT_CTX_MAX_AGE,
                        httponly=True, samesite="Lax", secure=not settings.DEBUG)
    return resp


def _resume_response_for_order(request, *, order: Order, guest_token, draft, cart_snapshot) -> HttpResponse | None:
    """
    Returns the appropriate response for a resumable order.
    Returns None if the order should be skipped (caller should fall back to cart modal).
    """

    # Don't surface paid orders unless the guest token explicitly matches
    if order.payment_status == PaymentStatus.PAID:
        token_covers_order = guest_token and getattr(guest_token, "order_id", None) == order.id
        if not token_covers_order:
            log_event(logger, logging.INFO, "checkout.resume.skipping_paid_order",
                      order_id=order.id, has_token=bool(guest_token))
            return None

    log_event(logger, logging.INFO, "checkout.resume.order_found",
              order_id=order.id, customer_id=getattr(order.customer, "id", None))

    # Skip if cart changed after payment (user started a new cart)
    if order.payment_status == PaymentStatus.PAID and cart_snapshot and draft:
        draft_cart = list(getattr(draft, "cart", None) or [])
        if not draft_cart or draft_cart != cart_snapshot:
            log_event(logger, logging.INFO, "checkout.resume.paid_order_cart_mismatch", order_id=order.id)
            return None

    stripe_session_id = (getattr(order, "stripe_checkout_session_id", None) or "").strip()
    if not stripe_session_id and order.payment_status != PaymentStatus.PAID:
        return _resume_redirect_to_pay(request, order=order, draft=draft)

    is_owner = request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id
    receipt_token = "" if is_owner else generate_order_receipt_token(order_id=order.id, email=order.email)
    return _render_order_payment_result_modal(request, order, receipt_token)


#-----------------------------------------------------------------------------
#  Render helpers
#-----------------------------------------------------------------------------

def _render_checkout_review(request, *, ctx: dict):
    items = list(_iter_cart_items_for_order(request))

    if not items:
        return hx_load_modal(
            reverse("hr_shop:view_cart"),
            after_settle={"showMessage": {"text": "Your cart is empty"}}
        )

    customer = ctx["customer"]
    address = ctx["address"]
    note = ctx.get("note", "")

    subtotal = sum((line["unit_price"] * line["quantity"] for line in items), Decimal("0.00"))
    tax = Decimal("0.00")
    shipping = Decimal("0.00")
    total = subtotal + tax + shipping

    return render(request, "hr_shop/checkout/_checkout_review.html",
        {"items": items, "subtotal": subtotal, "tax": tax, "shipping": shipping, "total": total, "customer": customer, "address": address, "note": note}
    )


def _render_checkout_awaiting_confirmation(request, *, email: str, message: str, rate_limited: bool = False, sent_at=None, error: bool = False):
    # Check cache for last-known timestamp if caller didn't pass sent_at
    if sent_at is None and not error:
        sent_at = _get_last_confirmation_sent_at(email)

    return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html",
        {"email": email, "message": message, "rate_limited": bool(rate_limited), "sent_at": sent_at, "error": bool(error)}
    )


def _resolve_payment_result(order: Order) -> tuple[str, str | None, str | None]:
    """
    Determine the current payment result for an order.
    Handles the webhook-lag case by updating the order in-place if Stripe confirms payment.
    Returns: (payment_result, failure_reason, failure_code)
    """
    if order.payment_status == PaymentStatus.PAID:
        return "paid", None, None

    payment_result, failure_reason, failure_code = _stripe_session_result(
        getattr(order, "stripe_checkout_session_id", None)
    )

    # Stripe says paid but webhook hasn't landed yet - persist it now
    if payment_result == "paid" and order.payment_status != PaymentStatus.PAID:
        updated = (
            Order.objects
            .filter(pk=order.pk)
            .exclude(payment_status=PaymentStatus.PAID)
            .update(payment_status=PaymentStatus.PAID)
        )
        if updated:
            order.payment_status = PaymentStatus.PAID
            mark_checkout_draft_used(order.id)

    return payment_result, failure_reason, failure_code


def _clear_checkout_session(request) -> None:
    """Clear cart and all checkout-related session keys after a successful payment."""
    _clear_cart(request)
    for key in ("checkout_customer_id", "checkout_address_id", "checkout_note", "wants_saved_info"):
        request.session.pop(key, None)
    request.session.modified = True


@require_GET
def _render_order_payment_result_modal(request, order: Order, token: str):
    payment_result, failure_reason, failure_code = _resolve_payment_result(order)

    cart_was_cleared = False
    if order.payment_status == PaymentStatus.PAID:
        _clear_checkout_session(request)
        cart_was_cleared = True

    is_guest = not (request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id)
    cta_dismissed = bool(request.session.get(f"pp_cta_dismissed:{order.id}"))

    resp = render(request, "hr_shop/checkout/_order_payment_result.html", {
        "order":                  order,
        "items":                  list(order.items.select_related("variant", "variant__product").all()),
        "customer":               getattr(order, "customer", None),
        "address":                getattr(order, "shipping_address", None),
        "is_guest":               is_guest,
        "payment_result":         payment_result,
        "payment_failure_reason": failure_reason,
        "payment_failure_code":   failure_code,
        "receipt_token":          token,
        "cta_dismissed":          cta_dismissed
    })

    if cart_was_cleared:
        merge_hx_trigger_after_settle(resp, {"updateCart": {"count": 0}})

    if order.payment_status == PaymentStatus.PAID:
        if is_guest:
            resp.delete_cookie("guest_checkout_token")
            merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Payment received. Thank you!"}})
    elif payment_result == "failed":
        merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Payment did not complete. Please try again."}})

    return resp
