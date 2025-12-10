# hr_access/views.py

import json
from logging import getLogger

from django.contrib import messages
from django.contrib.admin.views.decorators import user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from hr_access.forms import StaffForm, SetPasswordForm, CustomUserCreationForm
from hr_access.emails import send_claim_email
from hr_core.utils import http
from hr_core.utils.email import normalize_email
from hr_shop.cart import get_cart
from hr_shop.models import Order
from hr_site.views import display_message_box_modal
from hr_shop.services.customers import attach_customer_to_user
from hr_access.models import User

# =====================================================================================================================

logger = getLogger()
signer = TimestampSigner()


# =====================================================================================================================
#  ACCOUNT
# =====================================================================================================================

def signup(request):
    """
    Public signup.
    - If an INACTIVE (shadow) user exists with that email → send claim link instead.
    - If an ACTIVE user exists → error.
    - Else create user, log in.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data.get("email"))
            User = get_user_model()

            # inactive = User.objects.filter(email=email, is_active=False).first()
            # if inactive:
            #     # Send claim link instead of creating a duplicate account.
            #     send_claim_email(request, inactive)
            #     messages.info(
            #         request,
            #         "We found a pending account for that email. We sent a link to finish setup."
            #     )
            #     return redirect("account:login")  # or wherever

            if User.objects.filter(email=email, is_active=True).exists():
                messages.error(request, "An account already exists for that email. Please sign in.")
                return redirect("account:login")

            user = form.save()  # creation form already normalizes email + sets password
            login(request, user)
            #  immediately attach any guest orders with matching email
            try:
                attach_customer_to_user(user)
            except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
                logger.warning(f'Failed to attach guest orders for user {user.pk}: {err}')
            messages.success(request, "Welcome! Your account is ready.")
            return redirect("account:orders")  # or LOGIN_REDIRECT_URL
    else:
        form = CustomUserCreationForm()

    return render(request, "hr_access/signup.html", {"form": form})


def user_login(request):
    """
    Handles both:
    - Full page login (/account/login) for non-HTMX requests
    - Sidebar HTMX login for hx-post requests targeting #sidebar-access
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if http.is_htmx(request):
                response = render(request, "hr_access/_sidebar_access.html")
                response.headers["HX-Trigger"] = json.dumps({
                    "accessChanged": None,
                    "showMessage": "Login successful",
                })
                return response

            # Non-HTMX: normal redirect
            return redirect("hr_site:index")

        # ---- Invalid credentials ----
        if http.is_htmx(request):
            response = render(
                request,
                "hr_access/_sidebar_access.html",
                {"authentication_form": form},
            )
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": "No match found for Username/Password",
            })
            return response

        # Non-HTMX invalid login → full-page with errors
        messages.error(request, "No match found for Username/Password")
        return render(
            request,
            "hr_access/login.html",
            {"authentication_form": form},
        )

    # ------------------ GET ------------------
    form = AuthenticationForm(request)

    if http.is_htmx(request):
        return render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})

    # Normal full-page login view
    return render(request, "hr_access/login.html", {"authentication_form": form})


def login_success(request):
    return render(request, 'hr_access/_login_success.html')


def user_logout(request):
    logout(request)
    headers_dict = {
        'accessChanged':   None,
        'bulletinChanged': None,
        'dialogChanged':   None,
        'showsChanged':    None,
        'showMessage':     'You have been logged out.'
    }
    return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})


def logout_redirect(request):
    headers_dict = {'accessChanged': None,
                    'bulletinChanged': None,
                    'dialogChanged': None,
                    'showsChanged': None,
                    'showMessage': 'You have been logged out.'}
    return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})


@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            #messages.success(request, 'Password updated.')

            if http.is_htmx(request):
                headers = {
                    'HX-Trigger': json.dumps({
                        'passwordChanged': {
                            'message': "Your password has been changed"
                        }
                    })
                }
                return HttpResponse(status=204, headers=headers)

            messages.success(request, "Your password has been changed.")
            return redirect('hr_access:login_success')
    else:
        form = PasswordChangeForm(user=request.user)

    if http.is_htmx(request):
        return render(request, "hr_access/_password_change_form.html", {"form": form})
    return render(request, "hr_access/password_change_form.html", {"form": form})


# ==================================================================================================================
#  ORDER CLAIM
# ==================================================================================================================


@login_required
def claim_modal(request):
    return render(request, "hr_access/_claim_modal.html")


@require_POST
@login_required
def claim_start(request):
    email = normalize_email(request.POST.get('email'))
    token = signer.sign(email)  # contains email
    # TODO: ideally use reverse("account:claim_verify") instead of hardcoding the URL
    link = reverse('account:claim_verify')
    # link = request.build_absolute_uri(f"/account/orders/claim/verify?token={token}")
    send_mail("Confirm your order claim", f"Click to link orders: {link}", "merch@hellareptilian.com", [email])
    return JsonResponse({"ok": True})


