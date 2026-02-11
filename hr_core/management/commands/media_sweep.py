# hr_core/management/commands/media_sweep.py

from pathlib import Path

import django_rq
from django.conf import settings
from django.core.management.base import BaseCommand

from hr_core.media_jobs import generate_variants_for_file
from hr_core.media_jobs import RECIPES

WORKER_HINT = "Start an RQ worker to process jobs: python manage.py rqworker default"

class Command(BaseCommand):
    help = "Queue (or run inline) optimized media variant generation for known recipe buckets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipe",
            choices=sorted(RECIPES.keys()),
            help="Only sweep a specific recipe (e.g. wipe, background, post_hero, variant, about).",
        )
        parser.add_argument(
            "--run-now",
            action="store_true",
            help="Run conversion jobs synchronously instead of enqueueing RQ jobs.",
        )

    def handle(self, *args, **options):
        recipe_key = options.get("recipe")
        run_now = options.get("run_now", False)
        enqueue_available = not run_now
        keys = [recipe_key] if recipe_key else list(RECIPES.keys())

        q = None
        enqueued = 0
        processed = 0
        failed = 0

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
                if enqueue_available:
                    try:
                        if q is None:
                            q = django_rq.get_queue("default")
                        q.enqueue("hr_core.media_jobs.generate_variants_for_file", key, rel)
                        enqueued += 1
                        continue
                    except Exception as exc:
                        enqueue_available = False
                        self.stdout.write(
                            self.style.WARNING(
                                f"RQ unavailable ({exc}); falling back to inline processing for remaining files."
                            )
                        )

                result = generate_variants_for_file(key, rel)
                processed += 1
                if not result.get("ok", False):
                    failed += 1

            if processed:
                self.stdout.write(self.style.SUCCESS(f"Processed {processed} source files inline ({failed} failures)."))

            if enqueued:
                self.stdout.write(self.style.SUCCESS(f"Enqueued {enqueued} source files."))
                self.stdout.write(WORKER_HINT)
                return

            if not processed:
                self.stdout.write(self.style.SUCCESS("No matching source files found."))

        #         q.enqueue("hr_core.media_jobs.generate_variants_for_file", key, rel)
        #         enqueued += 1
        #
        # self.stdout.write(self.style.SUCCESS(f"Enqueued {enqueued} source files."))
