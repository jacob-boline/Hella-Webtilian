# hr_shop/views/checkout.py

import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from hr_common.security import secrets
from hr_common.utils.email import normalize_email
from hr_common.utils.http.htmx import hx_load_modal, hx_trigger, merge_hx_trigger_after_settle
from hr_common.utils.unified_logging import log_event
from hr_email.service import EmailProviderError
from hr_shop.cart import CART_SESSION_KEY, get_cart
from hr_shop.exceptions import EmailSendError, RateLimitExceeded
from hr_shop.forms import CheckoutDetailsForm
from hr_shop.models import CheckoutDraft, ConfirmedEmail, CustomerAddress, Order, OrderItem, OrderStatus, PaymentStatus
from hr_shop.services.email_confirmation import is_email_confirmed_for_checkout, send_checkout_confirmation_email
from hr_shop.services.order_receipt import send_order_receipt_email
from hr_shop.tokens.checkout_email_confirm_token import verify_checkout_email_token
from hr_shop.tokens.guest_checkout_token import CHECKOUT_CTX_MAX_AGE, generate_guest_checkout_token
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token, verify_order_receipt_token
from hr_shop.views.cart import _render_cart_modal
from hr_shop.views.checkout_helpers import _build_checkout_form_initial, _cart_snapshot, _find_order_for_resume, _get_checkout_context, \
    _get_or_create_active_draft, _get_or_create_address_from_form, _get_or_create_customer, \
    _is_allowed_to_email_receipt, _iter_cart_items_for_order, _rate_limit_ok, _render_checkout_awaiting_confirmation, _render_checkout_review, \
    _render_order_payment_result_modal, _resolve_checkout_prefill, _restore_cart_from_draft, _resume_response_for_order, _try_restore_guest_session, \
    _user_is_authorized_for_payment_result, _validate_guest_checkout

logger = logging.getLogger(__name__)

_RECEIPT_RESEND_COOLDOWN_SECONDS = 30

#----------------------------------------------------------------------
#  Checkout flow
#----------------------------------------------------------------------

@require_GET
def checkout_details(request):
    customer, addr, note = _resolve_checkout_prefill(request)
    initial = _build_checkout_form_initial(customer, addr, note, getattr(request, "user", None))
    form = CheckoutDetailsForm(initial=initial)
    return render(request, "hr_shop/checkout/_checkout_details.html", {"form": form})


@require_POST
def checkout_details_submit(request):
    form = CheckoutDetailsForm(request.POST)
    if not form.is_valid():
        log_event(logger, logging.INFO, "checkout.details.form_invalid")
        resp = render(request, "hr_shop/checkout/_checkout_details.html", {"form": form}, status=422)
        return merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Please fix the highlighted fields."}})

    user = getattr(request, "user", None)
    email = normalize_email(form.cleaned_data["email"])

    if user and user.is_authenticated and email != user.email:
        log_event(logger, logging.WARNING, "checkout.details.email_mismatch", form_email=email, user_email=user.email)
        form.add_error("email", "Please use the email associated with your account.")
        resp = render(request, "hr_shop/checkout/_checkout_details.html", {"form": form}, status=422)
        return merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Email must match your account email."}})

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
        CustomerAddress.objects.update_or_create(customer=customer, address=address, defaults={"is_default_shipping": True})

    # Create/update an active draft
    cart_payload = _cart_snapshot(request)
    draft = _get_or_create_active_draft \
        (customer=customer, email=customer.email, address=address, note=note, cart_payload=cart_payload)

    log_event(logger, logging.INFO, "checkout.details.saved",
              customer_id=customer.id, address_id=address.id, draft_id=draft.id, cart_item_count=len(cart_payload))

    if is_email_confirmed_for_checkout(request, email):
        return _render_checkout_review(request, ctx=ctx)

    try:
        send_checkout_confirmation_email(request=request, email=email, draft_id=draft.id)

    except RateLimitExceeded:
        msg = "Too many confirmation emails sent. Please check your inbox (including spam folder) or try again in an hour."
        resp = render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": email,
            "message": msg,
            "rate_limited": True,
            "sent_at": None
        }, status=429)
        return merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Rate limited. Try again in about an hour."}})

    except EmailSendError:
        log_event(logger, logging.ERROR, "checkout.details.email_send_failed")
        resp = render(request, "hr_shop/checkout/_checkout_details.html", {"form": form}, status=500)
        return merge_hx_trigger_after_settle(resp, {"showMessage": {"text": "Could not send confirmation email. Please try again."}})

    msg = "We've sent a confirmation link to your email. Please check your inbox and click the link to continue."
    return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
        "email": email,
        "message": msg,
        "rate_limited": False,
        "sent_at": timezone.now()
    })


