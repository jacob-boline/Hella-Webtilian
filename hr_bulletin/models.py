# hr_bulletin/models.py

import hashlib
import os

from django.conf import settings
from django.db import models
from django.utils import timezone

from hr_bulletin.managers import PostManager
from hr_common.db.slug import sync_slug_from_source


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = [
            "name",
        ]

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
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    body = models.TextField()  # HTML or Markdown
    hero = models.ImageField(upload_to="posts/hero/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    publish_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="posts")
    pin_until = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    allow_comments = models.BooleanField(default=False)

    objects = PostManager()

    class Meta:
        ordering = ["-pin_until", "-publish_at", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_pinned(self):
        return self.pin_until and self.pin_until > timezone.now()

    @property
    def is_published(self):
        return self.status == "published" and (not self.publish_at or self.publish_at <= timezone.now())

    # -------------------------
    # Hash-based hero dedupe
    # -------------------------

    @staticmethod
    def _sha256_stream(file_obj, chunk_size: int = 1024 * 1024) -> str:
        """
        Compute sha256 for a file-like object, restoring stream position afterward.
        """
        h = hashlib.sha256()

        try:
            pos = file_obj.tell()
        except Exception:
            pos = None

        try:
            if hasattr(file_obj, "seek"):
                try:
                    file_obj.seek(0)
                except Exception:
                    pass

            while True:
                chunk = file_obj.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        finally:
            if pos is not None and hasattr(file_obj, "seek"):
                try:
                    file_obj.seek(pos)
                except Exception:
                    pass

        return h.hexdigest()

    def _dedupe_hero_by_hash(self) -> None:
        """
        Store/reuse hero images by content hash.

        IMPORTANT: We keep the final stored path *flat* under posts/hero/
        so your existing variant pipeline continues to work:

          Original: posts/hero/<sha256><ext>
          Variants:  posts/hero/opt/<sha256>-640w.webp, etc.

        This avoids Django's name-collision suffixing and prevents duplicate copies.
        """
        if not self.hero:
            return

        # Only process newly assigned uploads (seeded or staff upload).
        if getattr(self.hero, "_committed", True):
            return

        storage = self.hero.storage

        # Try to access underlying file object
        try:
            fobj = self.hero.file
        except Exception:
            # As a fallback, open via FieldFile
            try:
                self.hero.open("rb")
                fobj = self.hero.file
            except Exception:
                return

        sha = self._sha256_stream(fobj)

        # Preserve extension (lowercased). If missing, default .bin
        _, ext = os.path.splitext(self.hero.name or "")
        ext = (ext or "").lower() or ".bin"

        # Flat destination to keep your current opt/ layout stable
        relpath = f"posts/hero/{sha}{ext}"

        # If it already exists, just point at it
        if storage.exists(relpath):
            self.hero.name = relpath
            self.hero._committed = True
            return

        # Save once under the deterministic name, then point FieldFile at it
        if hasattr(fobj, "seek"):
            try:
                fobj.seek(0)
            except Exception:
                pass

        storage.save(relpath, fobj)
        self.hero.name = relpath
        self.hero._committed = True

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.title, slug_field_name="slug", allow_update=True, max_length=220)

        # Ensure hero is deduped before model save triggers file handling
        self._dedupe_hero_by_hash()

        super().save(*args, **kwargs)
