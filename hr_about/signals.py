# hr_about/signals.py

import django_rq
from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_about.models import CarouselSlide


@receiver(post_save, sender=CarouselSlide)
def enqueue_about_slide_variants(sender, instance: CarouselSlide, **kwargs):
    if not instance.image:
        return

    q = django_rq.get_queue("default")
    q.enqueue("hr_core.media_jobs.generate_variants_for_file", "about", instance.image.name)
