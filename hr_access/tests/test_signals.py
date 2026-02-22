# hr_access/tests/test_signals.py

import pytest
from django.contrib.auth.models import Group

from hr_access.constants import GLOBAL_ADMIN_GROUP_NAME, SITE_ADMIN_GROUP_NAME
from hr_access.models import User


@pytest.mark.django_db
def test_created_global_admin_gets_flags_and_groups(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        user = User.objects.create_user(
            email="ga@example.com",
            username="globaladmin",
            password="StrongPass123!",
            role=User.Role.GLOBAL_ADMIN,
            is_staff=False,
            is_superuser=False,
        )

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.is_superuser is True
    assert set(user.groups.values_list("name", flat=True)) == {GLOBAL_ADMIN_GROUP_NAME, SITE_ADMIN_GROUP_NAME}


@pytest.mark.django_db
def test_role_change_syncs_exact_group_membership_and_flags(django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        user = User.objects.create_user(
            email="sa@example.com",
            username="siteadmin",
            password="StrongPass123!",
            role=User.Role.SITE_ADMIN,
        )

    user.refresh_from_db()
    assert user.is_staff is True
    assert user.is_superuser is False
    assert set(user.groups.values_list("name", flat=True)) == {SITE_ADMIN_GROUP_NAME}

    with django_capture_on_commit_callbacks(execute=True):
        user.role = User.Role.USER
        user.save(update_fields=["role"])

    user.refresh_from_db()

    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.groups.count() == 0


@pytest.mark.django_db
def test_update_fields_without_role_fast_exit_does_not_resync_groups():
    user = User.objects.create_user(
        email="ga2@example.com",
        username="globaladmin2",
        password="StrongPass123!",
        role=User.Role.GLOBAL_ADMIN,
    )
    user.refresh_from_db()

    site_admin_group = Group.objects.get(name=SITE_ADMIN_GROUP_NAME)
    user.groups.set([site_admin_group])

    user.first_name = "Touched"
    user.save(update_fields=["first_name"])
    user.refresh_from_db()

    assert set(user.groups.values_list("name", flat=True)) == {SITE_ADMIN_GROUP_NAME}
    
