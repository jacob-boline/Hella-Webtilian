# hr_access/signals.py

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from hr_access.constants import SITE_ADMIN_GROUP_NAME, GLOBAL_ADMIN_GROUP_NAME

UserModel = get_user_model()


def _get_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


@receiver(pre_save, sender=UserModel)
def cache_old_role(sender, instance: UserModel, **_kwargs):
    """
    Cache the prior role on the instance so post_save can know if role changed
    without an extra "old role" query after the save.
    """
    if not instance.pk:
        instance._old_role = None
        return

    try:
        old = sender.objects.only("role").get(pk=instance.pk)
        instance._old_role = old.role
    except sender.DoesNotExist:
        instance._old_role = None


@receiver(post_save, sender=UserModel)
def sync_user_role_to_groups(sender, instance: UserModel, created: bool, update_fields=None, **_kwargs):
    """
    Keep Django Groups and staff/superuser flags in sync with User.role.

    Canonical truth: instance.role
    Derived:
      - GLOBAL_ADMIN:
          * is_superuser = True
          * is_staff = True
          * groups = {GLOBAL_ADMIN, SITE_ADMIN}
      - SITE_ADMIN:
          * is_superuser = False
          * is_staff = True
          * groups = {SITE_ADMIN}
      - USER:
          * is_superuser = False
          * is_staff = False
          * groups = {}
    """

    # Fast exit: if role was not part of update_fields, nothing to do.
    # Note: update_fields can be None (normal save), so only skip when it's explicitly present.
    if update_fields is not None and "role" not in update_fields:
        return

    old_role = getattr(instance, "_old_role", None)
    role_changed = created or (old_role is None) or (old_role != instance.role)

    # If role didn't change, skip. (Created users always sync once.)
    if not role_changed:
        return

    site_admin_group = _get_group(SITE_ADMIN_GROUP_NAME)
    global_admin_group = _get_group(GLOBAL_ADMIN_GROUP_NAME)

    # Compute desired derived state
    if instance.role == instance.Role.GLOBAL_ADMIN:
        desired_is_staff = True
        desired_is_superuser = True
        desired_groups = [global_admin_group, site_admin_group]
    elif instance.role == instance.Role.SITE_ADMIN:
        desired_is_staff = True
        desired_is_superuser = False
        desired_groups = [site_admin_group]
    else:
        desired_is_staff = False
        desired_is_superuser = False
        desired_groups = []

    # Update flags only if needed (avoid extra writes)
    flags_changed = (
        instance.is_staff != desired_is_staff
        or instance.is_superuser != desired_is_superuser
    )

    if flags_changed:
        sender.objects.filter(pk=instance.pk).update(
            is_staff=desired_is_staff,
            is_superuser=desired_is_superuser,
        )
        # keep in-memory instance consistent for the rest of the request
        instance.is_staff = desired_is_staff
        instance.is_superuser = desired_is_superuser

    # Set groups to EXACTLY match desired role groups.
    # Use on_commit so we don't mess with m2m if the outer transaction rolls back.
    def _sync_groups():
        instance.groups.set(desired_groups)

    transaction.on_commit(_sync_groups)
