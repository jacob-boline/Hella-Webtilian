# hr_access/management/commands/setup_roles.py

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from hr_about.models import CarouselSlide, PullQuote
from hr_access.constants import SITE_ADMIN_GROUP_NAME
from hr_bulletin.models import Post, Tag
from hr_shop.models import Order, Product, ProductVariant


class Command(BaseCommand):
    help = "Create Site admin group and assign persmissions"

    def handle(self, *args, **options):
        site_admin_group, created = Group.objects.get_or_create(name=SITE_ADMIN_GROUP_NAME)
        allowed_models = [Post, Tag, Product, ProductVariant, CarouselSlide, PullQuote]
        perms = Permission.objects.filter(content_type__in=[ContentType.objects.get_for_model(m) for m in allowed_models])
        site_admin_group.permissions.set(perms)
        order_ct = ContentType.objects.get_for_model(Order)
        view_order_perm = Permission.objects.get(content_type=order_ct, codename="view_order")
        site_admin_group.permissions.add(view_order_perm)
        self.stdout.write(self.style.SUCCESS("Site admin group configured."))
