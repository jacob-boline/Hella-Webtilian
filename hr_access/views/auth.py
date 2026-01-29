# hr_access/views/auth.py

from __future__ import annotations

import logging

from django.contrib.auth import login, logout
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from hr_access.forms import AccountAuthenticationForm
from hr_common.utils.http.htmx import hx_trigger
from hr_common.utils.http.messages import show_message
from hr_common.utils.unified_logging import log_event
from hr_shop.models import Order

logger = logging.getLogger(__name__)


@require_POST
def auth_login(request):
    """
    Sidebar login endpoint.
    - Success: 204 + HX-Trigger(accessChanged)
    - Failure: returns sidebar panel partial with errors.
    """
    form = AccountAuthenticationForm(request, data=request.POST)

    if form.is_valid():
        login(request, form.get_user())
        log_event(logger, logging.INFO, "access.auth.login.success")
        return hx_trigger({"accessChanged": None, "authSuccess": None, "showMessage": show_message("Signed in.")}, status=204)

    log_event(logger, logging.INFO, "access.auth.login.invalid")
    return render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})


@require_POST
def auth_logout(request):
    logout(request)
    log_event(logger, logging.INFO, "access.auth.logout")
    return hx_trigger({"accessChanged": None, "showMessage": show_message("You have been logged out.")}, status=204)


@require_GET
def account_get_sidebar_panel(request):
    """
    HTMX-loaded sidebar container that swaps between login panel and user panel.
    """
    log_event(logger, logging.INFO, "access.sidebar.rendered")
    return render(request, "hr_access/_sidebar_access.html", {"authentication_form": AccountAuthenticationForm(request)})


@require_GET
def account_get_user_panel(request):
    """
    User panel fragment (used by sidebar once authenticated).
    """
    email = request.user.email
    unclaimed_count = Order.objects.filter(user__isnull=True, email__iexact=email).count() if email else 0

    log_event(logger, logging.INFO, "access.user_panel.rendered", unclaimed_count=unclaimed_count)
    return render(request,"hr_access/_user_panel.html", {"unclaimed_count": unclaimed_count})
