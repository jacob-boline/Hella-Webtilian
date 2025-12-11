# hr_shop/views/checkout.py

from decimal import Decimal
from typing import Dict, Any

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from hr_common.models import Address
from hr_shop.models import Customer, Order, OrderItem, ProductVariant
from hr_shop.cart import get_cart
from hr_shop.forms import CheckoutDetailsForm
from hr_core.utils import http
from hr_core.utils.email import normalize_email
from hr_payment.providers import get_payment_provider


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
        .filter(customer=customer, shipping_address__is_null=False)
        .order_by('-created_at')
        .select_related('shipping_address')
        .first()
    )
    return last_order.shipping_address if last_order else None


def _build_address_from_form(form: CheckoutDetailsForm) -> Address:
    street1 = form.cleaned_data['street_address'].strip()
    street2 = form.cleaned_data.get('street_address_line2', '').strip()
    unit = form.cleaned_data.get('unit_number', '').strip() or None

    address, created = Address.objects.create(
        street_address=street1,
        street_address_line2=street2,
        unit=unit,
        city=form.cleaned_data['city'].strip(),
        subdivision=form.cleaned_data['state'].strip(),
        postal_code=form.cleaned_data['zip_code'].strip(),
        country='United States'
    )

    return address


def _get_or_create_customer(email: str, user, form: CheckoutDetailsForm) -> Customer:
    """
    Normalize email, find or create a Customer.
    Attach the given user if non-null and not already linked.
    """
    customer, created = Customer.objects.get_or_create(
        email=normalize_email(email),
        defaults={
            'user':       user if user and user.is_authenticated else None,
            'first_name': form.cleaned_data['first_name'].strip(),
            'middle_initial': form.cleaned_data.get('middle_initial', '').strip() or None,
            'last_name':  form.cleaned_data['last_name'].strip(),
            'phone': form.cleaned_data.get('phone', '').strip() or None
        }
    )

    updated_fields = []
    if not created:
        first_name = form.cleaned_data['first_name'].strip()
        middle_initial = form.cleaned_data.get('middle_initial', '').strip()
        last_name = form.cleaned_data['last_name'].strip()
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
        if phone and customer.phone != phone:
            customer.phone = phone
            updated_fields.append('phone')
        if user and user.is_authenticated and customer.user_id is None:
            customer.user = user
            updated_fields.append('user')

        if updated_fields:
            customer.save(update_fields=updated_fields + ['updated_at'])

    return customer


