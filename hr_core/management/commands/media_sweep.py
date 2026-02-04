# hr_core/management/commands/media_sweep.py

from pathlib import Path

import django_rq
from django.conf import settings
from django.core.management.base import BaseCommand

from hr_core.media_jobs import RECIPES


class Command(BaseCommand):
    help = "Enqueue missing/outdated optimized media variants for known recipe buckets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipe",
            choices=sorted(RECIPES.keys()),
            help="Only sweep a specific recipe (e.g. wipe, background, post_hero, variant, about).",
        )

    def handle(self, *args, **options):
        recipe_key = options.get("recipe")
        keys = [recipe_key] if recipe_key else list(RECIPES.keys())

        q = django_rq.get_queue("default")
        enqueued = 0

        for key in keys:
            recipe = RECIPES[key]

            if recipe.src_root == "media":
                root = Path(settings.MEDIA_ROOT)
            elif recipe.src_root == "static_src":
                root = Path(settings.STATIC_SOURCE_ROOT)
            elif recipe.src_root == 'repo_static':
                root = Path(settings.REPO_STATIC_ROOT)
            else:
                self.stdout.write(self.style.WARNING(f"Unknown src_root for recipe {key}: {recipe.src_root} (skip)"))
                continue

            src_dir = root / recipe.src_rel_dir

            if not src_dir.exists():
                self.stdout.write(self.style.WARNING(f"Missing dir: {src_dir} (skip)"))
                continue

            for p in src_dir.iterdir():
                if not p.is_file() or p.name.startswith("."):
                    continue

                if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".avif"}:
                    continue

                # For static_src recipes, pass path relative to STATIC_SOURCE_ROOT
                rel = str(p.relative_to(root))
                q.enqueue("hr_core.media_jobs.generate_variants_for_file", key, rel)
                enqueued += 1

        self.stdout.write(self.style.SUCCESS(f"Enqueued {enqueued} source files."))