def claim_account(request, user_id: int, token: str):
    user = get_object_or_404(get_user_model(), pk=user_id, is_active=False)
    if not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired claim link.")
        return redirect("shop:product_list")

    if request.method == "POST":
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["password1"])
            user.is_active = True
            # optionally let them choose a new username on a later step
            user.save(update_fields=["password", "is_active"])
            login(request, user)
            try:
                attach_customer_to_user(user)
            except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
                logger.warning(f'Failed to attach guest orders for user {user.uk}: {err}')
            messages.success(request, "Your account is ready.")
            return redirect("account:orders")  # wherever
    else:
        form = SetPasswordForm()

    return render(request, "hr_access/claim_account.html", {"form": form, "shadow": user})


@login_required
def claim_verify(request):
    token = request.GET.get('token', '')
    try:
        email = signer.unsign(token, max_age=15 * 60)  # 15 minutes
    except (BadSignature, SignatureExpired):
        return render(request, "hr_access/_claim_result_modal.html", {"ok": False})
    # Link
    linked = (Order.objects
              .filter(user__isnull=True, email=normalize_email(email))
              .update(user=request.user))
    return render(request, "hr_access/_claim_result_modal.html", {"ok": True, "count": linked})


@require_http_methods(['GET', 'POST'])
def claim_resend(request):
    if request.method == 'POST':
        email = normalize_email(request.POST.get('email'))
        User = get_user_model()
        u = User.objects.filter(email=email, is_active=False).first()
        if u:
            send_claim_email(request, u)
        messages.info(request, "If a pending account exists for that email, we sent a link.")
        return redirect('account:login')
    return render(request, 'hr_access/resend_claim.html')


# ==================================================================================================================
#  ORDERS
# ==================================================================================================================

@login_required
def orders(request):
    email = normalize_email(getattr(request.user, 'email', ''))
    qs = (Order.objects.filter(user=request.user)
        | Order.objects.filter(email=email))\
        .order_by('-created_at').distinct()

    ctx = {"orders": qs[:20], "has_more": qs.count() > 20}

    if http.is_htmx(request):
        # Return ONLY the modal body (no base layout)
        return render(request, "hr_access/_orders_modal_body.html", ctx)

    # Normal browser visit → full page (includes base layout, modal shell, nav, etc.)
    return render(request, "hr_access/orders_page.html", ctx)


# ==================================================================================================================
#  COMPONENTS
# ==================================================================================================================

def access_panel(request):
    return render(request, 'hr_access/_sidebar_access.html')


def user_panel(request):
    # headers_dict = {'accessChanged': None}
    response = render(request, 'hr_access/_user_panel.html')
    # response.headers['HX-Trigger'] = json.dumps(headers_dict)
    return response


def sidebar_access(request):
    return render(request, 'hr_access/_sidebar_ul.html')


# ==================================================================================================================
#  ROLES
# ==================================================================================================================

class AdminLogin(LoginView):
    template_name = 'hr_access/loginview_form.html'


@user_passes_test(lambda u: u.is_superuser)
def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            user = form.save()
            headers_dict = {
                'dialogChanged': None,
                'showMessage':   f"Created staff user {user.username}"
            }
            return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})
    else:
        form = StaffForm()
    return render(request, 'hr_access/add_staff_form.html', {'add_staff_form': form})


@user_passes_test(lambda u: u.is_superuser)
def get_message_confirm_superuser_removal(request, user_id):
    """
    Show a confirmation message-box (HTMX partial) before demoting a user.
    Intended to be loaded into #message-box-modal via hx-get.
    """

    target = get_object_or_404(User, pk=user_id)

    removing_superuser = target.is_superuser
    removing_global_role = (target.role == User.Role.GLOBAL_ADMIN)

    confirm_url = reverse('hr_access:perform_superuser_removal', args=[target.pk])

    return display_message_box_modal(
        request,
        title='Confirm removal of elevated priveleges',
        message=(
            f"You are about to change privileges for {target.username} ({target.email}). "
            f"{'This will remove superuser status. ' if removing_superuser else ''}"
            f"{'This will remove Global Admin role.' if removing_global_role else ''}"
        ),
        level='warning',
        confirm_url=confirm_url,
        confirm_method='post',
        confirm_label='Yes, remove privileges',
        cancel_url=reverse('hr_access:cancel_superuser_removal', args=[target.pk]),
        cancel_label='Cancel',
    )


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def perform_superuser_removal(request, user_id):
    """
    Actually demote the user (remove superuser/global admin).
    Called when the user clicks YES in the message box.
    """
    target = get_object_or_404(User, pk=user_id)

    # Optional: guard against demoting the last superuser
    if target.is_superuser and not User.objects.exclude(pk=target.pk).filter(is_superuser=True).exists():
        return display_message_box_modal(
            request,
            title="Cannot remove last superuser",
            message="You must have at least one superuser account. Create another superuser first.",
            level="error",
            confirm_url="",  # Close button only
            confirm_label="OK",
        )

    # Demote according to your rules
    target.is_superuser = False
    if target.role == User.Role.GLOBAL_ADMIN:
        target.role = User.Role.SITE_ADMIN  # or USER, up to you
    target.save()

    # Show success message in the same modal box
    return display_message_box_modal(
        request,
        title="Privileges updated",
        message=f"{target.username}'s elevated privileges have been removed.",
        level="success",
        confirm_url="",  # just a Close button / clears message box
        confirm_label="Close",
    )




