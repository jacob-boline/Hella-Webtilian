# hr_access/views/admin.py

from __future__ import annotations

import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from hr_access.forms import AccountCreationForm
from hr_access.models import User
from hr_site.views import display_message_box_modal
from utils.http import hx_superuser_required


@hx_superuser_required
def admin_create_site_admin(request):
    """
    Internal "create site admin" view (superusers only).
    Superusers are created via terminal only.
    """
    if request.method == "POST":
        form = AccountCreationForm(request.POST)
        if not form.is_valid():
            # Keep your existing template name (you already have it)
            from django.shortcuts import render
            return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": form})

        user = form.create_user(role=User.Role.SITE_ADMIN)

        return HttpResponse(status=204, headers={
            "HX-Trigger": json.dumps({
                "dialogChanged": None,
                "showMessage": f"Created site admin {user.username}",
            })
        })

    from django.shortcuts import render
    return render(request, "hr_access/user_admin/add_staff_form.html", {"add_staff_form": AccountCreationForm()})


@hx_superuser_required
def admin_confirm_privilege_demotion(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)

    removing_superuser = target.is_superuser
    removing_global_role = (target.role == User.Role.GLOBAL_ADMIN)

    confirm_url = reverse("hr_access:admin_demote_superuser", args=[target.pk])

    return display_message_box_modal(
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


@hx_superuser_required
@require_POST
def admin_demote_superuser(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)

    # Guard against demoting the last superuser
    if target.is_superuser and not User.objects.exclude(pk=target.pk).filter(is_superuser=True).exists():
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

    return display_message_box_modal(
        request,
        title="Privileges updated",
        message=f"{target.username}'s elevated privileges have been removed.",
        level="success",
        confirm_url="",
        confirm_label="Close",
    )


@hx_superuser_required
@require_POST
def admin_cancel_privilege_demotion(_request, user_id: int):
    return HttpResponse(status=204, headers={
        "HX-Trigger": json.dumps({
            "messageBoxClosed": f"Canceled privilege demotion for ID {user_id}"
        })
    })
