# hr_shop/views/checkout.py

import json
import logging
from decimal import Decimal
from typing import Dict, Any

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from hr_common.models import Address
from hr_core.utils import http
from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import verify_checkout_email_token
from hr_payment.providers import get_payment_provider
from hr_shop.cart import get_cart
from hr_shop.exceptions import EmailSendError, RateLimitExceeded
from hr_shop.forms import CheckoutDetailsForm
from hr_shop.models import Customer, Order, OrderItem, ProductVariant, ConfirmedEmail
from hr_shop.services.email_confirmation import is_email_confirmed_for_checkout, send_checkout_confirmation_email

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_existing_customer_for_user(user):
    if not user or not user.is_authenticated:
        return None
    return Customer.objects.filter(user=user).order_by('-created_at').first()


def _get_most_recent_address_for_customer(customer: Customer):
    if not customer:
        return None
    last_order = (
        Order.objects
        .filter(customer=customer, shipping_address__isnull=False)
        .order_by('-created_at')
        .select_related('shipping_address')
        .first()
    )
    return last_order.shipping_address if last_order else None


def _build_address_from_form(form: CheckoutDetailsForm) -> Address:
    street1 = form.cleaned_data['street_address'].strip()
    street2 = form.cleaned_data.get('street_address_line2', '').strip() or None
    unit = form.cleaned_data.get('unit', '').strip() or None

    address = Address.objects.create(
        street_address=street1,
        street_address_line2=street2,
        building_type=form.cleaned_data['building_type'],
        unit=unit,
        city=form.cleaned_data['city'].strip(),
        subdivision=form.cleaned_data['subdivision'].strip(),
        postal_code=form.cleaned_data['postal_code'].strip(),
        country='United States'
    )

    return address


def _get_or_create_customer(email: str, user, form: CheckoutDetailsForm) -> Customer:
    """
    Get or create a customer record.
    Updates existing customer info if form data is newer/different.
    """
    customer, created = Customer.objects.get_or_create(
        email=normalize_email(email),
        defaults={
            'user':       user if user and user.is_authenticated else None,
            'first_name': form.cleaned_data['first_name'].strip(),
            'middle_initial': form.cleaned_data.get('middle_initial', '').strip() or None,
            'last_name':  form.cleaned_data['last_name'].strip(),
            'suffix': form.cleaned_data.get('suffix', '').strip() or None,
            'phone': form.cleaned_data.get('phone', '').strip() or None
        }
    )

    updated_fields = []
    if not created:
        first_name = form.cleaned_data['first_name'].strip()
        middle_initial = form.cleaned_data.get('middle_initial', '').strip()
        last_name = form.cleaned_data['last_name'].strip()
        suffix = form.cleaned_data.get('suffix', '').strip()
        phone = form.cleaned_data.get('phone', '').strip()

        if first_name and customer.first_name != first_name:
            customer.first_name = first_name
            updated_fields.append('first_name')
        if middle_initial and customer.middle_initial != middle_initial:
            customer.middle_initial = middle_initial
            updated_fields.append('middle_initial')
        if last_name and customer.last_name != last_name:
            customer.last_name = last_name
            updated_fields.append('last_name')
        if suffix and customer.suffix != suffix:
            customer.suffix = suffix
            updated_fields.append('suffix')
        if phone and customer.phone != phone:
            customer.phone = phone
            updated_fields.append('phone')
        if user and user.is_authenticated and customer.user_id is None:
            customer.user = user
            updated_fields.append('user')

        if updated_fields:
            customer.save(update_fields=updated_fields + ['updated_at'])

    return customer


def _iter_cart_items_for_order(request):
    """
    Iterate cart items in a format suitable for order creation.
    Yields dicts with 'variant', 'quantity', 'unit_price' keys.
    """
    cart = get_cart(request)
    for item in cart:
        variant = item.get("variant")
        quantity = int(item.get("quantity", 1))

        if variant is None:
            variant_id = item.get("variant_id")
            if variant_id is not None:
                try:
                    variant = ProductVariant.objects.get(pk=variant_id)
                except ProductVariant.DoesNotExist:
                    continue

        # if variant is None:
        #     continue

        unit_price_raw = item.get("unit_price") or item.get("price") or variant.price
        unit_price = Decimal(str(unit_price_raw))

        yield {
            "variant":    variant,
            "quantity":   quantity,
            "unit_price": unit_price,
        }


