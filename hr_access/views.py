# hr_access/views.py

import json
from logging import getLogger

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import user_passes_test
from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
    get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from hr_access.emails import send_claim_email
from hr_access.forms import StaffForm, SetPasswordForm, CustomUserCreationForm
from hr_access.models import User
from hr_core.mixins import HtmxTemplateMixin
from hr_core.utils import http
from hr_core.utils.email import normalize_email
from hr_shop.models import Order
from hr_shop.services.customers import attach_customer_to_user
from hr_site.views import display_message_box_modal

# =====================================================================================================================

logger = getLogger()
signer = TimestampSigner()


# =====================================================================================================================
#  ACCOUNT
# =====================================================================================================================
#
# def signup(request):
#     """
#     Public signup.
#     - If an INACTIVE (shadow) user exists with that email → send claim link instead.
#     - If an ACTIVE user exists → error.
#     - Else create user, log in.
#     """
#     if request.method == "POST":
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             email = normalize_email(form.cleaned_data.get("email"))
#             UserModel = get_user_model()
#
#             # inactive = User.objects.filter(email=email, is_active=False).first()
#             # if inactive:
#             #     # Send claim link instead of creating a duplicate account.
#             #     send_claim_email(request, inactive)
#             #     messages.info(
#             #         request,
#             #         "We found a pending account for that email. We sent a link to finish setup."
#             #     )
#             #     return redirect("account:login")  # or wherever
#
#             if UserModel.objects.filter(email=email, is_active=True).exists():
#                 messages.error(request, "An account already exists for that email. Please sign in.")
#                 return redirect("account:login")
#
#             user = form.save()  # creation form already normalizes email + sets password
#             login(request, user)
#             #  immediately attach any guest orders with matching email
#             try:
#                 attach_customer_to_user(user)
#             except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
#                 logger.warning(f'Failed to attach guest orders for user {user.pk}: {err}')
#             messages.success(request, "Welcome! Your account is ready.")
#             return redirect("account:orders")  # or LOGIN_REDIRECT_URL
#     else:
#         form = CustomUserCreationForm()
#
#     return render(request, "hr_access/signup.html", {"form": form})


