# hr_core/management/commands/init.py

import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command


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
        "hr_common",
        "hr_email",
        "hr_live",
        "hr_payment",
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

        parser.add_argument(
            "--keep-media",
            action="store_true",
            help="Preserve seeded media subfolders under MEDIA_ROOT.",
        )

        parser.add_argument("--wipe-media", action="store_true", help="Force delete seeded media folders even if --no-seed is used.")

    def handle(self, *args, **options):

        if not settings.DEBUG:
            raise RuntimeError("init command cannot run when DEBUG=False")

        no_input = options["no_input"]
        no_seed = options["no_seed"]
        keep_media = options["keep_media"]
        wipe_media = options["wipe_media"]

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

        # 5) Wipe Media
        should_wipe_media = (not keep_media) and ((not no_seed) or wipe_media)
        if should_wipe_media:
            self._wipe_seeded_media()
        else:
            self.stdout.write(self.style.WARNING("→ Skipping media wipe " f"({'--keep-media' if keep_media else '--no-seed'})."))

        # 6) Seed data
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

    def _wipe_seeded_media(self):
        self.stdout.write("→ Wiping seeded media folders…")
        media_root = Path(settings.MEDIA_ROOT)
        to_wipe = [
            media_root / "hr_about",
            media_root / "variants",
            media_root / "posts",
        ]
        for p in to_wipe:
            if p.exists() and p.is_dir():
                shutil.rmtree(p)
                self.stdout.write(f"  • Deleted {p}")
            else:
                self.stdout.write(f"  • Not found: {p}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _wipe_migrations(self, base_dir: Path):
        self.stdout.write("→ Wiping migrations…")
        for app in self.APPS_TO_WIPE:
            migrations_dir = base_dir / app / "migrations"

            # Ensure migrations package exists
            if not migrations_dir.exists():
                migrations_dir.mkdir(parents=True, exist_ok=True)
                self.stdout.write(f"  • {app}: created migrations/ directory.")

            init_py = migrations_dir / "__init__.py"
            if not init_py.exists():
                init_py.write_text("")
                self.stdout.write(f"  • {app}: created migrations/__init__.py.")

            # Remove migration files except __init__.py
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
            self.stdout.write(self.style.WARNING("  • DJANGO_SU_USERNAME and/or DJANGO_SU_PASSWORD not set; " "skipping superuser creation."))
            return

        if not email:
            email = ""

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"  • Superuser '{username}' already exists; skipping."))
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
                self.style.ERROR("  • Failed to start `npm run dev`: could not resolve `npm`.\n" "    Try running `npm --version` and `Get-Command npm` in this terminal.")
            )
            return

        cmd = [npm_exe, "run", "dev"]

        try:
            subprocess.Popen(cmd, cwd=str(base_dir), env=env)
            self.stdout.write(self.style.SUCCESS(f"  • `npm run dev` started using {npm_exe}."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  • Error starting `npm run dev`: {e}"))
