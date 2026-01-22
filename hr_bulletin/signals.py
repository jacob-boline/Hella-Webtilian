# hr_bulletin/signals.py

import django_rq
from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_bulletin.models import Post


@receiver(post_save, sender=Post)
def enqueue_post_hero_variants(sender, instance: Post, **kwargs):
    if not instance.hero:
        return

    q = django_rq.get_queue("default")
    # instance.hero.name is relative to MEDIA_ROOT, e.g. "posts/hero/foo.jpg"
    q.enqueue("hr_core.media_jobs.generate_variants_for_file", "post_hero", instance.hero.name)
