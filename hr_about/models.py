# hr_about/models.py

from django.db import models
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class CarouselSlide(models.Model):
    title = models.CharField(max_length=255)
    caption = models.TextField(blank=True)
    image = models.ImageField(upload_to='carousel/')
    image_thumb = ImageSpecField(source='image', processors=[ResizeToFill(220, 220)], format='JPEG', options={'quality': 80},)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.order}: {self.title}"


class PullQuote(models.Model):
    attribution = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Quote {self.order} - {self.attribution or 'Anonymous'}"
