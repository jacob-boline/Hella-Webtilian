# hr_access/signals.py

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_access.constants import SITE_ADMIN_GROUP_NAME, GLOBAL_ADMIN_GROUP_NAME


UserModel = get_user_model()


def _get_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


@receiver(post_save, sender=UserModel)
def sync_user_role_to_groups(sender, instance: UserModel, created, **_kwargs):
    """
       Keep Django Groups and staff/superuser flags in sync with User.role.

       - GLOBAL_ADMIN:
           * is_superuser = True
           * is_staff = True
       - SITE_ADMIN:
           * is_superuser = False
           * is_staff = True
       - USER:
           * is_superuser = False
           * is_staff = False
       """

    qs = instance.__class__.objects

    site_admin_group = _get_group(SITE_ADMIN_GROUP_NAME)
    global_admin_group = _get_group(GLOBAL_ADMIN_GROUP_NAME)

    if instance.role == instance.__class__.Role.GLOBAL_ADMIN:
        instance.is_superuser = True
        instance.is_staff = True
        qs.filter(pk=instance.pk).update(is_superuser=True, is_staff=True)
        instance.groups.add(global_admin_group, site_admin_group)
        return

    if instance.role == instance.__class__.Role.SITE_ADMIN:
        instance.is_superuser = False
        instance.is_staff = True
        qs.filter(pk=instance.pk).update(is_superuser=False, is_staff=True)
        instance.groups.add(site_admin_group)
        instance.groups.remove(global_admin_group)
        return

    # Normal user
    instance.is_superuser = False
    instance.is_staff = False
    qs.filter(pk=instance.pk).update(is_staff=False, is_superuser=False)
    instance.groups.remove(site_admin_group, global_admin_group)
    return
