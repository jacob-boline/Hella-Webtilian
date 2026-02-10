# hr_core/management/commands/seed_hr_bulletin.py

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import cast

import yaml
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone

from hr_bulletin.models import Post, Tag
from hr_core.management.commands.seed_data import attach_image_if_missing

POST_METADATA = {
    ("Matt Elliott", "Drinking Songs"): {
        "title": "Drinking Songs: Matt Elliott's Slow-Burn Confession",
        "tags": ["Album Review", "Post-Rock", "Chanson", "Melancholy"]
    },
    ("Between the Buried and Me", "Colors"): {
        "title": "BTBAM's Colors: A Kaleidoscope with Teeth",
        "tags": ["Album Review", "Progressive Metal", "Genre-Bending", "Technical"]
    },
    ("Every Time I Die", "Low Teens"): {
        "title": "Low Teens: Every Time I Die's Fluorescent Bruise",
        "tags": ["Album Review", "Hardcore", "Rock 'n' Roll", "Cathartic"]
    },
    ("Protest the Hero", "Fortress"): {
        "title": "Fortress: Protest the Hero's Golden Machine",
        "tags": ["Album Review", "Prog Metalcore", "Riffs", "Satire"]
    },
    ("Dethklok", "Dethalbum II"): {
        "title": "Dethalbum II: A Sledgehammer with a Punchline",
        "tags": ["Album Review", "Melodic Death Metal", "Metal", "Humor"]
    },
    ("The Mars Volta", "Amputecture"): {
        "title": "Amputechture: The Mars Volta's Gravity Rebellion",
        "tags": ["Album Review", "Art Rock", "Progressive", "Chaos"]
    },
    ("Animals as Leaders", "Animals as Leaders"): {
        "title": "Animals as Leaders: The CNC-Jazz Blueprint",
        "tags": ["Album Review", "Instrumental", "Djent", "Fusion"]
    },
    ("Blowfly", "Zodiac Blowfly"): {
        "title": "Zodiac Blowfly: Funk, Filth, and the Zodiac Wheel",
        "tags": ["Album Review", "Funk", "Comedy", "70s"]
    },
    ("Caravan Palace", "Chronologic"): {
        "title": "Chronologic: Caravan Palace in Neon Motion",
        "tags": ["Album Review", "Electro Swing", "Electro-Pop", "Dance"]
    },
    ("Les Racquet", "Whale Hail"): {
        "title": "Whale Hail: Les Racquet's Road-Run Groove",
        "tags": ["Album Review", "Indie Rock", "Road Notes", "Groove"]
    },
    ("Leprous", "Coal"): {
        "title": "Coal: Leprous and the Slow Eclipse",
        "tags": ["Album Review", "Progressive Metal", "Dark", "Atmosphere"]
    },
    ("Nick Mulvey", "First Mind"): {
        "title": "First Mind: Nick Mulvey's Quiet Pulse",
        "tags": ["Album Review", "Folk", "Singer-Songwriter", "Rhythmic"]
    },
    ("The Human Abstract", "Digital Veil"): {
        "title": "Digital Veil: The Human Abstract's Gothic Geometry",
        "tags": ["Album Review", "Metalcore", "Neoclassical", "Precision"]
    }
}


