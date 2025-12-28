# hr_access/views/account.py

from __future__ import annotations

import json
from logging import getLogger

from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from hr_access.forms import AccountCreationForm
from hr_access.models import User
from hr_core.utils.email import normalize_email
from hr_shop.models import Order
from hr_shop.services.customers import attach_customer_to_user
from utils.tokens import verify_checkout_email_token

logger = getLogger()


def account_signup(request):
    """
    Public account_signup (modal).
    GET: render account_signup form
    POST: create account, login, attach customer, render success partial
    """
    if request.method == "POST":
        form = AccountCreationForm(request.POST)
        if not form.is_valid():
            return render(request, "hr_access/registration/_signup.html", {"form": form})

        user = form.create_user(role=User.Role.USER, is_active=False)

        send_account_verify_email(request, user)

        response = render(request, 'hr_access/registration/_signup_check_email.html', {'email': user.email})
        response['HX-Trigger'] = json.dumps({
            'showMessage': 'Check your email to confirm your account.',
        })
        return response

        #
        # login(request, user)
        #
        # try:
        #     attach_customer_to_user(user)
        # except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
        #     logger.warning(f"Failed to attach guest account_get_orders for user {user.pk}: {err}")
        #
        # response = render(request, "hr_access/registration/_signup_success.html")
        # response.headers["HX-Trigger"] = json.dumps({
        #     "accessChanged": None,
        #     "showMessage": "Welcome! Your account is ready.",
        # })
        # return response

    return render(request, "hr_access/registration/_signup.html", {"form": AccountCreationForm()})

import json

from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from hr_access.models import User
from hr_shop.services.customers import attach_customer_to_user
from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import verify_account_signup_token


@require_GET
def account_signup_confirm(request):
    token = (request.GET.get("t") or "").strip()
    user_id = request.GET.get("u") or ""

    user = get_object_or_404(User, pk=user_id)

    data = verify_account_signup_token(token)
    if not data:
        return HttpResponse("Invalid or expired confirmation link.", status=400)

    # bind token to the intended user + email
    if int(data["user_id"]) != int(user.id):
        return HttpResponse("Invalid confirmation link.", status=400)

    if normalize_email(data["email"]) != normalize_email(user.email):
        return HttpResponse("Invalid confirmation link.", status=400)

    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])

    login(request, user)

    try:
        attach_customer_to_user(user)
    except Exception:
        pass

    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps({
                "accessChanged": None,
                "showMessage": "Email confirmed. You are now signed in.",
            })
        },
    )



@login_required
def account_change_password(request):
    """
    Password change (modal).
    GET: show form
    POST: validate + save + keep session
    """
    template = "hr_access/registration/_password_change_form.html"

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps({
                        "accessChanged": None,
                        "showMessage": "Your password has been changed.",
                    })
                },
            )

        return render(request, template, {"form": form})

    form = PasswordChangeForm(user=request.user)
    return render(request, template, {"form": form})


@require_GET
def account_get_post_purchase_create_account(request, order_id: int):
    """
    From thank-you modal (guest order):
    - Show the account creation form with email locked to the order email.
    """
    if request.user.is_authenticated:
        return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")

    order = get_object_or_404(Order, pk=order_id)
    form = AccountCreationForm(locked_email=(order.email or ""))

    return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {
        "order": order,
        "form": form,
    })


@require_POST
def account_submit_post_purchase_create_account(request, order_id: int):
    """
    Submit the post-purchase account creation form:
    - Create user (email locked to order email)
    - Link current order + customer to user
    - Login user
    - Return success fragment with list of other unclaimed account_get_orders for optional linking
    """
    if request.user.is_authenticated:
        return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")

    order = get_object_or_404(Order, pk=order_id)
    locked_email = normalize_email(order.email or "")

    # Hard-lock email (prevents tampering even if email is in POST)
    post = request.POST.copy()
    post["email"] = locked_email

    form = AccountCreationForm(post, locked_email=locked_email)
    if not form.is_valid():
        return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {
            "order": order,
            "form": form,
        })

    with transaction.atomic():
        user = form.create_user(role=User.Role.USER)

        cust = getattr(order, "customer", None)
        if cust and cust.user_id is None:
            cust.user = user
            cust.save(update_fields=["user", "updated_at"])

        if getattr(order, "user_id", None) is None:
            order.user = user
            order.save(update_fields=["user", "updated_at"])

    login(request, user)

    other_orders = (
        Order.objects
        .filter(email__iexact=locked_email, user__isnull=True)
        .exclude(pk=order.id)
        .order_by("-created_at")[:25]
    )

    return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
        "order": order,
        "other_orders": other_orders,
    })


@require_POST
def account_submit_post_purchase_claim_orders(request, order_id: int):
    """
    After post-purchase account creation:
    user selects which other guest account_get_orders (same email) to link to their account.
    """
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    order = get_object_or_404(Order, pk=order_id)
    email = normalize_email(order.email or "")

    # Ownership gate: only link account_get_orders if the account email matches order email
    if normalize_email(getattr(request.user, "email", "") or "") != email:
        return HttpResponse(status=403)

    raw_ids = request.POST.getlist("order_ids")
    order_ids = [int(x) for x in raw_ids if str(x).isdigit()]

    with transaction.atomic():
        qs = (
            Order.objects
            .select_for_update()
            .filter(id__in=order_ids, user__isnull=True, email__iexact=email)
        )
        claimed_count = qs.update(user=request.user)

    remaining = (
        Order.objects
        .filter(email__iexact=email, user__isnull=True)
        .exclude(pk=order.id)
        .order_by("-created_at")[:25]
    )

    return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
        "order": order,
        "other_orders": remaining,
        "claimed_count": claimed_count,
    })
