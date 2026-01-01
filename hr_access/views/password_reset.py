# hr_access/views/password_reset.py

from __future__ import annotations

from __future__ import annotations

from urllib.parse import urlencode

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


class AccountPasswordResetView(PasswordResetView):
    template_name = "hr_access/password_reset/_password_reset_form.html"
    email_template_name = "hr_access/password_reset/password_reset_email.txt"
    html_email_template_name = "hr_access/password_reset/password_reset_email.html"
    subject_template_name = "hr_access/password_reset/password_reset_subject.txt"
    success_url = reverse_lazy("hr_access:password_reset_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        if _is_htmx(self.request):
            return render(self.request, "hr_access/password_reset/_password_reset_done.html")
        return response


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "hr_access/password_reset/_password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "hr_access/password_reset/_password_reset_confirm.html"
    success_url = reverse_lazy("hr_access:password_reset_complete")

    def dispatch(self, request, *args, **kwargs):
        if _is_htmx(request) or request.GET.get("handoff") == "0":
            return super().dispatch(request, *args, **kwargs)

        qs = request.GET.copy()
        qs["handoff"] = "0"
        modal_url = f"{request.path}?{qs.urlencode()}"
        params = urlencode({
            "modal": "password_reset",
            "handoff": "password_reset",
            "modal_url": modal_url,
        })
        return redirect(f"{reverse('index')}?{params}")

    def form_valid(self, form):
        self.object = form.save()
        if _is_htmx(self.request):
            return render(self.request, "hr_access/password_reset/_password_reset_complete.html")
        return super().form_valid(form)


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "hr_access/password_reset/_password_reset_complete.html"