def signup(request):
    """
    Public signup.
        - If a shadow user exists with that email -> send claim link.
        - If an active user exists -> error.
        - Else create user, log in.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            email = normalize_email(form.cleaned_data.get('email'))
            UserModel = get_user_model()

            if UserModel.objects.filter(email=email, is_active=True).exists():
                form.add_error('email', "An account already exists with this email.")
                return render(request, 'hr_access/registration/_signup.html', {'form': form})

            user = form.save()
            login(request, user)

            try:
                attach_customer_to_user(user)
            except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
                logger.warning(f'Failed to attach guest orders for user {user.pk}: {err}')

            response = render(request, 'hr_access/registration/_signup_success.html')
            response.headers['HX-Trigger'] = json.dumps({
                'accessChanged': None,
                'showMessage': 'Welcome! Your account is ready.'
            })
            return response

        else:
            return render(request, 'hr_access/registration/_signup.html', {'form': form})

    form = CustomUserCreationForm()
    template = (
        'hr_access/registration/_signup.html'
        if http.is_htmx(request)
        else 'hr_access/registration/signup.html'
    )
    return render(request, template, {'form': form})


# ==================================================================================================================
#  Login/Logout
# ==================================================================================================================

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

            response = render(request, "hr_access/_sidebar_access.html")
            response.headers["HX-Trigger"] = json.dumps({
                "accessChanged": None,
                "showMessage": "Login successful",
            })
            return response

        # ---- Invalid credentials ----
        response = render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})
        response.headers["HX-Trigger"] = json.dumps({
            "showMessage": "No match found for Username/Password",
        })
        return response

    # ------------------ GET ------------------
    form = AuthenticationForm(request)

    return render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})


# def login_success(request):
#     template = (
#         'hr_access/registration/_login_success.html'
#     )
#     return render(request, template)

def login_success(request):
    headers_dict = {
        'accessChanged': None,
        'showMessage': 'Sign In Successful'
    }
    return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})


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
    headers_dict = {
        'accessChanged':   None,
        'bulletinChanged': None,
        'dialogChanged':   None,
        'showsChanged':    None,
        'showMessage':     'You have been logged out.'}
    return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})


# ==================================================================================================================
#  Password Change
# ==================================================================================================================

@login_required
def password_change(request):

    # POST
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)

            if http.is_htmx(request):
                headers = {
                    'HX-Trigger': json.dumps({
                        'closeModalShowGLobalMessage': {
                            'message': "Your password has been changed"
                        }
                    })
                }
                return HttpResponse(status=204, headers=headers)

            messages.success(request, "Your password has been changed.")
            return redirect('hr_access:password_change_done')

    # GET
    else:
        form = PasswordChangeForm(user=request.user)
        template = 'hr_accees/registration/_password_change_form.html' \
            if http.is_htmx(request) \
            else 'hr_access/registration/password_change_form.html'

        return render(request, template, {'form': form})


# ==================================================================================================================
#  Password Reset
# ==================================================================================================================

class HRPasswordResetView(HtmxTemplateMixin, PasswordResetView):
    template_name = 'hr_access/registration/password_reset_form.html'
    htmx_template_name = 'hr_access/registration/_password_reset_form.html'

    email_template_name = 'hr_access/registration/password_reset_email.txt'
    html_email_template_name = 'hr_access/registration/password_reset_email.html'
    subject_template_name = 'hr_access/registration/password_reset_subject.txt'
    # success_url 'password_reset_done' or override


class HRPasswordResetDoneView(HtmxTemplateMixin, PasswordResetDoneView):
    template_name = 'hr_access/registration/password_reset_done.html'
    htmx_template_name = 'hr_access/registration/_password_reset_done.html'


class HRPasswordResetConfirmView(HtmxTemplateMixin, PasswordResetConfirmView):
    template_name = 'hr_access/registration/password_reset_confirm.html'
    htmx_template_name = 'hr_access/registration/_password_reset_confirm.html'
    # success_url =  'password_reset_complete' or override


class HRPasswordResetCompleteView(HtmxTemplateMixin, PasswordResetCompleteView):
    template_name = 'hr_access/registration/password_reset_complete.html'
    htmx_template_name = 'hr_access/registration/_password_reset_complete.html'


# ==================================================================================================================
#  Order Claim
# ==================================================================================================================

@login_required
def claim_modal(request):
    template = 'hr_access/claim/_claim_modal.html' if http.is_htmx(request) else 'hr_access/claim/claim_modal.html'
    return render(request, template)


@require_POST
@login_required
def claim_start(request):

    email = normalize_email(request.POST.get('email', ''))
    if not email:
        if http.is_htmx(request):
            return render(request, 'hr_access/claim/_claim_modal.html', {
                'error': 'Please enter an email address'
            })
        messages.error(request, "Please enter an email address.")
        return redirect('hr_access:claim_modal')

    token = signer.sign(email)
    link = request.build_absolute_uri(
        f"{reverse('hr_access:claim_verify')}?token={token}"
    )

    try:
        send_mail(
            "Confirm your order claim",
            f"Click to link orders: {link}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hellareptilian.com'),
            recipient_list=[email]
        )
    except Exception as e:
        logger.error(f"Failed to send claim email: {e}")
        if http.is_htmx(request):
            return render(request, 'hr_access/claim/_claim_email_sent.html', {
                'ok': False,
                'message': "Could not send email. Please try again."
            })
        messages.error(request, "Could not send email. Please try again.")
        return redirect('hr_access:claim_modal')

    if http.is_htmx(request):
        return render(request, 'hr_access/claim/_claim_email_sent.html', {
            'ok': True,
            'email': email
        })

    messages.success(request, f'Verification email sent to {email}')
    return redirect('hr_access:orders')


@login_required
def claim_verify(request):
    """
    Verify token from email and link orders to user.
    """
    token = request.GET.get('token', '')
    try:
        email = signer.unsign(token, max_age=15 * 60)  # 15 minutes
    except (BadSignature, SignatureExpired):
        if http.is_htmx(request):
            return render(request, 'hr_access/claim/_claim_result.html', {'ok': False})
        messages.error(request, "This link is invalid or has expired.")
        return redirect('hr_access:orders')

    # Link
    linked = (Order.objects
              .filter(user__isnull=True, email=normalize_email(email))
              .update(user=request.user))

    if http.is_htmx(request):
        return render(request, 'hr_access/claim/_claim_result.html', {'ok': True, 'count': linked})

    if linked > 0:
        messages.success(request, f"{linked} order(s) have been linked to your account.")
    else:
        messages.info(request, "No orders found to link with that email.")
    return redirect('hr_access:orders')


def claim_account(request, user_id: int, token: str):
    """Allow user to take over shadow user attached to guest orders related to email"""
    shadow_user = get_object_or_404(get_user_model(), pk=user_id, is_active=False)
    if not default_token_generator.check_token(shadow_user, token):
        messages.error(request, "Invalid or expired claim link.")
        return redirect("hr_shop:product_list")

    if request.method == "POST":
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            shadow_user.set_password(form.cleaned_data["password1"])
            shadow_user.is_active = True
            shadow_user.save(update_fields=["password", "is_active"])
            login(request, shadow_user)
            try:
                attach_customer_to_user(shadow_user)
            except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
                logger.warning(f'Failed to attach guest orders for user {shadow_user.pk}: {err}')

            if http.is_htmx(request):
                return HttpResponse(status=204, headers={
                    'HX-Trigger': json.dumps({
                        'accessChanged': None,
                        'modalSuccess': {'message': 'Your account is ready!'}
                    })
                })
            messages.success(request, "Your account is ready.")
            return redirect("hr_access:orders")
    # GET
    else:
        form = SetPasswordForm()

    template = 'hr_access/claim/_claim_account.html' \
        if http.is_htmx(request) \
        else 'hr_access/claim/claim_account.html'

    return render(request, template, {'form': form, 'shadow': shadow_user})


@require_http_methods(['GET', 'POST'])
def claim_resend(request):
    if request.method == 'POST':
        email = normalize_email(request.POST.get('email'))
        UserModel = get_user_model()
        shadow_user = UserModel.objects.filter(email=email, is_active=False).first()

        if shadow_user:
            send_claim_email(request, shadow_user)

        if http.is_htmx(request):
            return HttpResponse(status=204, headers={
                'HX-Trigger': json.dumps({
                    'modalSuccess': {
                        'message': "If a pending account exists, a link has been sent."
                    }
                })
            })
        messages.info(request, "If a pending account exists for that email, a link has been sent..")
        return redirect('hr_access:login')

    # GET
    template = 'hr_access/claim/_claim_resend.html' if http.is_htmx(request) else 'hr_access/claim/claim_resend.html'
    return render(request, template)


# ==================================================================================================================
#  ORDERS
# ==================================================================================================================

@login_required
def orders(request):
    email = normalize_email(getattr(request.user, 'email', ''))
    qs = (Order.objects.filter(user=request.user) | Order.objects.filter(email=email)).order_by('-created_at').distinct()
    ctx = {"orders": qs[:20], "has_more": qs.count() > 20}

    template = 'hr_access/_orders_modal_body.html' if http.is_htmx(request) else 'hr_access/orders_page.html'

    return render(request, template, ctx)


# ==================================================================================================================
#  COMPONENTS
# ==================================================================================================================

def determine_sidebar_access_panel(request):
    return render(request, 'hr_access/_sidebar_access.html')


def get_user_sidebar_panel(request):
    response = render(request, 'hr_access/_user_panel.html')
    return response


# ==================================================================================================================
#  ROLES
# ==================================================================================================================

class AdminLogin(LoginView):
    template_name = 'hr_access/_unlinked/loginview_form.html'


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

    # Guard against demoting the last superuser
    if target.is_superuser and not User.objects.exclude(pk=target.pk).filter(is_superuser=True).exists():
        return display_message_box_modal(
            request,
            title="Cannot remove last superuser",
            message="You must have at least one superuser account. Create another superuser first.",
            level="error",
            confirm_url="",  # Close button only
            confirm_label="OK",
        )

    # Demote
    target.is_superuser = False
    if target.role == User.Role.GLOBAL_ADMIN:
        target.role = User.Role.SITE_ADMIN
    target.save()

    # Show success message in the same modal box
    return display_message_box_modal(
        request,
        title="Privileges updated",
        message=f"{target.username}'s elevated privileges have been removed.",
        level="success",
        confirm_url="",  # just a Close button / clears message box
        confirm_label="Close"
    )


@user_passes_test(lambda u: u.is_superuser)
def cancel_superuser_removal(request, user_id):
    """
    Cancel the superuser removal - just close the message box.
    """
    return HttpResponse(status=204, headers={
        'HX-Trigger': json.dumps({'messageBoxClosed': f'Canceled superuser removal for ID {user_id}'})
    })
