# hr_core/management/commands/seed_data.py
from pathlib import Path

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

def _set_field_and_save(instance, field_name: str, field_file, name: str) -> None:
    if field_file.name == name:
        return

    field_file.name = name
    if getattr(instance, "pk", None):
        instance.save(update_fields=[field_name])
    else:
        instance.save()


def attach_image_if_missing(instance, field_name: str, image_key: str, opened_file) -> bool:
    ff = getattr(instance, field_name)

    k = (image_key or "").strip().replace("\\", "/").lstrip("/")
    if k.startswith("media/"):
        k = k.removeprefix("media/")

    basename = Path(k).name
    expected_rel = ff.field.generate_filename(instance, basename).lstrip("/")

    try:
        if ff.storage.exists(expected_rel):
            _set_field_and_save(instance, field_name, ff, expected_rel)
            return False
    except Exception as exc:
        raise RuntimeError(f"Storage exists() failed for {expected_rel}") from exc

    try:
        opened_file.seek(0)
    except Exception:
        pass

    _save = getattr(ff.storage, "_save", None)
    if not _save:
        raise RuntimeError("Storage backend does not support _save(); cannot guarantee deterministic names.")

    saved_name = _save(expected_rel, File(opened_file))

    if saved_name != expected_rel:
        raise RuntimeError(
            f"Storage wrote unexpected key: {saved_name} (expected {expected_rel}). "
            "Refusing to create suffixed duplicates."
        )

    _set_field_and_save(instance, field_name, ff, expected_rel)
    return True