@require_GET
def checkout_details(request):
    """
    Show the order details form (contact + shipping info).
    If HTMX: returns modal content partial
    If non-HTMX: returns full page extending base.html.
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
        'unit_number':          '',
        'city':                 '',
        'state':                '',
        'zip_code':             '',
        'special_instructions': '',
    }

    customer = _get_existing_customer_for_user(user)
    if customer:
        initial['email'] = customer.email
        initial['phone'] = customer.phone or ''
        initial['first_name'] = customer.first_name
        initial['middle_initial'] = customer.middle_initial or ''
        initial['last_name'] = customer.last_name

        addr = _get_most_recent_address_for_customer(customer)
        if addr:
            initial['street_address'] = addr.street_address
            initial['street_address_line2'] = addr.street_address_line2
            initial['city'] = addr.city
            initial['state'] = addr.subdivision
            initial['zip_code'] = addr.postal_code

    else:
        if user and user.is_authenticated:
            initial['email'] = user.email or ''
            initial['first_name'] = user.first_name or ''
            initial['last_name'] = user.last_name or ''

    form = CheckoutDetailsForm(initial=initial)

    if http.is_htmx(request):
        template = 'hr_shop/_checkout_details.html'
    else:
        template = 'hr_shop/checkout_details.html'

    return render(request, template, {'form': form})


@require_POST
def checkout_details_submit(request):
    """
        Handle POST of the order details form.
        - Validate data
        - Ensure/Update Customer
        - Create/Reuse Address
        - Stash IDs + note in session
        - If a new Customer was created, display a message about email confirmation.
        - Redirect to checkout_review (or return partial if you want).
        """
    form = CheckoutDetailsForm(request.POST)

    if not form.is_valid():
        if http.is_htmx(request):
            template = 'hr_shop/_checkout_details.html'
        else:
            template = 'hr_shop/checkout_details.html'
        return render(request, template, {'form': form})

    user = getattr(request, 'user', None)
    email = form.cleaned_data['email'].strip()

    if user and user.is_authenticated:
        if normalize_email(email) != normalize_email(user.email):
            form.add_error('email', 'Use the email address associated with your account.')
            if http.is_htmx(request):
                template = 'hr_shop/_checkout_details.html'
            else:
                template = 'hr_shop/checkout_details.html'
            return render(request, template, {'form': form})

    customer, created = _get_or_create_customer(email, user, form)
    address = _build_address_from_form(form)
    note = form.cleaned_data.get('note', '').strip()

    request.session['checkout_customer_id'] = customer.id
    request.session['checkout_address_id'] = address.id
    request.session['checkout_note'] = note
    request.session.modified = True

    if created:
        # confirmation email logic here
        messages.info(request, "We've created a customer profile for you. Please check your email to confirm.")

    # redirect_url = reverse('hr_shop:checkout_review')

    if http.is_htmx(request):
        template = 'hr_shop/_checkout_review.html'
    else:
        template = 'hr_shop/checkout_review.html'

    return render(request, template)


def _iter_cart_items_for_order(request):
    """
    Helper to iterate the current cart in a way suitable for building an order.

    This assumes your Cart's __iter__ yields dict-like items with at least:
      - item["variant"]  -> ProductVariant instance
      - item["quantity"] -> int

    If your Cart uses a different shape, adjust this function only.
    """
    cart = get_cart(request)
    for item in cart:
        variant = item.get("variant")
        quantity = int(item.get("quantity", 1))

        if variant is None:
            variant_id = item.get("variant_id")
            if variant_id is not None:
                variant = ProductVariant.objects.get(pk=variant_id)

        if variant is None:
            continue

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


def is_email_confirmed_for_checkout(request, email: str) -> bool:
    """
    Hook to decide whether the given email is confirmed and allowed
    to place an order.

    For now:
      - If the user is authenticated and their account email matches
        the entered email (case-insensitive), treat as confirmed.
      - Guest emails (anonymous user) are NOT treated as confirmed yet.

    You can later replace this with your real email-verification logic,
    e.g. integrating with allauth or a custom confirmation table.
    """
    normalized_email = email.strip().casefold()
    user = getattr(request, "user", None)

    if user and user.is_authenticated and user.email:
        return user.email.strip().casefold() == normalized_email

    # Guests are not yet confirmed – implement your real flow here.
    return False


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@require_GET
def checkout_review(request):
    """
    Simple review page showing cart contents and totals.
    If HTMX: render a modal partial.
    If normal request: render a full page extending base.html.
    """
    items = list(_iter_cart_items_for_order(request))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    subtotal = sum(
        (line["unit_price"] * line["quantity"] for line in items),
        Decimal("0.00"),
    )

    tax = Decimal("0.00")  # placeholder
    shipping = Decimal("0.00")  # placeholder
    total = subtotal + tax + shipping

    context = {
        "items":         items,
        "subtotal":      subtotal,
        "tax":           tax,
        "shipping":      shipping,
        "total":         total,
        "email_initial": (
            request.user.email if getattr(request, "user", None) and request.user.is_authenticated else ""
        ),
    }

    if http.is_htmx(request):
        template = "hr_shop/_checkout_review.html"  # modal content
    else:
        template = "hr_shop/checkout_review.html"  # extends base.html

    return render(request, template, context)


@require_POST
def checkout_create_order(request):
    """
    POST endpoint to create an Order + OrderItems from the current cart,
    then hand it off to the payment provider (mock Stripe for now).

    Email MUST be confirmed before the order can be placed.
    Guest checkouts will work once you wire this to a real confirmation flow.
    """
    items = list(_iter_cart_items_for_order(request))

    if not items:
        messages.error(request, "Your cart is empty.")
        return redirect("hr_shop:view_cart")

    email = (request.POST.get("email") or "").strip()
    if not email:
        messages.error(request, "Please provide an email address.")
        return redirect("hr_shop:checkout_review")

    # Enforce email confirmation before placing the order
    if not is_email_confirmed_for_checkout(request, email):
        messages.error(
            request,
            "Please confirm your email address before placing an order."
        )
        # Later you might redirect to a 'start email verification' view here.
        return redirect("hr_shop:checkout_review")

    form = CheckoutDetailsForm()
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    customer = _get_or_create_customer(email, user, form)

    # --- Create Order shell ---
    order_kwargs: Dict[str, Any] = {
        "customer":         customer,
        "email":            email,
        "shipping_address": None,  # plug in real address selection later
        "total":            Decimal("0.00"),
        "status":           "pending",
    }
    # If your Order model also has a user FK, you can include it here:
    # if user is not None:
    #     order_kwargs["user"] = user

    order = Order(**order_kwargs)
    # Assumes stripe_checkout_session_id is nullable/blank
    order.stripe_checkout_session_id = None
    order.save()

    # --- Create OrderItems and compute totals ---
    subtotal = Decimal("0.00")
    for line in items:
        variant = line["variant"]
        quantity = line["quantity"]
        unit_price = line["unit_price"]
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
    total = subtotal + tax + shipping

    order.total = total
    order.save(update_fields=["total", "updated_at"])

    # --- Hand off to payment provider (mock Stripe for now) ---
    provider = get_payment_provider()
    session = provider.create_checkout_session(order)

    redirect_url = session.get("url") or reverse(
        "hr_shop:order_thank_you",
        args=[order.id],
    )

    if order.status == "paid":
        _clear_cart(request)
        messages.success(request, "Payment succeeded! Thank you for your order.")
    else:
        messages.info(request, "Redirecting to payment provider...")

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
        template = "hr_shop/_order_thank_you.html"
    else:
        template = "hr_shop/order_thank_you.html"

    return render(request, template, context)
