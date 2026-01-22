# hr_shop/signals.py

import django_rq
from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_shop.models import ProductImage


@receiver(post_save, sender=ProductImage)
def enqueue_variant_image_variants(sender, instance: ProductImage, **kwargs):
    if not instance.image:
        return

    q = django_rq.get_queue("default")
    q.enqueue("hr_core.media_jobs.generate_variants_for_file", "variant", instance.image.name)
