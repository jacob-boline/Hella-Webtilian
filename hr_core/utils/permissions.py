# hr_core/utils/permissions.py

from django.contrib.auth.decorators import login_required, user_passes_test


def is_site_admin(user) -> bool:
    """
    True for:
      - superusers
      - users with custom property `is_site_admin` on your User model
      - users in the 'Site admin' group
    """
    if not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    # custom property on hr_access.User, if you add/use it
    if bool(getattr(user, "is_site_admin", False)):
        return True

    # group membership; Group.DoesNotExist won't be raised here, so no try/except needed
    return user.groups.filter(name="Site admin").exists()


def staff_or_site_admin_required(view_func):
    """
    Decorator: require authenticated + is_site_admin(user).

    Usage:
        @staff_or_site_admin_required
        def some_view(request):
            ...
    """
    return login_required(user_passes_test(is_site_admin)(view_func))