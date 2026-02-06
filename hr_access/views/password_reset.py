# hr_access/views/password_reset.py

from __future__ import annotations

from urllib.parse import urlencode

from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

import logging

from hr_common.utils.http.htmx import is_htmx
from hr_common.utils.unified_logging import log_event

logger = logging.getLogger(__name__)


class AccountPasswordResetView(PasswordResetView):
    template_name = "hr_access/password_reset/_password_reset_form.html"
    email_template_name = "hr_access/password_reset/password_reset_email.txt"
    html_email_template_name = "hr_access/password_reset/password_reset_email.html"
    subject_template_name = "hr_access/password_reset/password_reset_subject.txt"
    success_url = reverse_lazy("hr_access:password_reset_done")

    def form_valid(self, form):
        resp = super().form_valid(form)
        log_event(logger, logging.INFO, "access.password_reset.requested")
        if is_htmx(self.request):
            return render(self.request, "hr_access/password_reset/_password_reset_done.html")
        return resp


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "hr_access/password_reset/_password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "hr_access/password_reset/_password_reset_confirm.html"
    success_url = reverse_lazy("hr_access:password_reset_complete")

    def dispatch(self, request, *args, **kwargs):
        if is_htmx(request) or request.GET.get("handoff") == "0":
            return super().dispatch(request, *args, **kwargs)

        qs = request.GET.copy()
        qs["handoff"] = "0"
        modal_url = f"{request.path}?{qs.urlencode()}"
        log_event(logger, logging.INFO, "access.password_reset.handoff_redirect")
        params = urlencode(
            {
                "modal": "password_reset",
                "handoff": "password_reset",
                "modal_url": modal_url,
            }
        )
        return redirect(f"{reverse('index')}?{params}")

    def form_valid(self, form):
        self.object = form.save()
        log_event(logger, logging.INFO, "access.password_reset.completed")
        if is_htmx(self.request):
            return render(self.request, "hr_access/password_reset/_password_reset_complete.html")
        return super().form_valid(form)


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "hr_access/password_reset/_password_reset_complete.html"
