# hr_core/management/commands/seed_hr_bulletin.py

from datetime import timedelta
from pathlib import Path

import yaml
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
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
    help = "Seed hr_bulletin posts + tags from seed_data/hr_bulletin/outline.yml."

    def handle(self, *args, **options):
        self._seed_hr_bulletin()

    def _seed_hr_bulletin(self):
        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_bulletin"
        if not base.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"  → No seed_data/hr_bulletin directory found at {base}"
                )
            )
            return

        outline_yml = base / "outline.yml"
        if not outline_yml.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"  → No outline.yml found in {base}; nothing to seed."
                )
            )
            return

        cfg = yaml.safe_load(outline_yml.read_text()) or {}
        posts_cfg = cfg.get("posts") or []

        if not posts_cfg:
            self.stdout.write(
                self.style.WARNING("  → outline.yml contains no posts; skipping.")
            )
            return

        author = self._get_author()
        now = timezone.now()

        self.stdout.write("  → hr_bulletin…")

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

            self._attach_hero_image(post, image)
            self._sync_tags(post, tags)

        self.stdout.write("    • hr_bulletin seed data applied.")

    @staticmethod
    def _get_author():
        User = get_user_model()
        return User.objects.order_by("id").first()

    def _attach_hero_image(self, post: Post, image_path: str):
        if not image_path:
            return

        resolved_path = Path(image_path)
        if not resolved_path.is_absolute():
            resolved_path = Path(settings.BASE_DIR) / image_path

        if not resolved_path.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"    • Image not found for '{post.title}': {resolved_path}"
                )
            )
            return

        if post.hero and Path(post.hero.name).name == resolved_path.name:
            return

        with resolved_path.open("rb") as handle:
            post.hero.save(resolved_path.name, File(handle), save=True)

    @staticmethod
    def _sync_tags(post: Post, tags):
        tag_objs = []
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objs.append(tag)

        post.tags.set(tag_objs)

