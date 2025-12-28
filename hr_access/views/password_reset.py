# hr_access/views/password_reset.py

from __future__ import annotations

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)


class AccountPasswordResetView(PasswordResetView):
    template_name = "hr_access/registration/../templates/hr_access/password_reset/_password_reset_form.html"
    email_template_name = "hr_access/registration/password_reset_email.txt"
    html_email_template_name = "hr_access/registration/password_reset_email.html"
    subject_template_name = "hr_access/registration/password_reset_subject.txt"


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = "hr_access/registration/../templates/hr_access/password_reset/_password_reset_done.html"


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "hr_access/registration/password_reset_confirm.html"
    htmx_template_name = "hr_access/registration/_password_reset_confirm.html"


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "hr_access/registration/password_reset_complete.html"
    htmx_template_name = "hr_access/registration/_password_reset_complete.html"