class Command(BaseCommand):
    help = "Seed hr_bulletin posts + tags from _seed_data/hr_bulletin/outline.yml."

    def handle(self, *args, **options):
        self._seed_hr_bulletin()

    # ------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------
    @staticmethod
    def _needs_file(fieldfile) -> bool:
        if not fieldfile:
            return True

        ff = cast(ImageFieldFile, fieldfile)
        try:
            if not ff.name:
                return True
            return not ff.storage.exists(ff.name)
        except Exception:
            return True

    @staticmethod
    def _normalize_media_key(key: str) -> str:
        """
        With AWS_PUBLIC_MEDIA_LOCATION='media', default_storage keys are relative
        to that prefix.

        Accept:
          - 'posts/hero/foo.webp'
          - 'media/posts/hero/foo.webp'
          - '/media/posts/hero/foo.webp'
        """
        k = (key or "").strip().replace("\\", "/").lstrip("/")
        if k.startswith("media/"):
            k = k.removeprefix("media/")
        return k

    def _open_media(self, key: str):
        """
        Try local MEDIA_ROOT first, otherwise storage.
        Returns an open file-like object or raises FileNotFoundError.
        """
        k = self._normalize_media_key(key)

        local_path = Path(settings.MEDIA_ROOT) / k
        if local_path.exists():
            return local_path.open("rb")

        if default_storage.exists(k):
            return default_storage.open(k, "rb")

        raise FileNotFoundError(f"Media not found (local or storage) for key: {k}")

    # ------------------------------------------------------
    # Seed driver
    # ------------------------------------------------------
    def _seed_hr_bulletin(self):
        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_bulletin"
        if not base.exists():
            self.stdout.write(self.style.WARNING(f"  → No _seed_data/hr_bulletin directory found at {base}"))
            return

        outline_yml = base / "outline.yml"
        if not outline_yml.exists():
            self.stdout.write(self.style.WARNING(f"  → No outline.yml found in {base}; nothing to seed."))
            return

        cfg = yaml.safe_load(outline_yml.read_text(encoding="utf-8-sig")) or {}
        posts_cfg = cfg.get("posts") or []

        if not posts_cfg:
            self.stdout.write(self.style.WARNING("  → outline.yml contains no posts; skipping."))
            return

        author = self._get_author()
        if not author:
            self.stdout.write(self.style.WARNING("  → No users exist; cannot assign post.author. Skipping."))
            return

        now = timezone.now()
        self.stdout.write("  → hr_bulletin…")

        for idx, post_cfg in enumerate(posts_cfg, start=1):
            artist = post_cfg.get("key") or "Unknown Artist"
            album = post_cfg.get("album") or "Untitled Album"
            body = post_cfg.get("body") or ""

            # STRICT: require image_key for posts
            image_key = post_cfg.get("image_key")
            if not image_key:
                raise CommandError(f"Post '{album}' by '{artist}' is missing required 'image_key' in outline.yml")

            meta = POST_METADATA.get((artist, album), {})
            title = meta.get("title") or f"{album} by {artist}"
            tags = meta.get("tags") or ["Album Review"]

            publish_at = now - timedelta(days=len(posts_cfg) - idx)

            post, created = Post.objects.get_or_create(
                title=title,
                defaults={
                    "body": body,
                    "status": "published",
                    "publish_at": publish_at,
                    "author": author,
                    "allow_comments": True
                }
            )

            if not created:
                post.body = body
                post.status = "published"
                post.publish_at = publish_at
                post.author = author
                post.allow_comments = True
                post.save(
                    update_fields=[
                        "body",
                        "status",
                        "publish_at",
                        "author",
                        "allow_comments"
                    ]
                )

            self._attach_hero_image(post, str(image_key))
            self._sync_tags(post, tags)

        self.stdout.write("    • hr_bulletin seed data applied.")

    @staticmethod
    def _get_author():
        User = get_user_model()
        return User.objects.order_by("id").first()

    def _attach_hero_image(self, post: Post, image_key: str):
        """
        Attach post.hero from a logical media key, e.g.:
            posts/hero/foo.webp

        Loads from local MEDIA_ROOT first, else storage (S3) via default_storage.
        """
        if not image_key:
            return

        k = self._normalize_media_key(image_key)

        try:
            with self._open_media(k) as handle:
                attach_image_if_missing(post, 'hero', k, handle)
        except FileNotFoundError as e:
            raise CommandError(f"Hero image missing for '{post.title}': {e}")

    @staticmethod
    def _sync_tags(post: Post, tags):
        tag_objs = []
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objs.append(tag)
        post.tags.set(tag_objs)
