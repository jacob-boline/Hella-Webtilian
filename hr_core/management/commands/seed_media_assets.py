# hr_core/management/commands/seed_media_assets.py

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed non-model media assets (backgrounds, wipes) from _seed_data/media/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing media files if they already exist.",
        )

    def handle(self, *args, **options):
        seed_base = Path(settings.BASE_DIR) / "_seed_data" / "media"
        if not seed_base.exists():
            self.stdout.write(self.style.WARNING(f"  → No _seed_data/media directory found at {seed_base}"))
            return

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        force = options["force"]

        copied = 0
        skipped = 0

        for rel_dir in ("backgrounds", "wipes"):
            src_dir = seed_base / rel_dir
            dest_dir = media_root / rel_dir

            if not src_dir.exists():
                self.stdout.write(self.style.WARNING(f"  → Missing seed folder: {src_dir} (skip)"))
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)

            for src_file in sorted(src_dir.iterdir()):
                if not src_file.is_file():
                    continue
                if src_file.name.startswith("."):
                    continue

                dest_file = dest_dir / src_file.name
                if dest_file.exists() and not force:
                    skipped += 1
                    continue

                shutil.copy2(src_file, dest_file)
                copied += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded media assets (copied={copied}, skipped={skipped})."))
