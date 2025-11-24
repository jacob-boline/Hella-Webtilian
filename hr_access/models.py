# hr_access/models.py

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext as _

from hr_access.managers import UserManager
from hr_core.utils.email import normalize_email


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        GLOBAL_ADMIN = 'global_admin', 'Global Admin'
        SITE_ADMIN = 'site_admin', 'Site Admin'
        USER = 'user', 'User'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER,)
    email = models.EmailField(_("email address"), unique=True, blank=False, null=False, max_length=254)
    first_name = models.CharField(_("First Name"), max_length=254, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=254, blank=True)
    username = models.CharField(max_length=30, unique=True, null=False, blank=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

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

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name_plural = "users"
        ordering = ["email"]
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.pk}-{self.email}"

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        super(User, self).save(*args, **kwargs)
