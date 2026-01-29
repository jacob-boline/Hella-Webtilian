# hr_access/views/account.py

from __future__ import annotations

import logging

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_POST

from hr_access.forms import AccountCreationForm, AccountEmailChangeForm
from hr_access.models import User
from hr_access.tokens.account_signup import generate_account_signup_token, verify_account_signup_token
from hr_access.tokens.email_change import generate_email_change_token, verify_email_change_token
from hr_access.services.post_purchase import (
    build_post_purchase_form,
    create_post_purchase_account,
    get_post_purchase_unclaimed_orders,
)
from hr_common.utils.email import normalize_email
from hr_common.utils.http.htmx import hx_trigger, merge_hx_trigger_after_settle
from hr_common.utils.http.messages import show_message
from hr_common.utils.htmx_responses import hx_login_required
from hr_common.utils.unified_logging import log_event
from hr_core.utils.urls import build_external_absolute_url
from hr_email.service import EmailProviderError, send_app_email
from hr_shop.exceptions import EmailSendError, RateLimitExceeded
from hr_shop.models import Order
from hr_shop.services.customers import attach_customer_to_user

logger = logging.getLogger(__name__)

SIGNUP_RATE_LIMIT_MAX_EMAILS = 3
SIGNUP_RATE_LIMIT_WINDOW_SECONDS = 3600
SIGNUP_SENT_AT_KEY = "account_signup_confirm_sent_at:{email}"
SIGNUP_COUNT_KEY = "account_signup_email_count:{email}"

EMAIL_CHANGE_RATE_LIMIT_MAX_EMAILS = 3
EMAIL_CHANGE_RATE_LIMIT_WINDOW_SECONDS = 3600
EMAIL_CHANGE_COUNT_KEY = "account_email_change_count:{user_id}"
EMAIL_CHANGE_SENT_AT_KEY = "account_email_change_sent_at:{user_id}"


def _increment_signup_email_count(email: str) -> int:
    key = SIGNUP_COUNT_KEY.format(email=email)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=SIGNUP_RATE_LIMIT_WINDOW_SECONDS)
    return count


def _can_send_signup_email(email: str) -> bool:
    key = SIGNUP_COUNT_KEY.format(email=email)
    return cache.get(key, 0) < SIGNUP_RATE_LIMIT_MAX_EMAILS


def _get_last_signup_confirmation_sent_at(email: str):
    return cache.get(SIGNUP_SENT_AT_KEY.format(email=email))


def send_account_verify_email(request, user: User) -> str:
    """
    Send a confirmation email for new account signups.
    Mirrors the checkout confirmation flow (rate limiting + cache tracking)
    """
    if not user.email:
        raise ValueError("User email is required for signup verification.")  # TODO Review

    if not _can_send_signup_email(user.email):
        raise RateLimitExceeded("Too many confirmation emails sent. Please check your inbox or try again.")  # TODO Review

    token = generate_account_signup_token(user_id=user.id, email=user.email)

    confirm_url = build_external_absolute_url(request, reverse("hr_access:account_signup_confirm"), query={"t": token})
    subject = "Confirm your Hella Reptilian! account"
    html_body = render_to_string("hr_access/registration/signup_confirmation_email.html", {"confirm_url": confirm_url, "email": user.email, "year": timezone.now().year})
    text_body = (
        f"Please confirm your email to activate your account.\n\n"
        f"Confirm here: {confirm_url}\n"
        "This link expires in 1 hour.\n\n"
        "If you didn't sign up, you can ignore this email.\n\n"
        "---\nHella Reptilian!"
    )

    try:
        send_app_email(to_emails=[user.email], subject=subject, text_body=text_body, html_body=html_body, custom_id=f"account_signup_confirm_{user.id}")
    except EmailProviderError as exc:
        log_event(logger, logging.ERROR, "access.signup_confirmation.send_failed", email=user.email, error=str(exc))
        raise EmailSendError("Could not send confirmation email. Please try again.") from exc  # TODO Review

    _increment_signup_email_count(user.email)
    cache.set(SIGNUP_SENT_AT_KEY.format(email=user.email), timezone.now(), timeout=SIGNUP_RATE_LIMIT_WINDOW_SECONDS)
    log_event(logger, logging.INFO, "access.signup_confirmation.sent", email=user.email, user_id=user.id)
    return confirm_url


def _increment_email_change_email_count(user_id: int) -> int:
    key = EMAIL_CHANGE_COUNT_KEY.format(user_id=user_id)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=EMAIL_CHANGE_RATE_LIMIT_WINDOW_SECONDS)
    return count


