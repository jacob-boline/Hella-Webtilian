# hr_core/management/commands/seed_media_assets.py

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Authoritative media seeding. Deletes and recreates seeded static media folders."

    def handle(self, *args, **options):
        seed_base = Path(settings.BASE_DIR) / "_seed_data" / "media"
        if not seed_base.exists():
            self.stdout.write(self.style.WARNING(f"No _seed_data/media directory at {seed_base}"))
            return

        static_root = Path(settings.REPO_STATIC_ROOT) / "hr_core" / "images"

        for rel_dir in ("backgrounds", "wipes"):
            src_dir = seed_base / rel_dir
            dest_dir = static_root / rel_dir

            if not src_dir.exists():
                self.stdout.write(self.style.WARNING(f"Missing seed folder: {src_dir} (skip)"))
                continue

            if dest_dir.exists():
                shutil.rmtree(dest_dir)
                self.stdout.write(f"Deleted {dest_dir}")

            dest_dir.mkdir(parents=True, exist_ok=True)

            for src_file in sorted(src_dir.iterdir()):
                if src_file.is_file() and not src_file.name.startswith("."):
                    shutil.copyfile(src_file, dest_dir / src_file.name)

            self.stdout.write(self.style.SUCCESS(f"Seeded {rel_dir}"))

        self.stdout.write(self.style.SUCCESS("Media seeding complete."))
