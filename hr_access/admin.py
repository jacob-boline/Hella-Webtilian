# hr_access/admin.py

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from hr_access.forms import AccountAdminChangeForm, AccountValidationMixin
from hr_common.utils.email import normalize_email

User = get_user_model()


class AccountAdminAddForm(AccountValidationMixin, forms.ModelForm):
    """
    Admin add form with a SINGLE password field.

    Reuses AccountValidationMixin for username/email rules, but is a ModelForm
    so BaseUserAdmin.add_view works properly.
    """
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "role", "is_active")

    def clean_email(self):
        self.cleaned_data["email"] = normalize_email(self.cleaned_data.get("email") or "")
        return self._clean_email_common()

    def clean_username(self):
        return self._clean_username_common()

    def clean_password(self):
        pw = self.cleaned_data.get("password") or ""
        password_validation.validate_password(pw, user=None)
        return pw

    def save(self, commit: bool = True):
        user = super().save(commit=False)

        user.email = self.cleaned_data.get("email")
        user.username = (self.cleaned_data.get("username") or "").strip()
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            self.save_m2m()

        # NOTE: role->groups/staff/superuser happens in post_save signal
        return user


@admin.register(User)
class AccountAdmin(BaseUserAdmin):
    add_form = AccountAdminAddForm
    form = AccountAdminChangeForm
    model = User

    list_display = ["email", "username", "role", "is_superuser", "is_staff", "is_active"]
    list_filter = ["role", "is_superuser", "is_staff", "is_active"]

    # Existing user edit
    fieldsets = (
        (None, {"fields": ("username", "username_ci", "email", "password")}),
        ("Role & Status", {"fields": ("role", "is_active")}),
        # These are derived by signals; show but lock.
        ("Derived Permissions (role based)", {"fields": ("is_staff", "is_superuser", "groups")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    # Add user (single password field)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password", "role", "is_active"),
        }),
    )

    # role-derived fields should be read-only to avoid "changed back" confusion
    readonly_fields = ("username_ci", "is_staff", "is_superuser", "groups", "last_login")

    search_fields = ["email", "username", "username_ci"]
    ordering = ["email"]
    filter_horizontal = ()  # groups is readonly; user_permissions omitted

    def save_model(self, request, obj, form, change):
        UserModel = self.model

        if change:
            old = UserModel.objects.get(pk=obj.pk)

            demoting_from_admin = (
                old.role == UserModel.Role.GLOBAL_ADMIN and
                obj.role != UserModel.Role.GLOBAL_ADMIN
            )

            if demoting_from_admin:
                has_other_admin = UserModel.objects.exclude(pk=obj.pk).filter(
                    role=UserModel.Role.GLOBAL_ADMIN,
                    is_active=True,
                ).exists()

                if not has_other_admin:
                    messages.error(
                        request,
                        "You cannot demote the last Global Admin. "
                        "Create another Global Admin first."
                    )
                    return  # Skip saving

        super().save_model(request, obj, form, change)