def _clear_cart(request) -> None:
    """
    Clear the cart from the session.
    """
    if "cart" in request.session:
        del request.session["cart"]
        request.session.modified = True


def _render_checkout_review(request):
    """
    Helper to render the checkout review page with all context.
    """
    items = list(_iter_cart_items_for_order(request))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    subtotal = sum(
        (line["unit_price"] * line["quantity"] for line in items),
        Decimal("0.00")
    )

    customer_id = request.session.get('checkout_customer_id')
    address_id = request.session.get('checkout_address_id')
    note = request.session.get('checkout_note', '')

    customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
    address = Address.objects.filter(pk=address_id).first() if address_id else None

    tax = Decimal("0.00")  # placeholder
    shipping = Decimal("0.00")  # placeholder
    total = subtotal + tax + shipping

    context = {
        "items":    items,
        "subtotal": subtotal,
        "tax":      tax,
        "shipping": shipping,
        "total":    total,
        'customer': customer,
        'address':  address,
        'note':     note
    }

    template = 'hr_shop/_checkout_review.html' if http.is_htmx(request) else 'hr_shop/checkout_review.html'

    return render(request, template, context)

#
# def is_email_confirmed_for_checkout(request, email: str) -> bool:
#     """
#     Hook to decide whether the given email is confirmed and allowed
#     to place an order.
#
#     For now:
#       - If the user is authenticated and their account email matches
#         the entered email (case-insensitive), treat as confirmed.
#       - Guest emails (anonymous user) are NOT treated as confirmed yet.
#
#     You can later replace this with your real email-verification logic,
#     e.g. integrating with allauth or a custom confirmation table.
#     """
#     normalized_email = email.strip().casefold()
#     user = getattr(request, "user", None)
#
#     if user and user.is_authenticated and user.email:
#         return user.email.strip().casefold() == normalized_email
#
#     # Guests are not yet confirmed – implement your real flow here.
#     return False


def _get_checkout_context(request) -> dict | None:
    """
    Get checkout context from session. Returns None if session is invalid.
    Returns dict with 'customer', 'address', 'note' if valid.
    """
    customer_id = request.session.get('checkout_customer_id')
    address_id = request.session.get('checkout_address_id')

    if not customer_id or not address_id:
        return None

    try:
        customer = Customer.objects.get(pk=customer_id)
        address = Address.objects.get(pk=address_id)
    except (Customer.DoesNotExist, Address.DoesNotExist):
        return None

    return {
        'customer': customer,
        'address': address,
        'note': request.session.get('checkout_note', '')
    }

# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

# At some point add request.session['last_confirmation_link'] = confirm_url  to appropriate views to help with troubleshooting


@require_GET
def checkout_details(request):
    """
    Show the order details form (contact + shipping info).
    Pre-fills form with known customer data if available.
    """
    user = getattr(request, 'user', None)

    initial: Dict[str, Any] = {
        'email':                '',
        'phone':                '',
        'first_name':           '',
        'middle_initial':       '',
        'last_name':            '',
        'suffix':               '',
        'street_address':       '',
        'street_address_line2': '',
        'building_type':        'single_family',
        'unit':          '',
        'city':                 '',
        'subdivision':                '',
        'postal_code':             '',
        'special_instructions': '',
    }

    customer = _get_existing_customer_for_user(user)
    if customer:
        initial['email'] = customer.email
        initial['phone'] = customer.phone or ''
        initial['first_name'] = customer.first_name
        initial['middle_initial'] = customer.middle_initial or ''
        initial['last_name'] = customer.last_name
        initial['suffix'] = customer.suffix or ''

        addr = _get_most_recent_address_for_customer(customer)
        if addr:
            initial['street_address'] = addr.street_address
            initial['street_address_line2'] = addr.street_address_line2
            initial['building_type'] = addr.building_type
            initial['unit'] = addr.unit
            initial['city'] = addr.city
            initial['subdivision'] = addr.subdivision
            initial['postal_code'] = addr.postal_code

    elif user and user.is_authenticated:
        initial['email'] = user.email or ''
        initial['first_name'] = user.first_name or ''
        initial['middle_initial'] = user.middle_initial or ''
        initial['last_name'] = user.last_name or ''
        initial['suffix'] = user.suffiix or ''

    form = CheckoutDetailsForm(initial=initial)
    template = 'hr_shop/_checkout_details.html' if http.is_htmx(request) else 'hr_shop/checkout_details.html'

    return render(request, template, {'form': form})


