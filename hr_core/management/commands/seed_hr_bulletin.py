# hr_core/management/commands/seed_hr_bulletin.py

import shutil
from datetime import timedelta
from pathlib import Path
from typing import cast

import yaml
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db.models.fields.files import ImageFieldFile
from django.utils import timezone

from hr_bulletin.models import Post, Tag

POST_METADATA = {
    ("Matt Elliott", "Drinking Songs"): {
        "title": "Drinking Songs: Matt Elliott's Slow-Burn Confession",
        "tags": ["Album Review", "Post-Rock", "Chanson", "Melancholy"],
    },
    ("Between the Buried and Me", "Colors"): {
        "title": "BTBAM's Colors: A Kaleidoscope with Teeth",
        "tags": ["Album Review", "Progressive Metal", "Genre-Bending", "Technical"],
    },
    ("Every Time I Die", "Low Teens"): {
        "title": "Low Teens: Every Time I Die's Fluorescent Bruise",
        "tags": ["Album Review", "Hardcore", "Rock 'n' Roll", "Cathartic"],
    },
    ("Protest the Hero", "Fortress"): {
        "title": "Fortress: Protest the Hero's Golden Machine",
        "tags": ["Album Review", "Prog Metalcore", "Riffs", "Satire"],
    },
    ("Dethklok", "Dethalbum II"): {
        "title": "Dethalbum II: A Sledgehammer with a Punchline",
        "tags": ["Album Review", "Melodic Death Metal", "Metal", "Humor"],
    },
    ("The Mars Volta", "Amputecture"): {
        "title": "Amputechture: The Mars Volta's Gravity Rebellion",
        "tags": ["Album Review", "Art Rock", "Progressive", "Chaos"],
    },
    ("Animals as Leaders", "Animals as Leaders"): {
        "title": "Animals as Leaders: The CNC-Jazz Blueprint",
        "tags": ["Album Review", "Instrumental", "Djent", "Fusion"],
    },
    ("Blowfly", "Zodiac Blowfly"): {
        "title": "Zodiac Blowfly: Funk, Filth, and the Zodiac Wheel",
        "tags": ["Album Review", "Funk", "Comedy", "70s"],
    },
    ("Caravan Palace", "Chronologic"): {
        "title": "Chronologic: Caravan Palace in Neon Motion",
        "tags": ["Album Review", "Electro Swing", "Electro-Pop", "Dance"],
    },
    ("Les Racquet", "Whale Hail"): {
        "title": "Whale Hail: Les Racquet's Road-Run Groove",
        "tags": ["Album Review", "Indie Rock", "Road Notes", "Groove"],
    },
    ("Leprous", "Coal"): {
        "title": "Coal: Leprous and the Slow Eclipse",
        "tags": ["Album Review", "Progressive Metal", "Dark", "Atmosphere"],
    },
    ("Nick Mulvey", "First Mind"): {
        "title": "First Mind: Nick Mulvey's Quiet Pulse",
        "tags": ["Album Review", "Folk", "Singer-Songwriter", "Rhythmic"],
    },
    ("The Human Abstract", "Digital Veil"): {
        "title": "Digital Veil: The Human Abstract's Gothic Geometry",
        "tags": ["Album Review", "Metalcore", "Neoclassical", "Precision"],
    },
}


class Command(BaseCommand):
    help = "Seed hr_bulletin posts + tags from _seed_data/hr_bulletin/outline.yml."

    def handle(self, *args, **options):
        self._seed_hr_bulletin()



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

        self._wipe_posts_hero_media()

        for idx, post_cfg in enumerate(posts_cfg, start=1):
            artist = post_cfg.get("key") or "Unknown Artist"
            album = post_cfg.get("album") or "Untitled Album"
            body = post_cfg.get("body") or ""
            image = post_cfg.get("image") or ""

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
                    "allow_comments": True,
                },
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
                        "allow_comments",
                    ]
                )

            self._attach_hero_image(post, image, seed_base=base)
            self._sync_tags(post, tags)

        self.stdout.write("    • hr_bulletin seed data applied.")

    def _wipe_posts_hero_media(self):
        """
        Clear generated hero media so reseeds don't accumulate stale files.
        Safe: only runs when DEBUG=True.
        """
        if not settings.DEBUG:
            self.stdout.write(self.style.WARNING("    • Skipping hero wipe (DEBUG=False)."))
            return

        media_root = Path(settings.MEDIA_ROOT)
        hero_dir = media_root / "posts" / "hero"
        hero_dir.mkdir(parents=True, exist_ok=True)

        # adjust if your optimizer outputs elsewhere
        opt_dirs = [
            hero_dir / "opt",
            hero_dir / "opt_webp",
        ]

        # wipe optimized dirs first
        for d in opt_dirs:
            if d.exists() and d.is_dir():
                shutil.rmtree(d)
                self.stdout.write(f"    • Deleted {d}")

        # wipe files directly under posts/hero (keep the folder)
        if hero_dir.exists() and hero_dir.is_dir():
            for p in hero_dir.iterdir():
                if p.is_file():
                    p.unlink()
            self.stdout.write(f"    • Cleared files in {hero_dir}")
        else:
            self.stdout.write(f"    • Not found: {hero_dir}")

    @staticmethod
    def _get_author():
        User = get_user_model()
        return User.objects.order_by("id").first()

    def _attach_hero_image(self, post: Post, image_path: str, seed_base: Path):
        """
        image_path is expected to be one of:
          - absolute path
          - relative to _seed_data/hr_bulletin (recommended: img/<file>)
          - relative to BASE_DIR (legacy)
        """
        if not image_path:
            return

        # If DB already points at a hero and the file exists in storage, do nothing.
        if not self._needs_file(post.hero):
            return

        resolved_path = Path(image_path)

        if not resolved_path.is_absolute():
            candidate = seed_base / image_path
            if candidate.exists():
                resolved_path = candidate
            else:
                resolved_path = Path(settings.BASE_DIR) / image_path

        if not resolved_path.exists():
            self.stdout.write(self.style.WARNING(f"    • Image not found for '{post.title}': {resolved_path}"))
            return

        with resolved_path.open("rb") as handle:
            # name becomes posts/hero/<filename> because upload_to="posts/hero/"
            post.hero.save(resolved_path.name, File(handle), save=True)

    @staticmethod
    def _sync_tags(post: Post, tags):
        tag_objs = []
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objs.append(tag)

        post.tags.set(tag_objs)
