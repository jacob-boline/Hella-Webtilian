# hr_access/signals.py

from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from hr_access.constants import SITE_ADMIN_GROUP_NAME, GLOBAL_ADMIN_GROUP_NAME


def _get_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_role_to_groups(_sender, instance: User, _created, **_kwargs):
    """
       Keep Django Groups and staff/superuser flags in sync with User.role.

       - GLOBAL_ADMIN:
           * is_superuser = True
           * is_staff = True
           * add to Global admin group
           * add to Site admin group (if you want them to inherit those perms)
       - SITE_ADMIN:
           * is_superuser = False (unless you want to allow overlap)
           * is_staff = True
           * add to Site admin group
           * remove from Global admin group
       - USER:
           * is_superuser unchanged (you can choose to reset it)
           * is_staff = False (optional)
           * remove from Site admin + Global admin groups
       """

    qs = instance.__class__.objects

    site_admin_group = _get_group(SITE_ADMIN_GROUP_NAME)
    global_admin_group = _get_group(GLOBAL_ADMIN_GROUP_NAME)

    if instance.role == User.Role.GLOBAL_ADMIN:
        qs.filter(pk=instance.pk).update(is_superuser=True, is_staff=True)
        instance.groups.add(global_admin_group, site_admin_group)
        return

    if instance.role == User.Role.SITE_ADMIN:
        qs.filter(pk=instance.pk).update(is_superuser=False, is_staff=True)
        instance.groups.add(site_admin_group)
        instance.groups.remove(global_admin_group)
        return

    # Normal user
    qs.filter(pk=instance.pk).update(is_staff=False, is_superuser=False)
    instance.groups.remove(site_admin_group, global_admin_group)
