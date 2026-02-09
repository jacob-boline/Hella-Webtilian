# hr_core/management/commands/regen_media_variants.py

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from hr_about.models import CarouselSlide
from hr_bulletin.models import Post
from hr_core.media_jobs import generate_variants_for_file
from hr_shop.models import ProductImage


class Command(BaseCommand):
    help = "Regenerate media variants for uploaded media in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipe",
            choices=["post_hero", "variant", "about"],
            help="Only regenerate a specific recipe (post_hero, variant, about).",
        )
        parser.add_argument("--limit", type=int, help="Limit number of records processed per recipe.")
        parser.add_argument("--since", type=int, help="Only include records updated/created in the last N days.")

    def handle(self, *args, **options):
        recipe_key = options.get("recipe")
        limit = options.get("limit")
        since_days = options.get("since")

        mapping = {
            "post_hero": (Post, "hero", "updated_at"),
            "variant": (ProductImage, "image", "created_at"),
            "about": (CarouselSlide, "image", "updated_at"),
        }

        keys = [recipe_key] if recipe_key else list(mapping.keys())
        total = 0
        failed = 0

        for key in keys:
            model, field, timestamp_field = mapping[key]
            qs = model.objects.all()

            if since_days is not None:
                cutoff = timezone.now() - timedelta(days=since_days)
                qs = qs.filter(**{f"{timestamp_field}__gte": cutoff})

            qs = qs.exclude(**{f"{field}__isnull": True}).exclude(**{field: ""})

            if limit:
                qs = qs[:limit]

            for instance in qs:
                file_field = getattr(instance, field)
                if not file_field:
                    continue

                result = generate_variants_for_file(key, file_field.name)
                total += 1
                if not result.get("ok"):
                    failed += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {total} records with {failed} failures."))
