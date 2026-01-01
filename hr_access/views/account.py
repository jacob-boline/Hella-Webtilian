# hr_access/views/account.py

from __future__ import annotations

import json
from logging import getLogger

from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from hr_access.forms import AccountCreationForm
from hr_access.models import User
from hr_core.utils.email import normalize_email
from hr_core.utils.tokens import verify_account_signup_token, generate_account_signup_token
from hr_shop.exceptions import RateLimitExceeded, EmailSendError
from hr_shop.models import Order
from hr_shop.services.customers import attach_customer_to_user
from hr_email.service import EmailProviderError, send_app_email

logger = getLogger()

SIGNUP_RATE_LIMIT_MAX_EMAILS = 3
SIGNUP_RATE_LIMIT_WINDOW_SECONDS = 3600
SIGNUP_SENT_AT_KEY = "account_signup_confirm_sent_at:{email}"
SIGNUP_COUNT_KEY = "account_signup_email_count:{email}"


def _increment_signup_email_count(email:str) -> int:
    normalized = normalize_email(email)
    key = SIGNUP_COUNT_KEY.format(email=normalized)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=SIGNUP_RATE_LIMIT_WINDOW_SECONDS)
    return count


def _can_send_signup_email(email: str) -> bool:
    normalized = normalize_email(email)
    key = SIGNUP_COUNT_KEY.format(email=normalized)
    return cache.get(key, 0) < SIGNUP_RATE_LIMIT_MAX_EMAILS


def _get_last_signup_confirmation_sent_at(email: str):
    return cache.get(SIGNUP_SENT_AT_KEY.format(email=normalize_email(email)))


def send_account_verify_email(request, user: User) -> str:
    """
    Send a confirmation email for new account signups.
    Mirrors the checkout confirmation flow (rate limiting + cache tracking)
    """
    if not user.email:
        raise ValueError("User email is required for signup verification.")

    if not _can_send_signup_email(user.email):
        raise RateLimitExceeded("Too many confirmation emails sent. Please check your inbox or try again.")

    token = generate_account_signup_token(user_id=user.id, email=user.email)
    confirm_url = request.build_absolute_uri(
        f"{reverse('hr_access:account_signup_confirm')}?u={user.id}&t={token}"
    )

    subject = "Confirm your Hella Reptilian! account"
    html_body = render_to_string(
        "hr_access/registration/signup_confirmation_email.html",
        {
            "confirm_url": confirm_url,
            "email": normalize_email(user.email),
            "year": timezone.now().year
        }
    )
    text_body = (
        f"Please confirm your email to activate your account.\n\n"
        f"Confirm here: {confirm_url}\n"
        "This link expires in 1 hour.\n\n"
        "If you didn't sign up, you can ignore this email.\n\n"
        "---\nHella Reptilian!"
    )

    try:
        send_app_email(
            to_emails=[user.email],
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            custom_id=f"account_signup_confirm_{user.id}"
        )
    except EmailProviderError as exc:
        logger.error('Failed to send signup confirmation to %s: %s', user.email, exc)
        raise EmailSendError("Could not send confirmation email. Please try again.") from exc

    _increment_signup_email_count(user.email)
    cache.set(
        SIGNUP_SENT_AT_KEY.format(email=normalize_email(user.email)),
        timezone.now(),
        timeout=SIGNUP_RATE_LIMIT_WINDOW_SECONDS
    )
    logger.info("Signup confirmation email sent to %s", user.email)
    return confirm_url


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

        try:
            send_account_verify_email(request, user)
            context = {
                'email': user.email,
                'sent_at': _get_last_signup_confirmation_sent_at(user.email),
                'rate_limited': False,
                'error': False,
                'message': "We've sent a confirmation link to your email. Please check your inbox."
            }
        except RateLimitExceeded:
            context = {
                'email':        user.email,
                'sent_at':      _get_last_signup_confirmation_sent_at(user.email),
                'rate_limited': True,
                'error':        False,
                'message':      "Too many confirmation emails sent. Please check your inbox or try again later.",
            }
        except EmailSendError:
            context = {
                'email':        user.email,
                'sent_at':      _get_last_signup_confirmation_sent_at(user.email),
                'rate_limited': False,
                'error':        True,
                'message':      "Could not send confirmation email. Please try again.",
            }
        response = render(request, 'hr_access/registration/_signup_check_email.html', context)
        response['HX-Trigger'] = json.dumps({
            'showMessage': context.get('message') or 'Check your email to confirm your account.'
        })
        return response

    # GET
    return render(request, "hr_access/registration/_signup.html", {"form": AccountCreationForm()})


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
