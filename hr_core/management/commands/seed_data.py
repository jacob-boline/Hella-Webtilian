# hr_core/management/commands/seed_data.py
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Seed all app data (hr_shop, hr_about, hr_live, hr_bulletin) "
        "from seed_data/hr_<app_name>/ and non-model media assets."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--shop",
            action="store_true",
            help="Seed only hr_shop data.",
        )
        parser.add_argument(
            "--about",
            action="store_true",
            help="Seed only hr_about data.",
        )
        parser.add_argument(
            "--live",
            action="store_true",
            help="Seed only hr_live data.",
        )
        parser.add_argument(
            "--bulletin",
            action="store_true",
            help="Seed only hr_bulletin data.",
        )
        parser.add_argument(
            "--media",
            action="store_true",
            help="Seed only non-model media assets (backgrounds, wipes).",
        )

    def handle(self, *args, **options):
        only_shop = options["shop"]
        only_about = options["about"]
        only_live = options["live"]
        only_bulletin = options["bulletin"]
        only_media = options["media"]

        # If no flags supplied → seed everything
        if not (only_shop or only_about or only_live or only_bulletin or only_media):
            only_shop = only_about = only_live = only_bulletin = only_media = True

        if only_shop:
            self.stdout.write("→ Seeding hr_shop…")
            call_command("seed_hr_shop")

        if only_about:
            self.stdout.write("→ Seeding hr_about…")
            call_command("seed_hr_about")

        if only_live:
            self.stdout.write("→ Seeding hr_live…")
            call_command("seed_hr_live")

        if only_bulletin:
            self.stdout.write("→ Seeding hr_bulletin…")
            call_command("seed_hr_bulletin")

        if only_media:
            self.stdout.write("→ Seeding media assets…")
            call_command("seed_media_assets")

        self.stdout.write(self.style.SUCCESS("✅ All requested seeders completed."))


def attach_image_if_missing(instance, field_name: str, image_key: str, opened_file) -> bool:
    """
    instance: model instance (e.g. Post)
    field_name: str name of ImageField on instance (e.g. "hero")
    key: relative path from MEDIA_ROOT
    opened_file: file-like object (already open in rb mode)

    Returns True if it wrote/saved a new file, else False.
    """
    ff = getattr(instance, field_name)

    k = (image_key or "").strip().replace("\\", "/").lstrip("/")
    if k.startswith("media/"):
        k = k.removeprefix("media/")

    basename = Path(k).name  # "foo.webp"

    upload_to = (ff.field.upload_to or "").strip("/")

    expected_rel = f"{upload_to}/{basename}" if upload_to else basename  # "posts/hero/foo.webp"

    # Point to existing image file if found
    local_path = Path(settings.MEDIA_ROOT) / expected_rel
    if local_path.exists():
        if ff.name != expected_rel:
            ff.name = expected_rel
            if getattr(instance, 'pk', None):
                instance.save(update_fields=[field_name])
            else:
                instance.save()
        return False

    # Otherwise save
    ff.save(basename, File(opened_file), save=True)
    return True
