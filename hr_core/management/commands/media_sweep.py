# hr_core/management/commands/media_sweep.py

# ================================================
#  DEV - python manage.py rqworker default
#
#  PROD - cron job ~10min:
#       python manage.py media_sweep --recipe wipe
#       python manage.py media_sweep --recipe background
# ===============================================

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
        media_root = Path(settings.MEDIA_ROOT)

        enqueued = 0

        for key in keys:
            recipe = RECIPES[key]
            src_dir = (media_root / recipe.src_rel_dir)

            if not src_dir.exists():
                self.stdout.write(self.style.WARNING(f"Missing dir: {src_dir} (skip)"))
                continue

            for p in src_dir.iterdir():
                if not p.is_file():
                    continue
                if p.name.startswith("."):
                    continue

                # only source images
                if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                    continue

                rel = str(p.relative_to(media_root))
                q.enqueue("hr_core.media_jobs.generate_variants_for_file", key, rel)
                enqueued += 1

        self.stdout.write(self.style.SUCCESS(f"Enqueued {enqueued} source files."))
