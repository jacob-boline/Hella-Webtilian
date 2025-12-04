# hr_core/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Seed all app data (hr_shop, hr_about, hr_live) from seed_data/hr_<app_name>/."

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

    def handle(self, *args, **options):
        only_shop = options["shop"]
        only_about = options["about"]
        only_live = options["live"]

        # If no flags supplied → seed everything
        if not (only_shop or only_about or only_live):
            only_shop = only_about = only_live = True

        if only_shop:
            self.stdout.write("→ Seeding hr_shop…")
            call_command("seed_hr_shop")

        if only_about:
            self.stdout.write("→ Seeding hr_about…")
            call_command("seed_hr_about")

        if only_live:
            self.stdout.write("→ Seeding hr_live…")
            call_command("seed_hr_live")

        self.stdout.write(self.style.SUCCESS("✅ All requested seeders completed."))
