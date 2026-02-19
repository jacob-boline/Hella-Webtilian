# hr_core/management/commands/seed_hr_about.py

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db.models.fields.files import ImageFieldFile

from hr_about.models import CarouselSlide, PullQuote
from hr_core.management.commands.seed_data import attach_image_if_missing


class Command(BaseCommand):
    help = "Seed hr_about data (carousel slides + pull quotes) from YAML + media keys."

    def handle(self, *args, **options):
        self._seed_hr_about()

    # ==============================
    # hr_about seeding
    # ==============================
    def _seed_hr_about(self):
        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_about"
        if not base.exists():
            self.stdout.write(self.style.WARNING(f"  → No _seed_data/hr_about directory found at {base}"))
            return

        self.stdout.write("  → hr_about…")

        self._seed_carousel(base)
        self._seed_pullquotes(base)

        self.stdout.write("    • hr_about seed data applied.")

    # ------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------
    @staticmethod
    def _needs_file(fieldfile) -> bool:
        """
        True if the FieldFile is missing or the referenced file is missing from storage.
        """
        if not fieldfile:
            return True

        ff = cast(ImageFieldFile, fieldfile)
        try:
            if not ff.name:
                return True
            return not ff.storage.exists(ff.name)
        except Exception:
            # If storage check fails, treat as missing.
            return True

    @staticmethod
    def _normalize_media_key(key: str) -> str:
        """
        With AWS_PUBLIC_MEDIA_LOCATION='media', default_storage keys are relative
        to that prefix.
        """
        k = (key or "").strip().replace("\\", "/").lstrip("/")
        if k.startswith("media/"):
            k = k.removeprefix("media/")
        return k

    def _open_media(self, key: str):
        """
        Check local MEDIA_ROOT first, otherwise default_storage (e.g. S3).
        Returns an open file-like object or raises FileNotFoundError.
        """
        k = self._normalize_media_key(key)

        local_path = Path(settings.MEDIA_ROOT) / k
        if local_path.exists():
            return local_path.open("rb")

        if default_storage.exists(k):
            return default_storage.open(k, "rb")

        raise FileNotFoundError(f"Media not found (local or storage) for key: {k}")

    def _ensure_slide_image_name(self, slide: CarouselSlide, image_key: str) -> None:
        """
        Keep variant filenames stable (stem-based) by enforcing that the DB points to the
        canonical original name from YAML (e.g. hr_about/amsterdam_2.jpg).

        This does NOT rename any existing objects in storage.
        It only:
          1) normalizes slide.image.name to the canonical key
          2) uploads the canonical object if it's missing
        """
        k = self._normalize_media_key(image_key)  # e.g. "hr_about/amsterdam_2.jpg"
        basename = Path(k).name                   # e.g. "amsterdam_2.jpg"
        expected_rel = slide.image.field.generate_filename(slide, basename).lstrip("/")

        # 1) Always correct the DB reference (even if current name exists)
        if slide.image.name != expected_rel:
            slide.image.name = expected_rel
            slide.save(update_fields=["image"])

        # 2) Ensure the canonical object exists in storage; upload if missing
        if not default_storage.exists(expected_rel):
            with self._open_media(k) as f:
                # Pass expected_rel as the "image_key" so attach_image_if_missing targets the canonical key.
                attach_image_if_missing(slide, "image", expected_rel, f)

    # ------------------------------------------------------
    # Carousel slides
    # ------------------------------------------------------
    def _seed_carousel(self, base: Path):
        carousel_yml = base / "carousel.yml"

        if not carousel_yml.exists():
            self.stdout.write(self.style.WARNING("    • No carousel.yml found; skipping CarouselSlide seeding."))
            return

        cfg = yaml.safe_load(carousel_yml.read_text()) or {}
        slides_cfg = cfg.get("slides") or []

        if not slides_cfg:
            self.stdout.write(self.style.WARNING("    • carousel.yml contains no slides; skipping."))
            return

        self.stdout.write("    • Seeding CarouselSlide entries…")

        for idx, s in enumerate(slides_cfg, start=1):
            title = s.get("title") or f"Slide {idx}"
            caption = s.get("caption") or ""
            order = s.get("order") or idx
            is_active = s.get("is_active", True)

            image_key = s.get("image_key")
            if not image_key:
                self.stdout.write(self.style.WARNING(
                    f"      (Slide order {order} missing required 'image_key'; skipping image.)"
                ))
                image_key = ""

            slide, created = CarouselSlide.objects.get_or_create(
                order=order,
                defaults={
                    "title": title,
                    "caption": caption,
                    "is_active": is_active,
                },
            )
            if not created:
                slide.title = title
                slide.caption = caption
                slide.is_active = is_active
                slide.save(update_fields=["title", "caption", "is_active"])

            # Enforce canonical image key in DB so responsive URL stems match existing S3 variants
            if image_key:
                try:
                    self._ensure_slide_image_name(slide, str(image_key))
                except FileNotFoundError as e:
                    self.stdout.write(self.style.WARNING(f"      ({e} for slide order {order})"))

    # ------------------------------------------------------
    # Pull quotes
    # ------------------------------------------------------
    def _seed_pullquotes(self, base: Path):
        pullquotes_yml = base / "pullquotes.yml"
        if not pullquotes_yml.exists():
            self.stdout.write(self.style.WARNING("    • No pullquotes.yml found; skipping PullQuote seeding."))
            return

        cfg = yaml.safe_load(pullquotes_yml.read_text()) or {}
        quotes_cfg = cfg.get("quotes") or []

        if not quotes_cfg:
            self.stdout.write(self.style.WARNING("    • pullquotes.yml contains no quotes; skipping."))
            return

        self.stdout.write("    • Seeding PullQuote entries…")

        for idx, q in enumerate(quotes_cfg, start=1):
            text = q.get("text") or ""
            if not text:
                self.stdout.write(self.style.WARNING(f"      (Skipping quote #{idx}: missing text.)"))
                continue

            attribution = q.get("attribution") or ""
            order = q.get("order") or idx
            is_active = q.get("is_active", True)

            quote, created = PullQuote.objects.get_or_create(
                order=order,
                defaults={
                    "text": text,
                    "attribution": attribution,
                    "is_active": is_active,
                },
            )
            if not created:
                quote.text = text
                quote.attribution = attribution
                quote.is_active = is_active
                quote.save(update_fields=["text", "attribution", "is_active"])