@require_GET
def checkout_resume(request):
    """Resume a checkout session from wherever the user left off."""
    cart = get_cart(request)
    if not cart or len(cart) == 0:
        log_event(logger, logging.INFO, "checkout.resume.empty_cart")
        return hx_trigger({"showMessage": {"text": "Your cart is empty."}})

    cart_snapshot = _cart_snapshot(request)

    ctx, clear_cookie = _try_restore_guest_session(request)
    if not ctx:
        log_event(logger, logging.INFO, "checkout.resume.no_session")
        resp = _render_cart_modal(request)
        if clear_cookie:
            resp.delete_cookie("guest_checkout_token")
        return resp

    customer   = ctx["customer"]
    guest_token = ctx.get("_guest_token")
    draft      = ctx.get("_draft")

    if draft and not draft.is_valid():
        log_event(logger, logging.INFO, "checkout.resume.invalid_draft",
                  customer_id=customer.id, draft_id=draft.id)
        resp = _render_cart_modal(request)
        if guest_token:
            resp.delete_cookie("guest_checkout_token")
        return resp

    order = _find_order_for_resume(customer=customer, guest_token=guest_token, draft=draft)

    if order:
        order_resp = _resume_response_for_order(
            request, order=order, guest_token=guest_token, draft=draft, cart_snapshot=cart_snapshot
        )
        if order_resp is not None:
            return order_resp

        # Order was skipped (paid, wrong cart, etc.) — fall back to cart
        resp = _render_cart_modal(request)
        if guest_token:
            resp.delete_cookie("guest_checkout_token")
        return resp

    if not is_email_confirmed_for_checkout(request, customer.email):
        return _render_checkout_awaiting_confirmation(
            request, email=customer.email, message="Please confirm your email to continue.",
            rate_limited=False, sent_at=None, error=False
        )

    return _render_checkout_review(request, ctx=ctx)


@require_GET
def checkout_review(request):
    ctx = _get_checkout_context(request)

    if not ctx:
        log_event(logger, logging.WARNING, "checkout.review.session_missing")
        return hx_load_modal(
            reverse("hr_shop:checkout_details"),
            after_settle={"showMessage": {"text": "Your session is invalid or has expired. Please try again."}}
        )

    email = ctx['customer'].email

    if not is_email_confirmed_for_checkout(request, email):
        log_event(logger, logging.INFO, "checkout.review.email_unconfirmed", customer_id=ctx["customer"].id)
        return _render_checkout_awaiting_confirmation(
            request, email=email, message="Please confirm your email to continue.", rate_limited=False, sent_at=None, error=False
        )

    return _render_checkout_review(request, ctx=ctx)


