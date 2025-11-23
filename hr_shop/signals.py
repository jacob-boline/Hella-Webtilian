# hr_shop/signals.py

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .services.customers import attach_guest_orders_for_user


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def link_guest_orders_when_user_saved(_sender, instance, **kwargs):
    attach_guest_orders_for_user(instance)
