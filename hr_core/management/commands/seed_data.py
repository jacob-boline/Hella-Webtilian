# hr_core/management/commands/seed_data.py

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
