# hr_shop/management/commands/cleanup_checkout_drafts.py

from django.core.management.base import BaseCommand
from django.utils import timezone

from hr_shop.models import CheckoutDraft


class Command(BaseCommand):
    help = "Delete expired or used checkout drafts"

    def handle(self, *args, **options):
        now = timezone.now()

        expired_qs = CheckoutDraft.objects.filter(expires_at__lt=now)
        used_qs = CheckoutDraft.objects.filter(used_at__isnull=False)

        expired_count = expired_qs.count()
        used_count = used_qs.count()

        expired_qs.delete()
        used_qs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"CheckoutDraft cleanup complete: "
                f"{expired_count} expired, {used_count} used"
            )
        )
