# from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from hr_access.managers import UserManager
from django.utils.translation import gettext as _


# class User(AbstractUser):
#     avatar = models.ImageField(verbose_name="Avatar Image", upload_to="user_avatar", null=True, blank=False)
#     email = models.EmailField(verbose_name="Email", null=True, blank=False)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True, blank=False, null=False, max_length=254)
    first_name = models.CharField(_("First Name"), max_length=254, blank=True)
    last_name = models.CharField(_("Last Namne"), max_length=254, blank=True)
    # avatar = models.ImageField(verbose_name="Avatar Image", upload_to="user_avatar", null=True, blank=True)
    username = models.CharField(max_length=30, unique=True, null=False, blank=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name_plural = "users"
        ordering = ["email"]
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.pk}-{self.email}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        self.email = self.email.casefold()
        super(User, self).save(*args, **kwargs)
