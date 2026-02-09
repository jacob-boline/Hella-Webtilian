# hr_bulletin/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from hr_bulletin.models import Post
from hr_core.image_batch import schedule_image_variants


@receiver(post_save, sender=Post)
def enqueue_post_hero_variants(sender, instance: Post, **kwargs):
    if not instance.hero:
        return

    # instance.hero.name is relative to MEDIA_ROOT, e.g. "posts/hero/foo.jpg"
    schedule_image_variants("post_hero", instance.hero.name)
