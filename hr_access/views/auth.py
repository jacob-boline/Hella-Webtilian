# hr_access/views/auth.py

from __future__ import annotations

import json
from logging import getLogger

from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from hr_access.forms import AccountAuthenticationForm

logger = getLogger()


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
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps({
                    "accessChanged": None,
                    "showMessage": "Signed in.",
                })
            },
        )

    return render(request, "hr_access/_sidebar_access.html", {"authentication_form": form})


@require_POST
def auth_logout(request):
    logout(request)
    return HttpResponse(
        status=204,
        headers={
            "HX-Trigger": json.dumps({
                "accessChanged": None,
                "bulletinChanged": None,
                "dialogChanged": None,
                "showsChanged": None,
                "showMessage": "You have been logged out.",
            })
        },
    )


@require_GET
def account_get_sidebar_panel(request):
    """
    HTMX-loaded sidebar container that swaps between login panel and user panel.
    """
    return render(request, "hr_access/_sidebar_access.html", {
        "authentication_form": AccountAuthenticationForm(request),
    })


@require_GET
def account_get_user_panel(request):
    """
    User panel fragment (used by sidebar once authenticated).
    """
    return render(request, "hr_access/_user_panel.html")