@require_POST
def checkout_details_submit(request):
    """
    Handle POST of the checkout details form.
        - Validate form data
        - Creates/updates Customer and Address records
        - Checks email confirmation status
        - Sends confirmation email if needed, or proceeds to review
    """
    form = CheckoutDetailsForm(request.POST)

    if not form.is_valid():
        template = 'hr_shop/_checkout_details.html' if http.is_htmx(request) else 'hr_shop/checkout_details.html'
        return render(request, template, {'form': form})

    user = getattr(request, 'user', None)
    email = form.cleaned_data['email'].strip()

    if user and user.is_authenticated:
        if normalize_email(email) != normalize_email(user.email):
            form.add_error('email', 'Please use the email address associated with your account.')
            template = 'hr_shop/_checkout_details.html' if http.is_htmx(request) else 'hr_shop/checkout_details.html'
            return render(request, template, {'form': form})

    customer = _get_or_create_customer(email, user, form)
    address = _build_address_from_form(form)
    note = form.cleaned_data.get('note', '').strip()

    request.session['checkout_customer_id'] = customer.id
    request.session['checkout_address_id'] = address.id
    request.session['checkout_note'] = note
    request.session.modified = True

    if is_email_confirmed_for_checkout(request, email):
        return _render_checkout_review(request)

    try:
        send_checkout_confirmation_email(
            request=request,
            email=email,
            customer_id=customer.id,
            address_id=address.id,
            note=note
        )
    except RateLimitExceeded:
        context = {
            'email': email,
            'message': 'Too many confirmation emails sent. Please check your inbox (including spam folder) or try again in an hour.',
            'rate_limited': True,
            'sent_at': None
        }
        template = 'hr_shop/_checkout_awaiting_confirmation.html' if http.is_htmx(request) else 'hr_shop/checkout_awaiting_confirmation.html'
        return render(request, template, context)

    except EmailSendError:
        messages.error(request, 'Could not send confirmation email. Please try again.')
        template = 'hr_shop/_checkout_details.html' if http.is_htmx(request) else 'hr_shop/checkout_details.html'
        return render(request, template, {'form': form})

    context = {
        'email': email,
        'message': "We've sent a confirmation link to your email. Please check your inbox and click the link to continue.",
        'rate_limited': False,
        'sent_at': timezone.now()
    }
    template = 'hr_shop/_checkout_awaiting_confirmation.html' if http.is_htmx(request) else 'hr_shop/checkout_awaiting_confirmation.html'
    return render(request, template, context)