def _can_send_email_change(user_id: int) -> bool:
    key = EMAIL_CHANGE_COUNT_KEY.format(user_id=user_id)
    return cache.get(key, 0) < EMAIL_CHANGE_RATE_LIMIT_MAX_EMAILS


def _get_last_email_change_sent_at(user_id: int):
    return cache.get(EMAIL_CHANGE_SENT_AT_KEY.format(user_id=user_id))


def send_email_change_verification(request, user: User, new_email: str) -> str:
    if not _can_send_email_change(user.id):
        raise RateLimitExceeded("Too many confirmation emails sent. Please try again later.")  # TODO Review

    token = generate_email_change_token(user_id=user.id, new_email=new_email)

    confirm_url = build_external_absolute_url(request, reverse("hr_access:account_change_email_confirm"), query={"u": user.id, "t": token})

    subject = "Confirm your new email"
    html_body = render_to_string("hr_access/account/email_change_email.html", {"confirm_url": confirm_url, "email": new_email, "username": user.username})
    text_body = render_to_string("hr_access/account/email_change_email.txt", {"confirm_url": confirm_url, "email": new_email, "username": user.username})

    try:
        send_app_email(
            to_emails=[new_email],
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            custom_id=f"account_email_change_{user.id}",
        )
    except EmailProviderError as exc:
        log_event(logger, logging.ERROR, "access.email_change_confirmation.send_failed", email=new_email, user_id=user.id, error=str(exc))
        raise EmailSendError("Could not send confirmation email. Please try again.") from exc  # TODO Review

    _increment_email_change_email_count(user.id)
    cache.set(EMAIL_CHANGE_SENT_AT_KEY.format(user_id=user.id), timezone.now(), timeout=EMAIL_CHANGE_RATE_LIMIT_WINDOW_SECONDS)
    log_event(logger, logging.INFO, "access.email_change_confirmation.sent", email=new_email, user_id=user.id)
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
            log_event(logger, logging.INFO, "access.account_signup.form_invalid")
            return render(request, "hr_access/registration/_signup.html", {"form": form})

        user = form.create_user(role=User.Role.USER, is_active=False)
        log_event(logger, logging.INFO, "access.account_signup.user_created.inactive_until_verified", user_id=user.id)

        try:
            log_event(logger, logging.INFO, "access.account_signup.verify_email_send_attempt", user_id=user.id, email=user.email)
            send_account_verify_email(request, user)
            log_event(logger, logging.INFO, "access.account_signup.verify_email_sent", user_id=user.id)
            context = {
                "email": user.email,
                "sent_at": _get_last_signup_confirmation_sent_at(user.email),
                "rate_limited": False,
                "error": False,
                "message": "We've sent a confirmation link to your email. Please check your inbox.",
            }
        except RateLimitExceeded:
            log_event(logger, logging.WARNING, "access.account_signup.rate_limit_exceeded", user_id=user.id, email=user.email, exc_info=True)
            context = {
                "email": user.email,
                "sent_at": _get_last_signup_confirmation_sent_at(user.email),
                "rate_limited": True,
                "error": False,
                "message": "Too many confirmation emails sent. Please check your inbox or try again later.",
            }
        except EmailSendError:
            log_event(logger, logging.WARNING, "access.account_signup.email_send_error", user_id=user.id, email=user.email, exc_info=True)
            context = {
                "email": user.email,
                "sent_at": _get_last_signup_confirmation_sent_at(user.email),
                "rate_limited": False,
                "error": True,
                "message": "Could not send confirmation email. Please try again.",
            }
        resp = render(request, "hr_access/registration/_signup_check_email.html", context)
        message = context.get("message") or "Check your email to confirm your account."
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(message)})

    # GET
    return render(request, "hr_access/registration/_signup.html", {"form": AccountCreationForm()})


@require_GET
def account_signup_confirm(request):
    raw_token = (request.GET.get("t") or "").strip()
    token = verify_account_signup_token(raw_token)
    if not token:
        log_event(logger, logging.WARNING, "access.signup_confirmation.invalid_token")
        return HttpResponse("Invalid or expired confirmation link.", status=400)  # TODO HX-Trigger

    user = get_object_or_404(User, pk=int(token.user_id))
    log_event(logger, logging.INFO, "access.signup_confirmation.started", user_id=user.id)

    # bind token to the intended user + email
    if int(token.user_id) != int(user.id):
        log_event(logger, logging.WARNING, "access.signup_confirmation.user_mismatch", user_id=user.id)
        return HttpResponse("Invalid confirmation link.", status=400)  # TODO HX-Trigger

    if normalize_email(token.email) != user.email:
        log_event(logger, logging.WARNING, "access.signup_confirmation.email_mismatch", user_id=user.id, token_email=token.email, user_email=user.email)
        return HttpResponse("Invalid confirmation link.", status=400)  # TODO HX-Trigger

    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
        log_event(logger, logging.INFO, "access.signup_confirmation.activated", user_id=user.id)

    login(request, user)

    try:
        attach_customer_to_user(user)
    except Exception:
        log_event(logger, logging.ERROR, "access.signup_confirmation.attach_customer_failed", user_id=user.id, exc_info=True)

    log_event(logger, logging.INFO, "access.signup_confirmation.confirmed", user_id=user.id)

    return hx_trigger({"accessChanged": None, "showMessage": show_message("Email confirmed. You are now signed in.")}, status=204)


