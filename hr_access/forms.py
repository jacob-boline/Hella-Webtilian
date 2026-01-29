# hr_access/forms.py

from __future__ import annotations

from typing import Any

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    ReadOnlyPasswordHashField,
    UserChangeForm,
)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from hr_access.constants import RESERVED_USERNAMES
from hr_access.models import User
from hr_common.utils.email import normalize_email

# ------------------------------------------------------------
# Validators
# ------------------------------------------------------------

username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9._-]{5,150}$",
    message=_("Only letters, numbers, dots, underscores, and dashes are allowed.")
)


# ------------------------------------------------------------
# Shared validation mixin
# ------------------------------------------------------------


class AccountValidationMixin:
    cleaned_data: dict[str, Any]
    instance: Any
    """
    Shared username/email validation for:
    - public account creation
    - post-purchase claim
    - admin user edit
    """

    def _clean_username_common(self) -> str:
        raw = (self.cleaned_data.get("username") or "").strip()
        ci = raw.casefold()

        if ci in RESERVED_USERNAMES:
            raise ValidationError(_("That username is unavailable."))

        qs = User.objects.filter(username_ci=ci)

        instance = getattr(self, "instance", None)
        if instance and getattr(instance, "pk", None):
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError(_("That username is unavailable."))

        self.cleaned_data["username_ci"] = ci
        return raw

    def _clean_email_common(self) -> str:
        email = normalize_email(self.cleaned_data.get("email") or "")

        qs = User.objects.filter(email__iexact=email)

        instance = getattr(self, "instance", None)
        if instance and getattr(instance, "pk", None):
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError(_("An account with this email already exists."))

        return email


# ------------------------------------------------------------
# Account creation (public / claim / staff)
# ------------------------------------------------------------


class AccountCreationForm(AccountValidationMixin, forms.Form):
    """
    Single-password account creation form.

    Used for:
    - public account_signup
    - post-purchase account_signup (locked_email)
    - internal staff creation (via create_user flags)
    """

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "email",
                "autocapitalize": "none",
                "spellcheck": "false",
                "inputmode": "email",
            }
        )
    )

    username = forms.CharField(
        min_length=5,
        max_length=150,
        strip=True,
        validators=[username_validator],
        help_text=_("5–150 chars. Letters, numbers, dots, dashes, underscores only."),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "autocapitalize": "none",
                "spellcheck": "false",
                "inputmode": "text",
                "placeholder": "username",
            }
        ),
    )

    password = forms.CharField(
        min_length=8,
        max_length=255,
        strip=True,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "password",
                "autocapitalize": "none",
                "spellcheck": "false",
            }
        ),
        help_text=password_validation.password_validators_help_text_html(),
    )

    def __init__(self, *args, locked_email: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.locked_email = normalize_email(locked_email) if locked_email else None

        if self.locked_email:
            self.fields["email"].initial = self.locked_email
            self.fields["email"].widget.attrs["readonly"] = "readonly"
            self.fields["email"].widget.attrs["aria-readonly"] = "true"

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email") or "")

        if self.locked_email and email != self.locked_email:
            raise ValidationError(_("This email is locked to the one used for this order."))

        self.cleaned_data["email"] = email
        return self._clean_email_common()

    def clean_username(self):
        return self._clean_username_common()

    def clean_password(self):
        pw = self.cleaned_data.get("password") or ""
        password_validation.validate_password(pw, user=None)
        return pw

    def create_user(self, *, role: str | None = None, is_staff: bool = False, is_active: bool = True) -> User:
        """
        Call after is_valid().
        Creates and saves a User instance.
        """
        user = User(email=self.cleaned_data["email"], username=self.cleaned_data["username"], is_staff=is_staff, is_active=is_active)

        if role and hasattr(User, "Role"):
            user.role = role

        user.set_password(self.cleaned_data["password"])
        user.save()
        return user


# ------------------------------------------------------------
# Authentication (login)
# ------------------------------------------------------------


class AccountAuthenticationForm(AuthenticationForm):
    """
    Login form for username OR email.
    Backend determines which.
    """

    def clean_username(self):
        return (self.cleaned_data.get("username") or "").strip()


# ------------------------------------------------------------
# Admin edit form (existing users)
# ------------------------------------------------------------


class AccountAdminChangeForm(AccountValidationMixin, UserChangeForm):
    """
    Django admin edit-user form.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def clean_email(self):
        self.cleaned_data["email"] = normalize_email(self.cleaned_data.get("email") or "")
        return self._clean_email_common()

    def clean_username(self):
        return self._clean_username_common()


# ------------------------------------------------------------
# Account email change
# ------------------------------------------------------------


class AccountEmailChangeForm(AccountValidationMixin, forms.Form):
    new_email = forms.EmailField(
        label=_("New email"),
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": _("new email"),
                "autocapitalize": "none",
                "spellcheck": "false",
                "inputmode": "email",
            }
        ),
    )
    password = forms.CharField(
        label=_("Current password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": _("current password"),
            }
        ),
    )

    def __init__(self, user: User, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.instance = user

    def clean_new_email(self):
        email = normalize_email(self.cleaned_data.get("new_email") or "")
        if email == normalize_email(self.user.email or ""):
            raise ValidationError(_("That's already your email address."))

        self.cleaned_data["email"] = email
        return self._clean_email_common()

    def clean_password(self):
        pw = self.cleaned_data.get("password") or ""
        if not self.user.check_password(pw):
            raise ValidationError(_("Incorrect password."))
        return pw
