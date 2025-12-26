# hr_shop/views/checkout.py

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction, IntegrityError

from hr_common.models import Address
from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import verify_checkout_email_token
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_last_confirmation_sent_at(email: str):
    return cache.get(("checkout_confirm_sent_at", normalize_email(email)))


def _render_checkout_awaiting_confirmation(
        request,
        *,
        email: str,
        message: str,
        rate_limited: bool = False,
        sent_at=None,
        error: bool = False
):
    if sent_at is None and not error:
        sent_at = _get_last_confirmation_sent_at(email)

    return render(request, 'hr_shop/checkout/_checkout_awaiting_confirmation.html', {
        'email': email,
        'message': message,
        'rate_limited': bool(rate_limited),
        'sent_at': sent_at,
        'error': bool(error)
    })


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


def _get_existing_customer_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'customer', None)


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
    address, _created = Address.objects.get_or_create_by_components(**components)
    return address


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


def _iter_cart_items_for_order(request):
    cart = get_cart(request)
    for item in cart:
        variant = item.get("variant")
        if variant is None:
            continue

        quantity = int(item.get("quantity", 1))
        unit_price_raw = item.get("unit_price") or variant.price
        unit_price = Decimal(str(unit_price_raw))

        yield {
            "variant": variant,
            "quantity": quantity,
            "unit_price": unit_price,
        }


def _clear_cart(request) -> None:
    request.session.pop(CART_SESSION_KEY, None)
    request.session.modified = True


def _render_checkout_review(request):
    items = list(_iter_cart_items_for_order(request))
    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    subtotal = sum((line["unit_price"] * line["quantity"] for line in items), Decimal("0.00"))
    tax = Decimal("0.00")
    shipping = Decimal("0.00")
    total = subtotal + tax + shipping

    customer_id = request.session.get("checkout_customer_id")
    address_id = request.session.get("checkout_address_id")
    note = request.session.get("checkout_note", "")

    customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
    address = Address.objects.filter(pk=address_id).first() if address_id else None

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
        with transaction.atomic():
            draft = CheckoutDraft.objects.select_for_update().get(
                customer=customer,
                used_at__isnull=True,
            )
            for k, v in defaults.items():
                setattr(draft, k, v)
            draft.save(update_fields=list(defaults.keys()))
            return draft

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

    request.session["checkout_customer_id"] = customer.id
    request.session["checkout_address_id"] = address.id
    request.session["checkout_note"] = note
    request.session.modified = True

    with transaction.atomic():
        CustomerAddress.objects.select_for_update().filter(customer=customer)
        CustomerAddress.objects.filter(customer=customer, is_default_shipping=True).update(is_default_shipping=False)
        CustomerAddress.objects.update_or_create(
            customer=customer,
            address=address,
            defaults={"is_default_shipping": True},
        )

    draft = _get_or_create_active_draft(
        customer=customer,
        email=customer.email,
        address=address,
        note=note,
        cart_payload=_cart_snapshot(request),
    )

    if is_email_confirmed_for_checkout(request, email):
        return _render_checkout_review(request)

    try:
        send_checkout_confirmation_email(
            request=request,
            email=email,
            draft_id=draft.id,
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
            if draft.order_id:
                return redirect("hr_shop:order_thank_you", order_id=draft.order_id)

            messages.warning(request, "This checkout link expired. Please restart checkout.")
            return redirect("hr_shop:checkout_details")

        ConfirmedEmail.mark_confirmed(norm_email)

        if draft.used_at is None:
            draft.used_at = now
            draft.save(update_fields=["used_at"])

        if draft.order_id:
            return redirect("hr_shop:order_thank_you", order_id=draft.order_id)

        request.session["checkout_customer_id"] = draft.customer_id
        request.session["checkout_address_id"] = draft.address_id
        request.session["checkout_note"] = draft.note or ""
        request.session.modified = True

        existing_cart = request.session.get(CART_SESSION_KEY) or {}
        if not existing_cart:
            _restore_cart_from_draft(request, draft)

    success_url = reverse('hr_shop:email_confirmation_success')
    url = reverse('index')
    return redirect(f'{url}?modal=email_confirmed&handoff=email_confirmed&modal_url={success_url}#parallax-section-merch')


@require_GET
def email_confirmation_status(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        return render(request, "hr_shop/checkout/_checkout_session_expired.html")

    if is_email_confirmed_for_checkout(request, ctx["customer"].email):
        return _render_checkout_review(request)

    return HttpResponse(status=204)


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

    return _render_checkout_review(request)


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
            redirect_url = reverse("hr_shop:order_thank_you", args=[draft.order_id])
            return HttpResponse(status=204, headers={"HX-Redirect": redirect_url})

        order = Order.objects.create(
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

        if draft:
            draft.order = order
            draft.used_at = timezone.now()
            draft.save(update_fields=["order", "used_at"])

    # IMPORTANT:
    # Do NOT create a Stripe session here.
    # Embedded Checkout session creation is done by hr_payment.checkout_stripe_session
    # (called by the pay modal JS). That endpoint is idempotent and will reuse/open sessions.
    pay_url = reverse('hr_shop:checkout_pay', args=[order.id])

    if request.headers.get('HX-Request') == 'true':
        return HttpResponse(status=204, headers={'HX-Redirect': pay_url})
    return redirect(pay_url)


@require_GET
def order_thank_you(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    if order.payment_status == PaymentStatus.PAID:
        _clear_cart(request)
        for k in ('checkout_customer_id', 'checkout_address_id', 'checkout_note'):
            request.session.pop(k, None)
        request.session.modified = True

    return render(request, "hr_shop/checkout/_order_thank_you.html", {"order": order})


@require_GET
def checkout_resume(request):
    cart = get_cart(request)
    if not cart or len(cart) == 0:
        return view_cart(request)

    ctx = _get_checkout_context(request)
    if not ctx:
        return checkout_details(request)

    customer = ctx['customer']
    email = customer.email
    latest_draft = _latest_draft_for_customer(customer)

    if latest_draft and latest_draft.order_id:
        return redirect('hr_shop:order_thank_you', order_id=latest_draft.order_id)

    if not is_email_confirmed_for_checkout(request, email):
        return _render_checkout_awaiting_confirmation(
            request,
            email=email,
            message='Please confirm your email to continue.',
            rate_limited=False,
            sent_at=None,
            error=False
        )

    return _render_checkout_review(request)


@require_GET
def checkout_pay(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    return render(request, 'hr_shop/checkout/_checkout_pay.html', {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': ''
    })
