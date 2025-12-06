# hr_core/management/commands/initialize.py

import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = (
        "Dangerous dev initializer: wipes selected app migrations, deletes db.sqlite3, "
        "recreates the schema, seeds data, and starts `npm run dev`."
        ""
        "$ python manage.py initialize  (full nuke and rebuild)"
        ""
        "flags (can be combined):"
        ""
        "--no-input (skip confirmation)"
        ""
        "--no-npm   (skips 'npm run dev' which runs the app with livereload)"
        ""
        "--no-seed  (skips seeding/populating the DB)"
    )

    APPS_TO_WIPE = [
        "hr_about",
        "hr_access",
        "hr_bulletin",
        "hr_email",
        "hr_live",
        "hr_shop",
        "hr_payment",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation (DANGEROUS).",
        )
        parser.add_argument(
            "--no-seed",
            action="store_true",
            help="Skip running `seed_data` after migrations.",
        )
        parser.add_argument(
            "--no-npm",
            action="store_true",
            help="Skip starting `npm run dev`.",
        )

    def handle(self, *args, **options):

        if not settings.DEBUG:
            raise RuntimeError('init command cannot run when DEBUG=False')

        no_input = options["no_input"]
        no_seed = options["no_seed"]
        no_npm = options["no_npm"]

        base_dir = Path(settings.BASE_DIR)
        db_path = base_dir / "db.sqlite3"

        # ============================================================
        # ASCII WARNING (skipped only with --no-input)
        # ============================================================
        if not no_input:
            warning = r"""
        ██████████████████████████████████████████████████████████████████████████
        █░░░░░░░░░░░░░░░░░░░░░░  D E V   I N I T I A L I Z E R  ░░░░░░░░░░░░░░░░░█
        █                                                                        █
        █   This command will COMPLETELY DESTROY your current database.          █
        █   It will DELETE db.sqlite3, WIPE migrations, RECREATE schema,         █
        █   RESEED all apps, and optionally LAUNCH the frontend dev server.      █
        █                                                                        █
        █   If you are not fully aware of what this will do, STOP NOW.           █
        █                                                                        █
        █   Type YES to continue, anything else to abort:                        █
        ██████████████████████████████████████████████████████████████████████████
        """
            self.stdout.write(self.style.WARNING(warning))
            confirm = input("> ").strip()
            if confirm != "YES":
                self.stdout.write(self.style.ERROR("Initialization aborted."))
                return

        # Otherwise (if --no-input), skip warning and continue silently.

        # 1) Wipe migrations
        self._wipe_migrations(base_dir)

        # 2) Delete db.sqlite3
        self._delete_db(db_path)

        # 3) makemigrations + migrate
        self._run_migrations()

        # 4) Create superuser from env
        self._create_superuser_from_env()

        # 5) Seed data
        if not no_seed:
            self._run_seed_data()
        else:
            self.stdout.write(self.style.WARNING("Skipping seed_data (per --no-seed)."))

        # 6) Start npm run dev
        # if not no_npm:
        #     self._start_npm_dev(base_dir)
        # else:
        #     self.stdout.write(self.style.WARNING("Skipping `npm run dev` (per --no-npm)."))

        self.stdout.write(self.style.SUCCESS("✅ initialize complete."))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _wipe_migrations(self, base_dir: Path):
        self.stdout.write("→ Wiping migrations…")
        for app in self.APPS_TO_WIPE:
            migrations_dir = base_dir / app / "migrations"
            if not migrations_dir.exists():
                self.stdout.write(
                    self.style.WARNING(f"  • {app}: no migrations/ directory found; skipping.")
                )
                continue

            removed_any = False
            for f in migrations_dir.iterdir():
                if f.is_file() and f.name != "__init__.py":
                    f.unlink()
                    removed_any = True

            if removed_any:
                self.stdout.write(f"  • {app}: migrations cleared (kept __init__.py).")
            else:
                self.stdout.write(f"  • {app}: no migration files to remove.")

    def _delete_db(self, db_path: Path):
        self.stdout.write("→ Deleting db.sqlite3 (if present)…")
        if db_path.exists():
            db_path.unlink()
            self.stdout.write(f"  • Deleted {db_path}")
        else:
            self.stdout.write("  • No db.sqlite3 found; skipping.")

    def _run_migrations(self):
        self.stdout.write("→ Running makemigrations…")
        call_command("makemigrations")
        self.stdout.write("→ Running migrate…")
        call_command("migrate")

    def _create_superuser_from_env(self):
        self.stdout.write("→ Creating superuser from environment variables…")

        username = os.environ.get("DJANGO_SU_USERNAME")
        email = os.environ.get("DJANGO_SU_EMAIL")
        password = os.environ.get("DJANGO_SU_PASSWORD")

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "  • DJANGO_SU_USERNAME and/or DJANGO_SU_PASSWORD not set; "
                    "skipping superuser creation."
                )
            )
            return

        if not email:
            email = ""

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"  • Superuser '{username}' already exists; skipping.")
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"  • Superuser '{username}' created."))

    def _run_seed_data(self):
        self.stdout.write("→ Running seed_data…")
        call_command("seed_data")

    def _start_npm_dev(self, base_dir: Path):
        self.stdout.write("→ Starting `npm run dev`…")

        env = os.environ.copy()

        # Resolve the actual npm executable
        if os.name == "nt":
            npm_exe = shutil.which("npm.cmd") or shutil.which("npm")
        else:
            npm_exe = shutil.which("npm")

        if not npm_exe:
            self.stdout.write(
                self.style.ERROR(
                    "  • Failed to start `npm run dev`: could not resolve `npm`.\n"
                    "    Try running `npm --version` and `Get-Command npm` in this terminal."
                )
            )
            return

        cmd = [npm_exe, "run", "dev"]

        try:
            subprocess.Popen(cmd, cwd=str(base_dir), env=env)
            self.stdout.write(self.style.SUCCESS(f"  • `npm run dev` started using {npm_exe}."))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  • Error starting `npm run dev`: {e}")
            )