@require_GET
def confirm_checkout_email(request, token: str):
    """
    Handle email confirmation link click.
    Verifies token, marks email as confirmed, resotres session subdivision, redirects to review.
    """
    payload = verify_checkout_email_token(token)

    if payload is None:
        messages.error(request, 'This confirmation link is invalid or has expired. Please request a new one.')
        return redirect('hr_shop:checkout_details')

    email = payload.get('email')
    if not email:
        messages.error(request, 'Invalid confirmation link.')
        return redirect('hr_shop:checkout_details')

    ConfirmedEmail.mark_confirmed(email)
    logger.info(f'Email confirmed: {email}')

    customer_id = payload.get('cid')
    address_id = payload.get('aid')
    note = payload.get('note', '')

    if customer_id and address_id:
        customer_exists = Customer.objects.filter(pk=customer_id).exists()
        address_exists = Address.objects.filter(pk=address_id).exists()

        if customer_exists and address_exists:
            request.session['checkout_customer_id'] = customer_id
            request.session['checkout_address_id'] = address_id
            request.session['checkout_note'] = note
            request.session.modified = True
        else:
            messages.warning(request, 'Your email is confirmed, but your checkout session expired. Please re-enter your details.')
            return redirect('hr_shop:checkout_details')

    # messages.success(request, 'Email confirmed! You can now complete your order.')
    # return redirect('hr_shop:checkoout_review')
    return render(request, 'hr_shop/_email_confirmed.html', {
        'redirect_url': reverse('hr_shop:checkout_review'),
        'redirect_delay': 3
    })


@require_GET
def check_email_confirmed(request):
    """
    HTMX polling endpoint to check if email has been confirmed.
    Returns the review page if confirmed, or 284 No Content if still waiting.
    """
    # customer_id = request.session.get('checkout_customer_id')
    #
    # if not customer_id:
    #     return render(request, 'hr_shop/_checkout_session_expired.html')
    #
    # try:
    #     customer = Customer.objects.get(pk=customer_id)
    # except Customer.DoesNotExist:
    #     return render(request, 'hr_shop/_checkout_session_expired.html')
    #
    # if ConfirmedEmail.is_confirmed(customer.email):
    #     return _render_checkout_review(request)
    #
    # return HttpResponse(status=204)

    ctx = _get_checkout_context(request)
    if not ctx:
        return render(request, 'hr_shop/_checkout_session_expired.html')

    if ConfirmedEmail.is_confirmed(ctx['customer'].email):
        return _render_checkout_review(request)

    # Still waiting - return 2-4 so HTMX doesn't swap
    return HttpResponse(status=204)


@require_POST
def resend_checkout_confirmation(request):
    """
    Resend the confirmation email if the user didn't receive it.
    Subject to rate limiting.
    """
    # customer_id = request.session.get('checkout_customer_id')
    # address_id = request.session.get('checkout_address_id')
    # note = request.session.get('checkout_note', '')
    #
    # if not customer_id:
    #     messages.error(request, 'Please fill ouot the checkout form first.')
    #     return redirect('hr_shop:checkout_details')
    #
    # try:
    #     customer = Customer.objects.get(pk=customer_id)
    # except Customer.DoesNotExist:
    #     messages.error(request, 'Could not find your information. Please try again.')
    #     return redirect('hr_shop:checkout_details')

    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect('hr_shop:checkout_details')

    customer = ctx['customer']
    address = ctx['address']

    try:
        send_checkout_confirmation_email(
            request=request,
            email=customer.email,
            customer_id=customer.id,
            address_id=address.id,
            note=ctx['note']
        )
        context = {
            'email': customer.email,
            'message': "We've sent another confirmation link. Please check your inbox.",
            'rate_limited': False,
            'sent_at': timezone.now()
        }
    except RateLimitExceeded:
        context = {
            'email': customer.email,
            'message': "Too many emails sent. Please check your inbox (including spam folder) or try again later.",
            'rate_limited': True,
            'sent_at': None
        }
    except EmailSendError:
        context = {
            'email': customer.email,
            'message': "Could not send email. Please try again.",
            'rate_limited': False,
            'sent_at': None,
            'error': True
        }

    template = 'hr_shop/_checkout_awaiting_confirmation.html' if http.is_htmx(request) else 'hr_shop/checkout_awaiting_confirmation.html'
    return render(request, template, context)