@require_POST
def checkout_create_order(request):
    items = list(_iter_cart_items_for_order(request))
    if not items:
        log_event(logger, logging.WARNING, "checkout.order.create.empty_cart")
        return hx_load_modal(
            reverse("hr_shop:view_cart"),
            after_settle={"showMessage": {"text": "Your cart is empty."}}
        )

    ctx = _get_checkout_context(request)
    if not ctx:
        log_event(logger, logging.WARNING, "checkout.order.create.session_missing")
        return hx_load_modal(
            reverse("hr_shop:checkout_resume"),
            after_settle={"showMessage": {"text": "Your session is invalid or has expired. Please try again."}}
        )

    customer = ctx["customer"]
    shipping_address = ctx["address"]
    note = ctx["note"]

    if not is_email_confirmed_for_checkout(request, customer.email):
        log_event(logger, logging.WARNING, "checkout.order.create.email_unconfirmed", customer_id=customer.id)
        return _render_checkout_awaiting_confirmation(
            request, email=customer.email, message="Please confirm your email to continue.", rate_limited=False, sent_at=None, error=False
        )

    with transaction.atomic():
        # Lock the most recent active draft for this customer
        draft = (
            CheckoutDraft.objects
            .select_for_update()
            .filter(customer=customer, used_at__isnull=True, expires_at__gt=timezone.now())
            .order_by("-created_at")
            .first()
        )

        if not draft or not draft.is_valid():
            if not draft:
                log_event(logger, logging.INFO, 'checkout.order.create.draft_missing', customer_id=customer.id)
            else:
                log_event(logger, logging.INFO, 'checkout.order.create.draft_invalid', draft_id=draft.id, used_at=str(draft.used_at), customer_id=customer.id)
            return hx_load_modal(
                reverse("hr_shop:checkout_details"),
                after_settle={"showMessage": {"text": "Your checkout session expired. Please restart checkout."}}
            )

        # Idempotent: if draft already has an order, go pay for that order
        if draft.order_id:
            order_id = int(draft.order_id)
            log_event(logger, logging.INFO, "checkout.order.create.found_existing", customer_id=customer.id, draft_id=draft.id, order_id=order_id)
            pay_url = reverse("hr_shop:checkout_pay", args=[order_id])
            return hx_load_modal(pay_url)

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer=customer,
            email=customer.email,
            shipping_address=shipping_address,
            total=Decimal("0.00"),
            order_status=OrderStatus.RECEIVED,
            payment_status=PaymentStatus.UNPAID,
            note=note or None
        )

        subtotal = Decimal("0.00")
        for line in items:
            variant = line["variant"]
            quantity = int(line["quantity"])
            unit_price = Decimal(str(line["unit_price"]))
            line_total = unit_price * quantity

            OrderItem.objects.create(order=order, variant=variant, quantity=quantity, unit_price=unit_price)
            subtotal += line_total

        tax = Decimal("0.00")
        shipping = Decimal("0.00")
        order.total = subtotal + tax + shipping
        order.save(update_fields=["total", "updated_at"])

        # Link draft to the order for idempotency
        draft.order = order
        draft.save(update_fields=["order"])

    log_event(logger, logging.INFO, "checkout.order.create.created",
              order_id=order.id, customer_id=customer.id, draft_id=draft.id if draft else None, item_count=len(items), total=str(order.total))

    return hx_load_modal(reverse('hr_shop:checkout_pay', args=[order.id]))


@require_GET
@ensure_csrf_cookie
def checkout_pay(request, order_id: int):
    """
    Display payment form for an order.
    """
    order = get_object_or_404(Order, pk=int(order_id))

    # -------------------------------------------------------------------------
    # Check if already paid
    # -------------------------------------------------------------------------
    if order.payment_status == PaymentStatus.PAID:
        receipt_token = ""

        # Generate receipt token for guests
        if not request.user.is_authenticated:
            receipt_token = generate_order_receipt_token(order_id=order.id, email=order.email)

        resp = _render_order_payment_result_modal(request, order, receipt_token)

        # Clear guest token cookie if guest
        if not request.user.is_authenticated:
            resp.delete_cookie('guest_checkout_token')

        return resp

    # -------------------------------------------------------------------------
    # Authenticated users
    # -------------------------------------------------------------------------
    if request.user.is_authenticated:
        if getattr(order, 'user_id', None) != request.user.id:
            return hx_trigger({'showMessage': {'text': 'Not Authorized'}}, status=403)

        return render(request, "hr_shop/checkout/_checkout_pay.html", {
            "order":                  order,
            "stripe_publishable_key": secrets.read_secret('STRIPE_PUBLIC_KEY'),
            "client_secret":          "",
            "checkout_ctx_token":     ""
        })

    # -------------------------------------------------------------------------
    # Guest users: validate checkout context
    # -------------------------------------------------------------------------
    guest_ctx, error_response = _validate_guest_checkout(request, order_id)

    if error_response:

        draft = (
            CheckoutDraft.objects
            .select_related('customer', 'address', 'order')
            .filter(order_id=order_id, used_at__isnull=True)
            .order_by('-created_at')
            .first()
        )

        if draft and draft.is_valid():
            request.session['checkout_customer_id'] = draft.customer_id
            request.session['checkout_address_id'] = draft.address_id
            request.session['checkout_note'] = draft.note or ''
            request.session.modified = True

            guest_checkout_token = generate_guest_checkout_token(
                customer_id=int(draft.customer_id),
                draft_id=int(draft.id),
                order_id=int(order_id)
            )

            resp = render(request, 'hr_shop/checkout/_checkout_pay.html', {
                'order': order,
                'stripe_publishable_key': secrets.read_secret('STRIPE_PUBLIC_KEY'),
                'client_secret': '',
                'checkout_ctx_token': guest_checkout_token
            })

            resp.set_cookie(
                'guest_checkout_token',
                guest_checkout_token,
                max_age=CHECKOUT_CTX_MAX_AGE,
                httponly=True,
                samesite='Lax',
                secure=not settings.DEBUG
            )

            log_event(logger, logging.INFO, 'checkout.pay.token_regenerated', order_id=order_id, draft_id=draft.id)

            return resp
        else:
            return render(request, 'hr_shop/checkout/_checkout_session_expired.html', {
                'message': 'Your checkout session has expired. Please restart checkout from your cart.',
                'restart_url': reverse('hr_shop:view_cart')
            }, status=400)

    # -------------------------------------------------------------------------
    # Generate token and render payment form
    # -------------------------------------------------------------------------
    checkout_ctx_token = generate_guest_checkout_token(
        customer_id=int(guest_ctx.draft.customer_id),
        draft_id=int(guest_ctx.draft.id),
        order_id=int(order.id),
    )

    resp = render(request, "hr_shop/checkout/_checkout_pay.html", {
        "order":                  order,
        "stripe_publishable_key": secrets.read_secret('STRIPE_PUBLIC_KEY'),
        "client_secret":          "",
        "checkout_ctx_token":     checkout_ctx_token
    })

    # Persist guest context for payment API calls
    resp.set_cookie(
        "guest_checkout_token",
        checkout_ctx_token,
        max_age=CHECKOUT_CTX_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=not settings.DEBUG
    )

    return resp



