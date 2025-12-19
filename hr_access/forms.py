# hr_access/forms.py

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, ReadOnlyPasswordHashField, AuthenticationForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User

username_validator = UnicodeUsernameValidator()


def _normalize_email(email: str) -> str:
    return (email or '').strip().casefold()


class CustomUserCreationForm(UserCreationForm):
    """
    Public signup form. Uses Django's built-in password checks.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = _normalize_email(self.cleaned_data.get('email'))
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with that email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = _normalize_email(self.cleaned_data['email'])
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password',)


class StaffForm(UserCreationForm):
    """
    Internal staff/site-admin creation form.
    """
    email = forms.EmailField(
        max_length=254,
        help_text=_("Required. Enter a valid email address."),
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=password_validation.password_validators_help_text_html())

    password2 = forms.CharField(
        label=_('Password Confirmation'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('Confirm Password'))

    username = forms.CharField(
        label=_('Username'),
        max_length=150,
        help_text=_('Required. Max 150 characters. Letters, digits, and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={'unique': _('Username is unavailable.')},
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = _normalize_email(self.cleaned_data.get('email'))
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with that email already exists'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = _normalize_email(self.cleaned_data['email'])
        if hasattr(User, 'Role'):
            user.role = User.Role.SITE_ADMIN
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class SetPasswordForm(forms.Form):
    """
    For claim-your-account flow (shadow → active).
    """
    password1 = forms.CharField(label=_('New password'), widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label=_('Confirm password'), widget=forms.PasswordInput, strip=False)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 != p2:
            raise ValidationError(_('Passwords do not match'))
        password_validation.validate_password(p1)
        return cleaned
