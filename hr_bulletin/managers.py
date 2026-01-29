# hr_bulletin/managers.py

from django.db import models
from django.utils import timezone


class PostQuerySet(models.QuerySet):

    def published(self):
        now = timezone.now()
        qs = self.filter(status="published")
        return qs.filter(models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=now))

    def drafts(self):
        return self.filter(status="draft")

    def frontpage(self):
        return self.published().order_by(*self.model._meta.ordering)


class PostManager(models.Manager):

    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def drafts(self):
        return self.get_queryset().drafts()

    def frontpage(self):
        return self.get_queryset().frontpage()
