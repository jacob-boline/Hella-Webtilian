# hr_access/models.py

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from hr_common.db.fields import NormalizedEmailField
from hr_access.constants import RESERVED_USERNAMES
from hr_access.managers import UserManager


username_chars = RegexValidator(
    regex=r"^[a-zA-Z0-9._-]{5,150}$",
    message=_("5–150 chars. Use letters, numbers, dots, underscores, and dashes only."),
)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        GLOBAL_ADMIN = 'global_admin', 'Global Admin'
        SITE_ADMIN = 'site_admin', 'Site Admin'
        USER = 'user', 'User'

    email: str
    email =               NormalizedEmailField(_("email address"), unique=True, blank=False, null=False)
    role =                models.CharField(max_length=20, choices=Role.choices, default=Role.USER,)
    first_name =          models.CharField(_("First Name"), max_length=254, blank=True)
    last_name =           models.CharField(_("Last Name"),  max_length=254, blank=True)
    username =            models.CharField(max_length=150, unique=False, null=False, blank=False, validators=[MinLengthValidator(5)])
    username_ci =         models.CharField(max_length=150, unique=True, editable=False, db_index=True, validators=[MinLengthValidator(5)])
    is_staff =            models.BooleanField(default=False)
    is_superuser =        models.BooleanField(default=False)
    is_active =           models.BooleanField(default=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    deleted_at =          models.DateTimeField(null=True, blank=True)

    @property
    def is_site_admin(self):
        return self.role == self.Role.SITE_ADMIN

    @property
    def is_global_admin(self):
        return self.role == self.Role.GLOBAL_ADMIN

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    objects = UserManager()

    USERNAME_FIELD = "username_ci"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        verbose_name_plural = "users"
        ordering = ["email"]

        # The below can replace the username_ci field on the model IF ON POSTGRES
        #
        # constraints = [
        #     models.UniqueConstraint(
        #         Lower('username'),
        #         name='uniq_user_username_lower'
        #     )
        # ]

    def __str__(self):
        return f"{self.pk}-{self.email}"

    def clean(self):
        super().clean()
        norm = (self.username or "").strip().casefold()
        if norm in RESERVED_USERNAMES:
            raise ValidationError({"username": _("That username is reserved.")})

    def save(self, *args, **kwargs):
        self.username = (self.username or "").strip()
        self.username_ci = self.username.casefold()

        if self.username_ci in RESERVED_USERNAMES:
            raise ValidationError({"username": _("That username is reserved.")})

        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.password_changed_at = timezone.now()