#----------------------------------------------------------------------
#  Email confirmation flow
#----------------------------------------------------------------------

@require_GET
def email_confirmation_process_response(request, token: str):
    checkout_email_token = verify_checkout_email_token(token)
    index_url = reverse("index")
    details_url = reverse("hr_shop:checkout_details")
    if not checkout_email_token:
        log_event(logger, logging.WARNING, "checkout.confirmation.invalid_token")
        return redirect(f"{index_url}?handoff=email_confirmed&modal_url={details_url}#parallax-section-merch")  # TODO showMessage, possible dedicated modal for failure states

    # Dataclass fields are guaranteed valid here
    norm_email = normalize_email(checkout_email_token.email)
    draft_id = int(checkout_email_token.draft_id)

    with transaction.atomic():
        draft = (
            CheckoutDraft.objects
            .select_for_update()
            .filter(id=draft_id)
            .first()
        )
        if not draft:
            log_event(logger, logging.WARNING, "checkout.confirmation.draft_missing", draft_id=draft_id, email=norm_email)
            return redirect(f"{index_url}?handoff=email_confirmed&modal_url={details_url}#parallax-section-merch")  # TODO showMessage

        if normalize_email(draft.email) != norm_email:
            log_event(logger, logging.WARNING, "checkout.confirmation.email_mismatch", draft_id=draft.id, draft_email=draft.email, token_email=norm_email)
            return redirect(f"{index_url}?handoff=email_confirmed&modal_url={details_url}#parallax-section-merch")  # TODO showMessage

        ConfirmedEmail.mark_confirmed(norm_email)

        # If they already made an order, this click should just send them there.
        if draft.order_id:
            receipt = generate_order_receipt_token(order_id=draft.order_id, email=normalize_email(draft.email or ""))
            url = reverse("hr_shop:order_payment_result")
            return redirect(f"{url}?t={receipt}")

        if not draft.is_valid():
            log_event(logger, logging.WARNING, "checkout.confirmation.draft_expired", draft_id=draft.id)
            return redirect(f"{index_url}?handoff=email_confirmed&modal_url={details_url}#parallax-section-merch")  # TODO showMessage

        # Restore session context
        request.session["checkout_customer_id"] = draft.customer_id
        request.session["checkout_address_id"] = draft.address_id
        request.session["checkout_note"] = draft.note or ""
        request.session.modified = True

        # Restore cart only if empty
        existing_cart = request.session.get(CART_SESSION_KEY) or {}
        if not existing_cart:
            _restore_cart_from_draft(request, draft)

    log_event(logger, logging.INFO, "checkout.confirmation.processed", draft_id=draft_id, customer_id=draft.customer_id)

    success_url = reverse("hr_shop:email_confirmation_success")
    resp = redirect(f"{index_url}?modal=email_confirmed&handoff=email_confirmed&modal_url={success_url}#parallax-section-merch")
    resp.delete_cookie('guest_checkout_token')
    return resp


