# hr_bulletin/models.py

from django.conf import settings
from django.db import models
from django.utils import timezone

from hr_bulletin.managers import PostManager
from hr_core.utils.slug import sync_slug_from_source


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        source = self.name
        sync_slug_from_source(self, source, max_length=160)
        super().save(*args, **kwargs)


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status="published")


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published')
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    body = models.TextField()  # wHTML or Markdown
    hero = models.ImageField(upload_to='posts/hero/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    publish_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='posts')
    pin_until = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    allow_comments = models.BooleanField(default=False)

    objects = PostManager()

    class Meta:
        ordering = ['-pin_until', '-publish_at', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_pinned(self):
        return self.pin_until and self.pin_until > timezone.now()

    @property
    def is_published(self):
        return self.status == 'published' and (not self.publish_at or self.publish_at <= timezone.now())

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.title, slug_field_name="slug", allow_update=True, max_length=220)
        super().save(*args, **kwargs)
