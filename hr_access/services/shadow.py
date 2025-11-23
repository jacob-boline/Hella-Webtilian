# hr_access/services/shadow.py

import secrets
from django.utils.text import slugify
from django.contrib.auth import get_user_model


User = get_user_model()


def _guest_username_seed(email: str) -> str:
    name = slugify((email or '').split('@')[0]) or 'guest'
    return f'guest-{name}-{secrets.token_hex(3)}'


def get_or_create_shadow_user(email: str) -> User:
    email = (email or '').strip().casefold()
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': _guest_username_seed(email),
            'is_active': False,
            'role': getattr(User.Role, 'USER', 'user'),
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
    return user