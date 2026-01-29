# hr_core/management/commands/seed_data.py

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed all app data (hr_shop, hr_about, hr_live, hr_bulletin) " "from seed_data/hr_<app_name>/."

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

    def handle(self, *args, **options):
        only_shop = options["shop"]
        only_about = options["about"]
        only_live = options["live"]
        only_bulletin = options["bulletin"]

        # If no flags supplied → seed everything
        if not (only_shop or only_about or only_live or only_bulletin):
            only_shop = only_about = only_live = only_bulletin = True

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

        self.stdout.write(self.style.SUCCESS("✅ All requested seeders completed."))