@require_GET
def checkout_review(request):
    """
    Show the checkout review modal/page with cart contents and totals.
    Requires email to be confirmed for guests.
    """
    # customer_id = request.session.get('checkout_customer_id')
    # address_id = request.session.get('checkout_address_id')
    #
    # if not customer_id or not address_id:
    #     messages.info('Please enter your details to continue.')
    #     return redirect('hr_shop:checkout_details')
    #
    # try:
    #     customer = Customer.objects.get(pk=customer_id)
    # except Customer.DoesNotExist:
    #     messages.warning(request, "Your session expired. Please re-enter your details.")
    #     return redirect('hr_shop:checkout_details')

    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect('hr_shop:checkout_details')

    if not is_email_confirmed_for_checkout(request, ctx.get('customer').email):
        messages.warning(request, "Please confirm your email address to continue.")
        return redirect('hr_shop:checkout_details')

    return _render_checkout_review(request)


@require_POST
def checkout_create_order(request):
    """
    Create an Order from the current cart and checkout session.
    Requires confirmed email. Hands off to payment provider.
    """
    items = list(_iter_cart_items_for_order(request))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    ctx = _get_checkout_context(request)
    if not ctx:
        messages.error(request, "Your session is invalid or has expired. Please try again.")
        return redirect('hr_shop:checkout_details')

    customer = ctx.get('customer')
    note = ctx.get('note')
    shipping_address = ctx.get('address')

    # customer_id = request.session.get('checkout_customer_id')
    # address_id = request.session.get('checkout_address_id')
    # note = request.session.get('checkout_note', '').strip()
    #
    # if not customer_id or not address_id:
    #     messages.error(request, "Your checkout session is missing details. Please start again.")
    #     return redirect('hr_shop:checkout_details')
    #
    # try:
    #     customer = Customer.objects.get(pk=customer_id)
    # except Customer.DoesNotExist:
    #     messages.error(request, "Could not find your customer profile. Please re-enter your details.")
    #     return redirect('hr_shop:checkout_details')
    #
    # try:
    #     shipping_address = Address.objects.get(pk=address_id)
    # except Address.DoesNotExist:
    #     messages.error(request, "Could not find your shipping address. Please re-enter your details.")
    #     return redirect('hr_shop:checkout_details')

    if not is_email_confirmed_for_checkout(request, customer.email):
        messages.error(request, "Please confirm your email address before placing an order.")
        return redirect('hr_shop:checkout_review')

    order_kwargs = {
        "customer":         customer,
        "email":            normalize_email(customer.email),
        "shipping_address": shipping_address,
        "total":            Decimal("0.00"),
        "status":           "pending",
    }

    if note:
        order_kwargs["note"] = note

    order = Order.objects.create(**order_kwargs)

    subtotal = Decimal('0.00')
    for line in items:
        variant = line['variant']
        quantity = line['quantity']
        unit_price = line['unit_price']
        line_total = unit_price * quantity

        OrderItem.objects.create(
            order=order,
            variant=variant,
            quantity=quantity,
            unit_price=unit_price
        )
        subtotal += line_total

    tax = Decimal('0.00')
    shipping = Decimal('0.00')
    total = subtotal + tax + shipping

    order.total = total
    order.save(update_fields=['total', 'updated_at'])

    provider = get_payment_provider()
    session = provider.create_checkout_session(order)

    redirect_url = session.get('url') or reverse(
        'hr_shop:order_thank_you', args=[order.id]
    )

    if order.status == 'paid':
        _clear_cart(request)
        messages.success(request, "Payment succeeded! Thank you for your order.")
    else:
        messages.info(request, "Redirecting to payment provider...")

    if http.is_htmx(request):
        return HttpResponse(status=204, headers={
            'HX-Trigger': json.dumps({
                'messageBoxClosed': f'Payment succeeded! Thank you for your order!'
            })
        })

    return redirect(redirect_url)


@require_GET
def order_thank_you(request, order_id: int):
    """
    Simple thank-you page for after payment succeeds.
    If HTMX: returns a fragment for a modal.
    If not: full page.
    """
    order = get_object_or_404(Order, pk=order_id)
    context = {"order": order}

    if http.is_htmx(request):
        return HttpResponse("Thank you for your order!", status=204)
    return render(request, 'hr_shop/order_thank_you.html', context)
