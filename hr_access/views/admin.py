# hr_access/views/admin.py

from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from hr_access.forms import AccountCreationForm
from hr_access.models import User
from hr_common.utils.http.htmx import hx_trigger, merge_hx_trigger_after_settle
from hr_common.utils.http.messages import show_message
from hr_common.utils.htmx_responses import hx_superuser_required
from hr_common.utils.unified_logging import log_event
from hr_common.views import display_message_box_modal

logger = logging.getLogger(__name__)


@hx_superuser_required
def admin_create_site_admin(request):
    """
    Internal "create site admin" view (superusers only).
    Superusers are created via terminal only.
    """
    if request.method == "POST":
        form = AccountCreationForm(request.POST)
        if not form.is_valid():
            from django.shortcuts import render

            log_event(logger, logging.INFO, "access.admin.create_site_admin.form_invalid")
            return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": form})

        user = form.create_user(role=User.Role.SITE_ADMIN)

        log_event(logger, logging.INFO, "access.admin.create_site_admin.created", target_user_id=user.id, username=user.username)
        return hx_trigger({"dialogChanged": None, "showMessage": show_message(f"Created site admin {user.username}")}, status=204)

    from django.shortcuts import render

    log_event(logger, logging.INFO, "access.admin.create_site_admin.form_rendered")
    return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": AccountCreationForm()})


@hx_superuser_required
def admin_confirm_privilege_demotion(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)

    removing_superuser = target.is_superuser
    removing_global_role = target.role == User.Role.GLOBAL_ADMIN

    confirm_url = reverse("hr_access:admin_demote_superuser", args=[target.pk])

    resp = display_message_box_modal(
        request,
        title="Confirm removal of elevated privileges",
        message=(
            f"You are about to change privileges for {target.username} ({target.email}). "
            f"{'This will remove superuser status. ' if removing_superuser else ''}"
            f"{'This will remove Global Admin role.' if removing_global_role else ''}"
        ),
        level="warning",
        confirm_url=confirm_url,
        confirm_method="post",
        confirm_label="Yes, remove privileges",
        cancel_url=reverse("hr_access:admin_cancel_privilege_demotion", args=[target.pk]),
        cancel_label="Cancel",
    )
    log_event(logger, logging.INFO, "access.admin.demote.confirm_rendered", target_user_id=target.id)
    return resp


@hx_superuser_required
@require_POST
def admin_demote_superuser(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)

    # Guard against demoting the last superuser
    if target.is_superuser and not User.objects.exclude(pk=target.pk).filter(is_superuser=True).exists():
        log_event(logger, logging.WARNING, "access.admin.demote.last_superuser_blocked", target_user_id=target.id)
        return display_message_box_modal(
            request,
            title="Cannot remove last superuser",
            message="You must have at least one superuser account. Create another superuser first.",
            level="error",
            confirm_url="",
            confirm_label="OK",
        )

    target.is_superuser = False
    if target.role == User.Role.GLOBAL_ADMIN:
        target.role = User.Role.SITE_ADMIN
    target.save()

    log_event(logger, logging.INFO, "access.admin.demote.completed", target_user_id=target.id)
    resp = display_message_box_modal(
        request,
        title="Privileges updated",
        message=f"{target.username}'s elevated privileges have been removed.",
        level="success",
        confirm_url="",
        confirm_label="Close",
    )
    return merge_hx_trigger_after_settle(resp, {"dialogChanged": None})


@hx_superuser_required
@require_POST
def admin_cancel_privilege_demotion(_request, user_id: int):
    log_event(logger, logging.INFO, "access.admin.demote.canceled", target_user_id=user_id)
    return hx_trigger({"messageBoxClosed": f"Canceled privilege demotion for ID {user_id}"}, status=204)
