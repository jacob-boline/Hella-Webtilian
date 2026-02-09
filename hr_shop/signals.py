# hr_shop/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_core.image_batch import schedule_image_variants
from hr_shop.models import ProductImage


@receiver(post_save, sender=ProductImage)
def enqueue_variant_image_variants(sender, instance: ProductImage, **kwargs):
    if not instance.image:
        return

    schedule_image_variants("variant", instance.image.name)