def email_confirmation_success(request):
    return render(request, "hr_shop/checkout/_email_confirmation_success.html")


@require_GET
def email_confirmation_status(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        log_event(logger, logging.WARNING, 'checkout.email.status.missing_context')
        messages.error(request, 'Session expired')
        return render(request, "hr_shop/checkout/_checkout_session_expired.html", status=400)

    # Use the same rules as checkout (authenticated users count too)
    if is_email_confirmed_for_checkout(request, ctx["customer"].email):
        return _render_checkout_review(request, ctx=ctx)

    return HttpResponse(status=204)


@require_POST
def email_confirmation_resend(request):
    ctx = _get_checkout_context(request)
    if not ctx:
        log_event(logger, logging.WARNING, "checkout.confirmation.resend.session_missing")
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect("hr_shop:checkout_details")

    customer = ctx["customer"]

    cart_payload = _cart_snapshot(request)

    draft = _get_or_create_active_draft(
        customer=customer,
        email=customer.email,
        address=ctx["address"],
        note=ctx["note"],
        cart_payload=cart_payload
    )

    try:
        send_checkout_confirmation_email(request=request, email=customer.email, draft_id=draft.id)

        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "Confirmation link sent. Please check your inbox.",
            "rate_limited": False,
            "sent_at": timezone.now()
        })

    except RateLimitExceeded:
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "Too many emails sent. Please check your inbox (including spam folder) or try again later.",
            "rate_limited": True,
            "sent_at": None
        })

    except EmailSendError:
        return render(request, "hr_shop/checkout/_checkout_awaiting_confirmation.html", {
            "email": customer.email,
            "message": "Could not send email. Please try again.",
            "rate_limited": False,
            "sent_at": None,
            "error": True
        })



#----------------------------------------------------------------------
#  Order / receipt
#----------------------------------------------------------------------

@require_GET
def order_payment_result(request):
    order_receipt_token = (request.GET.get("t") or "").strip()
    if not order_receipt_token:
        return HttpResponse("Missing token.", status=400)

    claims = verify_order_receipt_token(order_receipt_token)
    if not claims:
        log_event(logger, logging.WARNING, "checkout.receipt.invalid_token")
        return HttpResponse("Invalid or expired receipt link", status=403)

    order = get_object_or_404(Order.objects.select_related("customer", "shipping_address"), pk=int(claims.order_id))

    if not _user_is_authorized_for_payment_result(request, order, order_receipt_token):
        log_event(logger, logging.WARNING, "checkout.receipt.unauthorized", order_id=order.id, has_token=True)
        return HttpResponse("Not authorized to view this receipt.", status=403)

    return _render_order_payment_result_modal(request, order, order_receipt_token)


@require_POST  # TODO implement different receipt id logic
def order_send_receipt_email(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)

    if not _is_allowed_to_email_receipt(request, order):
        log_event(logger, logging.WARNING, "checkout.receipt.send_forbidden", order_id=order.id)
        return HttpResponse(status=404)

    if not order.email:
        log_event(logger, logging.WARNING, "checkout.receipt.missing_email", order_id=order.id)
        return hx_trigger({"showMessage": {"text": "No email address is associated with this order."}}, status=400)

    rl_key = f"receipt_resend:{order.id}"
    if not _rate_limit_ok(request, key=rl_key, cooldown_s=_RECEIPT_RESEND_COOLDOWN_SECONDS):
        log_event(logger, logging.WARNING, "checkout.receipt.rate_limited", order_id=order.id)
        return hx_trigger({"showMessage": {"text": "Please wait a moment before resending the receipt."}}, status=429)

    try:
        send_order_receipt_email(order=order, request=request)
        log_event(logger, logging.INFO, "checkout.receipt.sent", order_id=order_id, email=order.email)
        return hx_trigger({"showMessage": {"text": "Receipt email sent."}})

    except (EmailProviderError) as exc:
        log_event(logger, logging.ERROR, "checkout.receipt.send_failed", order_id=order.id, email=order.email, error=str(exc), exc_info=True)
        return hx_trigger({"showMessage": {"text": "Receipt email failed to send. Try again shortly."}}, status=500)


@require_POST
def dismiss_post_purchase_cta(request, order_id: int):
    request.session[f"pp_cta_dismissed:{order_id}"] = True
    request.session.modified = True  # Ensure Django saves the session
    return HttpResponse("", status=200, content_type="text/html")
