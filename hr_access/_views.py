# # hr_access/views.py
#
# from __future__ import annotations
#
# import json
# from logging import getLogger
#
# from django.contrib.admin.views.decorators import user_passes_test
# from django.contrib.auth import login, logout, update_session_auth_hash
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import PasswordChangeForm
# from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
# from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
# from django.db import IntegrityError, transaction
# from django.db.models import Prefetch
# from django.http import HttpResponse
# from django.shortcuts import get_object_or_404, render
# from django.urls import reverse
# from django.views.decorators.http import require_GET, require_POST
#
# from hr_access.forms import AccountAuthenticationForm, AccountCreationForm
# from hr_access.models import User
# from hr_core.utils.email import normalize_email
# from hr_shop.models import Order, OrderItem
# from hr_shop.services.customers import attach_customer_to_user
# from hr_site.views import display_message_box_modal
#
# logger = getLogger()
#
#
# # =====================================================================================================================
# #  SIGNUP (public)
# # =====================================================================================================================
#
# # def account_signup(request):
# #     if request.method == "POST":
# #         form = AccountCreationForm(request.POST)
# #         if not form.is_valid():
# #             return render(request, "hr_access/registration/_signup.html", {"form": form})
# #
# #         user = form.create_user(role=User.Role.USER)
# #         login(request, user)
# #
# #         try:
# #             attach_customer_to_user(user)
# #         except (ObjectDoesNotExist, MultipleObjectsReturned, ValidationError, IntegrityError) as err:
# #             logger.warning(f"Failed to attach guest account_get_orders for user {user.pk}: {err}")
# #
# #         response = render(request, "hr_access/registration/_signup_success.html")
# #         response.headers["HX-Trigger"] = json.dumps({
# #             "accessChanged": None,
# #             "showMessage": "Welcome! Your account is ready.",
# #         })
# #         return response
# #
# #     return render(request, "hr_access/registration/_signup.html", {"form": AccountCreationForm()})
#
#
# # =====================================================================================================================
# #  Login/Logout (sidebar)
# # =====================================================================================================================
#
# @require_POST
# def auth_login(request):
#     form = AccountAuthenticationForm(request, data=request.POST)
#     if form.is_valid():
#         login(request, form.get_user())
#         return HttpResponse(status=204, headers={
#             "HX-Trigger": json.dumps({
#                 "accessChanged": None,
#                 "showMessage": "Signed in.",
#             })
#         })
#
#     # invalid: return the sidebar access partial with errors
#     return render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})
#
#
# @require_POST
# def auth_logout(request):
#     logout(request)
#     return HttpResponse(status=204, headers={
#         "HX-Trigger": json.dumps({
#             "accessChanged": None,
#             "bulletinChanged": None,
#             "dialogChanged": None,
#             "showsChanged": None,
#             "showMessage": "You have been logged out.",
#         })
#     })
#
#
# # =====================================================================================================================
# #  Sidebar components
# # =====================================================================================================================
#
# def account_get_sidebar_panel(request):
#     return render(request, "hr_access/_sidebar_access.html", {
#         "authentication_form": AccountAuthenticationForm(request),
#     })
#
#
# @require_GET
# def account_get_user_panel(request):
#     return render(request, "hr_access/_user_panel.html")
#
#
# # =====================================================================================================================
# #  Password change (modal)
# # =====================================================================================================================
#
# # @login_required
# # def account_change_password(request):
# #     template = "hr_access/registration/_password_change_form.html"
# #
# #     if request.method == "POST":
# #         form = PasswordChangeForm(user=request.user, data=request.POST)
# #         if form.is_valid():
# #             user = form.save()
# #             update_session_auth_hash(request, user)
# #
# #             return HttpResponse(status=204, headers={
# #                 "HX-Trigger": json.dumps({
# #                     "accessChanged": None,
# #                     "showMessage": "Your password has been changed.",
# #                 })
# #             })
# #
# #         # invalid POST -> re-render modal with errors
# #         return render(request, template, {"form": form})
# #
# #     # GET
# #     form = PasswordChangeForm(user=request.user)
# #     return render(request, template, {"form": form})
# #
# #
# # # =====================================================================================================================
# # #  Password reset (CBVs)
# # # =====================================================================================================================
# #
# # # class AccountPasswordResetView(PasswordResetView):
# # #     template_name = "hr_access/registration/_password_reset_form.html"
# # #     email_template_name = "hr_access/registration/password_reset_email.txt"
# # #     html_email_template_name = "hr_access/registration/password_reset_email.html"
# # #     subject_template_name = "hr_access/registration/password_reset_subject.txt"
# # #
# # #
# # # class AccountPasswordResetDoneView(PasswordResetDoneView):
# # #     template_name = "hr_access/registration/_password_reset_done.html"
# # #
# # #
# # # class AccountPasswordResetConfirmView(PasswordResetConfirmView):
# # #     template_name = "hr_access/registration/password_reset_confirm.html"
# # #     # if you want HTMX: route to htmx_template_name yourself via request.headers.get("HX-Request")
# # #     htmx_template_name = "hr_access/registration/_password_reset_confirm.html"
# # #
# # #
# # # class AccountPasswordResetCompleteView(PasswordResetCompleteView):
# # #     template_name = "hr_access/registration/password_reset_complete.html"
# # #     htmx_template_name = "hr_access/registration/_password_reset_complete.html"
# #
# #
# # # =====================================================================================================================
# # #  Orders (account modal)
# # # =====================================================================================================================
# #
# # # @login_required
# # # def account_get_orders(request):
# # #     email = normalize_email(getattr(request.user, "email", "") or "")
# # #
# # #     base_qs = (
# # #         Order.objects
# # #         .filter(user=request.user)
# # #         .select_related("shipping_address", "customer")
# # #         .prefetch_related(
# # #             Prefetch(
# # #                 "items",
# # #                 queryset=OrderItem.objects.select_related("variant", "variant__product"),
# # #             )
# # #         )
# # #         .order_by("-created_at")
# # #     )
# # #
# # #     order_list = list(base_qs[:21])
# # #
# # #     ctx = {
# # #         "account_get_orders": order_list[:20],
# # #         "has_more": len(order_list) > 20,
# # #         "unclaimed_count": (
# # #             Order.objects.filter(user__isnull=True, email__iexact=email).count()
# # #             if email else 0
# # #         ),
# # #     }
# # #
# # #     return render(request, "hr_access/orders/_orders_modal_body.html", ctx)
# #
# #
# # # @login_required
# # # def account_get_order_receipt(request, order_id: int):
# # #     order = get_object_or_404(
# # #         Order.objects.select_related("customer", "shipping_address"),
# # #         id=order_id,
# # #         user=request.user,
# # #     )
# # #
# # #     items = order.items.select_related("variant", "variant__product").all()
# # #
# # #     return render(request, "hr_shop/checkout/_order_receipt_modal.html", {
# # #         "order": order,
# # #         "items": items,
# # #         "customer": order.customer,
# # #         "address": order.shipping_address,
# # #         "is_guest": False,
# # #     })
# #
# #
# # # =====================================================================================================================
# # #  Site-admin creation (superusers only via terminal; site admins created by superuser)
# # # =====================================================================================================================
# # #
# # # @user_passes_test(lambda u: u.is_superuser)
# # # def admin_create_site_admin(request):
# # #     if request.method == "POST":
# # #         form = AccountCreationForm(request.POST)
# # #         if not form.is_valid():
# # #             return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": form})
# # #
# # #         # staff == site admin, never superuser
# # #         user = form.create_user(role=User.Role.SITE_ADMIN)
# # #
# # #         return HttpResponse(status=204, headers={
# # #             "HX-Trigger": json.dumps({
# # #                 "dialogChanged": None,
# # #                 "showMessage": f"Created site admin {user.username}",
# # #             })
# # #         })
# # #
# # #     return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": AccountCreationForm()})
# # #
# # #
# # # # =====================================================================================================================
# # # #  Superuser/global-admin demotion UI (message box modal)
# # # # =====================================================================================================================
# # #
# # # # @user_passes_test(lambda u: u.is_superuser)
# # # # def admin_confirm_privilege_demotion(request, user_id: int):
# # # #     target = get_object_or_404(User, pk=user_id)
# # # #
# # # #     removing_superuser = target.is_superuser
# # # #     removing_global_role = (target.role == User.Role.GLOBAL_ADMIN)
# # # #
# # # #     confirm_url = reverse("hr_access:admin_demote_superuser", args=[target.pk])
# # # #
# # # #     return display_message_box_modal(
# # # #         request,
# # # #         title="Confirm removal of elevated privileges",
# # # #         message=(
# # # #             f"You are about to change privileges for {target.username} ({target.email}). "
# # # #             f"{'This will remove superuser status. ' if removing_superuser else ''}"
# # # #             f"{'This will remove Global Admin role.' if removing_global_role else ''}"
# # # #         ),
# # # #         level="warning",
# # # #         confirm_url=confirm_url,
# # # #         confirm_method="post",
# # # #         confirm_label="Yes, remove privileges",
# # # #         cancel_url=reverse("hr_access:admin_cancel_privilege_demotion", args=[target.pk]),
# # # #         cancel_label="Cancel",
# # # #     )
# # #
# # #
# # # @user_passes_test(lambda u: u.is_superuser)
# # # @require_POST
# # # def admin_demote_superuser(request, user_id: int):
# # #     target = get_object_or_404(User, pk=user_id)
# # #
# # #     # Guard: cannot demote the last superuser
# # #     if target.is_superuser and not User.objects.exclude(pk=target.pk).filter(is_superuser=True).exists():
# # #         return display_message_box_modal(
# # #             request,
# # #             title="Cannot remove last superuser",
# # #             message="You must have at least one superuser account. Create another superuser first.",
# # #             level="error",
# # #             confirm_url="",
# # #             confirm_label="OK",
# # #         )
# # #
# # #     # Demote: superuser off, global -> site admin
# # #     target.is_superuser = False
# # #     if target.role == User.Role.GLOBAL_ADMIN:
# # #         target.role = User.Role.SITE_ADMIN
# # #     target.save()
# # #
# # #     return display_message_box_modal(
# # #         request,
# # #         title="Privileges updated",
# # #         message=f"{target.username}'s elevated privileges have been removed.",
# # #         level="success",
# # #         confirm_url="",
# # #         confirm_label="Close",
# # #     )
# # #
# # #
# # # @user_passes_test(lambda u: u.is_superuser)
# # # def admin_cancel_privilege_demotion(request, user_id: int):
# # #     return HttpResponse(status=204, headers={
# # #         "HX-Trigger": json.dumps({"messageBoxClosed": f"Canceled superuser removal for ID {user_id}"})
# # #     })
# #
# #
# # # =====================================================================================================================
# # #  Post-purchase account creation + order claim
# # # =====================================================================================================================
# #
# # @require_GET
# # def account_get_post_purchase_create_account(request, order_id: int):
# #     if request.user.is_authenticated:
# #         return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")
# #
# #     order = get_object_or_404(Order, pk=order_id)
# #     form = AccountCreationForm(locked_email=(order.email or ""))
# #
# #     return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {
# #         "order": order,
# #         "form": form,
# #     })
# #
# #
# # @require_POST
# # def account_submit_post_purchase_create_account(request, order_id: int):
# #     if request.user.is_authenticated:
# #         return render(request, "hr_access/post_purchase/_post_purchase_account_done.html")
# #
# #     order = get_object_or_404(Order, pk=order_id)
# #     locked_email = normalize_email(order.email or "")
# #
# #     post = request.POST.copy()
# #     post["email"] = locked_email
# #
# #     form = AccountCreationForm(post, locked_email=locked_email)
# #     if not form.is_valid():
# #         return render(request, "hr_access/post_purchase/_post_purchase_account_form.html", {
# #             "order": order,
# #             "form": form,
# #         })
# #
# #     with transaction.atomic():
# #         user = form.create_user(role=User.Role.USER)
# #
# #         cust = getattr(order, "customer", None)
# #         if cust and cust.user_id is None:
# #             cust.user = user
# #             cust.save(update_fields=["user", "updated_at"])
# #
# #         if getattr(order, "user_id", None) is None:
# #             order.user = user
# #             order.save(update_fields=["user", "updated_at"])
# #
# #     login(request, user)
# #
# #     other_orders = (
# #         Order.objects.filter(email__iexact=locked_email, user__isnull=True)
# #         .exclude(pk=order.id)
# #         .order_by("-created_at")[:25]
# #     )
# #
# #     return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
# #         "order": order,
# #         "other_orders": other_orders,
# #     })
# #
# #
# # @require_POST
# # def account_submit_post_purchase_claim_orders(request, order_id: int):
# #     if not request.user.is_authenticated:
# #         return HttpResponse(status=401)
# #
# #     order = get_object_or_404(Order, pk=order_id)
# #     email = normalize_email(order.email or "")
# #
# #     if normalize_email(request.user.email) != email:
# #         return HttpResponse(status=403)
# #
# #     raw_ids = request.POST.getlist("order_ids")
# #     order_ids = [int(x) for x in raw_ids if str(x).isdigit()]
# #     if not order_ids:
# #         return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
# #             "order": order,
# #             "other_orders": (
# #                 Order.objects.filter(email__iexact=email, user__isnull=True)
# #                 .exclude(pk=order.id)
# #                 .order_by("-created_at")[:25]
# #             ),
# #             "claimed_count": 0,
# #         })
# #
# #     with transaction.atomic():
# #         qs = Order.objects.select_for_update().filter(
# #             id__in=order_ids,
# #             user__isnull=True,
# #             email__iexact=email,
# #         )
# #         claimed_count = qs.update(user=request.user)
# #
# #     remaining = (
# #         Order.objects.filter(email__iexact=email, user__isnull=True)
# #         .exclude(pk=order.id)
# #         .order_by("-created_at")[:25]
# #     )
# #
# #     return render(request, "hr_access/post_purchase/_post_purchase_account_success.html", {
# #         "order": order,
# #         "other_orders": remaining,
# #         "claimed_count": claimed_count,
# #     })
#
#
# # @require_GET
# # def account_get_unclaimed_orders(request):
# #     if not request.user.is_authenticated:
# #         return HttpResponse(status=401)
# #
# #     email = normalize_email(getattr(request.user, "email", "") or "")
# #     if not email:
# #         return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
# #             "email": "",
# #             "account_get_orders": [],
# #             "error": "No email address is associated with your account.",
# #         })
# #
# #     unclaimed_orders = (
# #         Order.objects.filter(user__isnull=True, email__iexact=email)
# #         .order_by("-created_at")[:50]
# #     )
# #
# #     return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
# #         "email": email,
# #         "account_get_orders": unclaimed_orders,
# #         "error": None,
# #     })
# #
# #
# # @require_POST
# # def account_submit_claim_unclaimed_orders(request):
# #     if not request.user.is_authenticated:
# #         return HttpResponse(status=401)
# #
# #     email = normalize_email(getattr(request.user, "email", "") or "")
# #     if not email:
# #         return HttpResponse(status=400)
# #
# #     raw_ids = request.POST.getlist("order_ids")
# #     order_ids = [int(x) for x in raw_ids if str(x).isdigit()]
# #
# #     if not order_ids:
# #         remaining = (
# #             Order.objects.filter(user__isnull=True, email__iexact=email)
# #             .order_by("-created_at")[:50]
# #         )
# #         return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
# #             "email": email,
# #             "account_get_orders": remaining,
# #             "error": "Select at least one order to claim.",
# #             "claimed_count": 0,
# #         })
# #
# #     with transaction.atomic():
# #         qs = Order.objects.select_for_update().filter(
# #             id__in=order_ids,
# #             user__isnull=True,
# #             email__iexact=email,
# #         )
# #         claimed_count = qs.update(user=request.user)
# #
# #     remaining = (
# #         Order.objects.filter(user__isnull=True, email__iexact=email)
# #         .order_by("-created_at")[:50]
# #     )
# #
# #     return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
# #         "email": email,
# #         "account_get_orders": remaining,
# #         "error": None,
# #         "claimed_count": claimed_count,
# #     })
