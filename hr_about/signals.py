# hr_about/signals.py

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_about.models import CarouselSlide
from hr_core.image_batch import schedule_image_variants


@receiver(post_save, sender=CarouselSlide)
def enqueue_about_slide_variants(sender, instance: CarouselSlide, **kwargs):

    if not getattr(settings, "ENABLE_MEDIA_JOBS", False):
        return

    if not instance.image:
        return

    schedule_image_variants("about", instance.image.name)
