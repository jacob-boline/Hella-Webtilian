# hr_core/management/commands/seed_hr_about.py

from pathlib import Path

import yaml
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from hr_about.models import CarouselSlide, PullQuote


class Command(BaseCommand):
    help = "Seed hr_about data (carousel slides + pull quotes) from YAML + images."

    def handle(self, *args, **options):
        self._seed_hr_about()

    # ==============================
    # hr_about seeding
    # ==============================
    def _seed_hr_about(self):
        """
        Seed hr_about from:

            seed_data/hr_about/
              carousel.yml
              pullquotes.yml
              carousel_images/
                <image files>
        """
        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_about"
        if not base.exists():
            self.stdout.write(self.style.WARNING(f"  → No seed_data/hr_about directory found at {base}"))
            return

        self.stdout.write("  → hr_about…")

        self._seed_carousel(base)
        self._seed_pullquotes(base)

        self.stdout.write("    • hr_about seed data applied.")

    # ------------------------------------------------------
    # Carousel slides
    # ------------------------------------------------------
    def _seed_carousel(self, base: Path):
        carousel_yml = base / "carousel.yml"
        images_dir = base / "carousel_images"

        if not carousel_yml.exists():
            self.stdout.write(self.style.WARNING("    • No carousel.yml found; skipping CarouselSlide seeding."))
            return

        cfg = yaml.safe_load(carousel_yml.read_text()) or {}
        slides_cfg = cfg.get("slides") or []

        if not slides_cfg:
            self.stdout.write(self.style.WARNING("    • carousel.yml contains no slides; skipping."))
            return

        if not images_dir.exists():
            self.stdout.write(self.style.WARNING(f"    • No carousel_images directory found at {images_dir}; " f"slides will be created without images."))

        self.stdout.write("    • Seeding CarouselSlide entries…")

        for idx, s in enumerate(slides_cfg, start=1):
            title = s.get("title") or f"Slide {idx}"
            caption = s.get("caption") or ""
            order = s.get("order") or idx
            is_active = s.get("is_active", True)
            image_name = s.get("image")

            # Use 'order' as the stable key; update title/caption/active if it already exists.
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

            # Attach image if configured and not already set
            if image_name and images_dir.exists():
                image_path = images_dir / image_name
                if image_path.exists():
                    if not slide.image:
                        with image_path.open("rb") as f:
                            slide.image.save(image_path.name, File(f), save=True)
                else:
                    self.stdout.write(self.style.WARNING(f"      (Image '{image_name}' not found in {images_dir} for slide order {order})"))

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

            # Use 'order' as the stable key here as well
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
