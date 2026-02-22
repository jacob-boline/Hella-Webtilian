# hr_access/tests/test_forms.py

import pytest

from hr_access.forms import AccountCreationForm, AccountEmailChangeForm
from hr_access.models import User


@pytest.mark.django_db
def test_account_creation_form_rejects_reserved_username():
    form = AccountCreationForm(data={"email": "person@example.com", "username": "merch", "password": "StrongPass123!"})

    assert form.is_valid() is False
    assert "username" in form.errors


@pytest.mark.django_db
def test_account_creation_form_rejects_case_insensitive_username_duplicates():
    User.objects.create_user(email="one@example.com", username="ExistingUser", password="StrongPass123!")

    form = AccountCreationForm(data={"email": "two@example.com", "username": "existinguser", "password": "StrongPass123!"})

    assert form.is_valid() is False
    assert "username" in form.errors


@pytest.mark.django_db
def test_account_creation_form_rejects_case_insensitive_email_duplicates():
    User.objects.create_user(email="one@example.com", username="existinguser", password="StrongPass123!")

    form = AccountCreationForm(data={"email": "ONE@EXAMPLE.COM", "username": "newuser", "password": "StrongPass123!"})

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_account_creation_form_locked_email_is_immutable():
    form = AccountCreationForm(
        data={"email": "other@example.com", "username": "newuser", "password": "StrongPass123!"},
        locked_email="locked@example.com",
    )

    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_account_email_change_form_requires_correct_password_and_unique_email():
    user = User.objects.create_user(email="current@example.com", username="currentuser", password="StrongPass123!")
    User.objects.create_user(email="taken@example.com", username="takenuser", password="StrongPass123!")

    wrong_password_form = AccountEmailChangeForm(
        user,
        data={"new_email": "fresh@example.com", "password": "bad"},
    )
    assert wrong_password_form.is_valid() is False
    assert "password" in wrong_password_form.errors

    duplicate_email_form = AccountEmailChangeForm(
        user,
        data={"new_email": "TAKEN@EXAMPLE.COM", "password": "StrongPass123!"},
    )
    assert duplicate_email_form.is_valid() is False
    assert "new_email" in duplicate_email_form.errors
