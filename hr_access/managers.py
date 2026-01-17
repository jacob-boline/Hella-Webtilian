# hr_access/managers.py

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from hr_access.constants import RESERVED_USERNAMES
from hr_common.utils.email import normalize_email


class UserManager(BaseUserManager):
    use_in_migrations = True

    @staticmethod
    def _normalize_username(username: str) -> tuple[str, str]:
        raw = (username or "").strip()
        norm = raw.casefold()
        return raw, norm

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        email = normalize_email(email)
        raw_username, username_ci = self._normalize_username(username)

        if username_ci in RESERVED_USERNAMES:
            raise ValidationError({"username": _("That username is reserved.")})

        extra_fields.setdefault("is_active", True)

        user = self.model(
            email=email,
            username=raw_username,     # preserve typed case (minus whitespace)
            username_ci=username_ci,   # normalized key
            **extra_fields
        )
        user.set_password(password)

        # Run model validators (MinLengthValidator, RegexValidator, etc.)
        user.full_clean()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.GLOBAL_ADMIN)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)