@hx_login_required
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
            log_event(logger, logging.INFO, "access.account_password.changed")
            return hx_trigger(
                {"showMessage": show_message("Your password has been changed.", duration=5000), "closeModal": None},
                status=204
            )

        log_event(logger, logging.INFO, "access.account_password.form_invalid")
        return render(request, template, {"form": form})

    form = PasswordChangeForm(user=request.user)
    return render(request, template, {"form": form})


@hx_login_required
@require_GET
def account_settings(request):
    email = request.user.email
    order_count = Order.objects.filter(user=request.user).count()
    unclaimed_count = Order.objects.filter(user__isnull=True, email__iexact=email).count() if email else 0
    log_event(logger, logging.INFO, "access.account_settings.rendered", order_count=order_count, unclaimed_count=unclaimed_count)

    return render(request, "hr_access/account/_account_settings_modal.html", {
            "last_login": request.user.last_login,
            "password_changed_at": getattr(request.user, "password_changed_at", None),
            "order_count": order_count,
            "unclaimed_count": unclaimed_count
        }
    )


@hx_login_required
def account_change_email(request):
    template = "hr_access/account/_account_email_change_form.html"

    if request.method == "POST":
        form = AccountEmailChangeForm(request.user, request.POST)
        if form.is_valid():
            new_email = normalize_email(form.cleaned_data["email"])
            try:
                send_email_change_verification(request, request.user, new_email)
                ctx = {
                    "email": new_email,
                    "sent_at": _get_last_email_change_sent_at(request.user.id),
                    "rate_limited": False,
                    "error": False
                }
                log_event(logger, logging.INFO, "access.email_change.requested", email=new_email)
            except RateLimitExceeded:
                ctx = {
                    "email": new_email,
                    "sent_at": _get_last_email_change_sent_at(request.user.id),
                    "rate_limited": True,
                    "error": False
                }
                log_event(logger, logging.WARNING, "access.email_change.rate_limited", email=new_email)
            except EmailSendError:
                ctx = {
                    "email": new_email,
                    "sent_at": _get_last_email_change_sent_at(request.user.id),
                    "rate_limited": False,
                    "error": True
                }
                log_event(logger, logging.ERROR, "access.email_change.send_failed", email=new_email)
            return render(request, "hr_access/account/_account_email_change_check_email.html", ctx)

        log_event(logger, logging.INFO, "access.email_change.form_invalid")
        return render(request, template, {"form": form})

    form = AccountEmailChangeForm(request.user)
    return render(request, template, {"form": form})


@require_GET
def account_change_email_confirm(request):
    token = (request.GET.get("t") or "").strip()
    user_id = request.GET.get("u") or ""
    user = get_object_or_404(User, pk=user_id)

    data = verify_email_change_token(token)
    if not data:
        log_event(logger, logging.WARNING, "access.email_change.invalid_token", token_present=bool(token), user_id=user.id)
        return HttpResponse("Invalid or expired confirmation link.", status=400)  # TODO HX-Trigger

    if not user.is_active:
        log_event(logger, logging.WARNING, "access.email_change.user_inactive", user_id=user.id)
        return HttpResponse("Account is inactive.", status=400)  # TODO HX-Trigger

    if int(data["user_id"]) != int(user.id):
        log_event(logger, logging.WARNING, "access.email_change.user_mismatch", user_id=user.id, token_user_id=data["user_id"])
        return HttpResponse("Invalid confirmation link.", status=400)  # TODO HX-Trigger

    new_email = normalize_email(data["email"])

    if User.objects.filter(email__iexact=new_email).exclude(pk=user.id).exists():
        log_event(logger, logging.WARNING, "access.email_change.email_in_use", email=new_email, user_id=user.id)
        return HttpResponse("This email is already in use.", status=400)  # TODO use HX-Trigger

    if user.email != new_email:
        user.email = new_email
        user.save(update_fields=["email", "updated_at"])
        log_event(logger, logging.INFO, "access.email_change.updated", email=new_email, user_id=user.id)

    modal_url = f"{reverse('hr_access:account_email_change_success')}?{urlencode({'email': new_email})}"
    params = urlencode({"modal": "email_change", "handoff": "email_change", "modal_url": modal_url})
    return redirect(f"{reverse('index')}?{params}")


