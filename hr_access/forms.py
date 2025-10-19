from django.contrib.auth.forms import UserChangeForm, UserCreationForm, ReadOnlyPasswordHashField
from django import forms
from django.core.exceptions import ValidationError

from .models import User
from django.contrib.auth import password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _


username_validator = UnicodeUsernameValidator()


class CustomUserCreationForm(UserCreationForm):
    model = User
    fields = ('username', 'email', 'password1', 'password2')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_passworrd(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('password',)


class StaffForm(UserCreationForm):

    email = forms.EmailField(
        max_length=50,
        help_text="Required. Enter a valid email address.",
        widget=(forms.TextInput(attrs={'class': 'form-control'})))

    password1 = forms.CharField(
        label=_('Password'),
        widget=(forms.PasswordInput(attrs={'class': 'form-control'})),
        help_text=password_validation.password_validators_help_text_html())

    password2 = forms.CharField(
        label=_('Password Confirmation'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Confirm Password')

    username = forms.CharField(
        label=_('Username'),
        max_length=150,
        help_text='Required. Max 150 characters. Letters, digits, and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={'unique': _('Username is unavailable.')},
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        mnodel = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(StaffForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        # user.avater = self.cleaned_data['avatar']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