@require_GET
def account_email_change_success(request):
    email = request.GET.get("email")
    resp = render(request, "hr_access/account/_account_email_change_success.html", {"email": email})
    return merge_hx_trigger_after_settle(resp, {"accessChanged": None, "showMessage": show_message("Email updated.")})


@hx_login_required
@require_GET
def account_logout_all_confirm(request):
    return render(request, "hr_access/account/_logout_all_confirm.html")


@hx_login_required
@require_POST
def account_logout_all_sessions(request):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    deleted = 0
    for session in sessions:
        data = session.get_decoded()
        if str(data.get("_auth_user_id")) == str(request.user.pk):
            session.delete()
            deleted += 1

    logout(request)

    log_event(logger, logging.INFO, "access.account_logout_all.completed", deleted_sessions=deleted)
    return hx_trigger({"accessChanged": None, "showMessage": show_message(f"Logged out of {deleted} session(s).")}, status=204)


@hx_login_required
@require_GET
def account_delete_confirm(request):
    return render(request, "hr_access/account/_delete_account_confirm.html")


@hx_login_required
@require_POST
def account_delete_account(request):
    user = request.user
    user.is_active = False
    user.deleted_at = timezone.now()
    user.save(update_fields=["is_active", "deleted_at"])

    logout(request)

    log_event(logger, logging.INFO, "access.account_deleted")
    return hx_trigger({"accessChanged": None, "showMessage": show_message("Account deleted.")}, status=204)


@require_GET
def account_get_post_purchase_create_account(request, order_id: int):
    """
    Follows hank-you modal for guest orders
    """
    if request.user.is_authenticated:
        log_event(logger, logging.INFO, "access.post_purchase.already_authenticated", order_id=order_id)
        return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")

    order = get_object_or_404(Order, pk=order_id)
    form = build_post_purchase_form(order)

    log_event(logger, logging.INFO, "access.post_purchase.signup_form_rendered", order_id=order_id)
    return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {"order": order, "form": form})


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
        log_event(logger, logging.INFO, "access.post_purchase.submit.already_authenticated", order_id=order_id)
        return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")

    order = get_object_or_404(Order, pk=order_id)
    form = build_post_purchase_form(order, request.POST)
    if not form.is_valid():
        log_event(logger, logging.INFO, "access.post_purchase.signup_form_invalid", order_id=order_id)
        return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {"order": order, "form": form})

    result = create_post_purchase_account(order, request.POST)
    if not result:
        log_event(logger, logging.INFO, "access.post_purchase.signup_form_invalid", order_id=order_id)
        return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {"order": order, "form": form})

    user, other_orders = result
    login(request, user)

    log_event(logger, logging.INFO, "access.post_purchase.account_created", order_id=order.id, other_orders_count=len(other_orders))
    return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {"order": order, "other_orders": other_orders})


@require_POST
def account_submit_post_purchase_claim_orders(request, order_id: int):
    """
    After post-purchase account creation:
    Presents user with any other orders linked to the email (prior guest orders) used to make their new account.
    User may claim/deny as desired.
    """
    if not request.user.is_authenticated:
        log_event(logger, logging.WARNING, "access.post_purchase.claim_orders.unauthenticated", order_id=order_id)
        return hx_trigger({"showMessage": show_message("Please sign in to claim orders.")}, status=401)

    order = get_object_or_404(Order, pk=order_id)
    email = order.email

    # Ownership gate: only link account_get_orders if the account email matches order email
    if request.user.email != email:
        log_event(logger, logging.WARNING, "access.post_purchase.claim_orders.email_mismatch", order_id=order_id, order_email=email)
        return hx_trigger({"showMessage": show_message("This order does not match your account email.")}, status=403)

    unclaimed_orders = get_post_purchase_unclaimed_orders(email, exclude_order_id=order.id)

    log_event(logger, logging.INFO, "access.post_purchase.claim_orders.rendered", order_id=order_id, unclaimed_count=len(unclaimed_orders))
    return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {"email": email, "unclaimed_orders": unclaimed_orders, "error": None})

    # return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
    #     "order": order,
    #     "other_orders": remaining,
    #     "claimed_count": claimed_count,
    # })
