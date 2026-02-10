# hr_core/management/commands/seed_hr_shop.py
import itertools
from decimal import Decimal
from pathlib import Path
from typing import cast

import yaml
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db.models.fields.files import ImageFieldFile
from django.utils.text import slugify

from hr_core.management.commands.seed_data import attach_image_if_missing
from hr_shop.models import (
    InventoryItem,
    Product,
    ProductImage,
    ProductOptionType,
    ProductOptionValue,
    ProductVariant
)


class Command(BaseCommand):
    help = "Seed hr_shop data only."

    def handle(self, *args, **options):
        self._seed_hr_shop()

    # ==============================
    # hr_shop seeding (data-driven)
    # ==============================
    def _seed_hr_shop(self):
        self.stdout.write("  → hr_shop…")

        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_shop"
        if not base.exists():
            self.stdout.write(self.style.WARNING(f"    • No _seed_data/hr_shop directory found at {base}"))
            return

        product_dirs = [p for p in base.iterdir() if p.is_dir()]
        if not product_dirs:
            self.stdout.write(self.style.WARNING("    • No product directories found."))
            return

        for product_dir in sorted(product_dirs, key=lambda p: p.name.lower()):
            self._seed_shop_product(product_dir)

        self.stdout.write("    • hr_shop seed data applied.")

    # ------------------------------------------------------
    # Product-level seeding
    # ------------------------------------------------------
    def _seed_shop_product(self, product_dir: Path):
        product_yml = product_dir / "product.yml"
        if not product_yml.exists():
            self.stdout.write(self.style.WARNING(f"    • Skipping {product_dir.name}: no product.yml"))
            return

        cfg = yaml.safe_load(product_yml.read_text()) or {}

        product_name = cfg.get("Product") or product_dir.name
        description = cfg.get("description") or f"{product_name} (seeded product)"
        default_price = Decimal(str(cfg.get("default_price", "0.00")))
        active = cfg.get("active", True)

        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={"description": description, "active": active}
        )
        if not created:
            product.description = description
            product.active = active
            product.save(update_fields=["description", "active"])

        self.stdout.write(f"    • Seeding product: {product.name}")

        option_cfg = cfg.get("option_types", {}) or {}
        _, value_map = self._ensure_product_option_types_and_values(product, option_cfg)

        variant_dirs = [d for d in product_dir.iterdir() if d.is_dir()]

        existing_variants = product.variants.order_by("id").values_list("sku", flat=True)
        next_index = len(existing_variants) + 1

        for vdir in sorted(variant_dirs, key=lambda p: p.name.lower()):
            next_index = self._seed_variant_group_from_folder(
                product=product,
                product_option_cfg=option_cfg,
                vdir=vdir,
                value_map=value_map,
                default_price=default_price,
                start_index=next_index
            )

        if not product.variants.filter(is_display_variant=True).exists():
            first = product.variants.order_by("id").first()
            if first:
                first.is_display_variant = True
                first.save(update_fields=["is_display_variant"])

    # ------------------------------------------------------
    # Product option types & values
    # ------------------------------------------------------
    @staticmethod
    def _ensure_product_option_types_and_values(product, option_cfg):
        type_map = {}
        value_map = {}

        for type_name, values in option_cfg.items():
            type_code = slugify(type_name)
            pot, _ = ProductOptionType.objects.get_or_create(
                product=product,
                code=type_code,
                defaults={"name": type_name, "active": True}
            )
            type_map[type_name] = pot

            for value_name in values or []:
                value_code = slugify(value_name)
                pov, _ = ProductOptionValue.objects.get_or_create(
                    option_type=pot,
                    code=value_code,
                    defaults={"name": value_name, "active": True}
                )
                value_map[(type_name, value_name)] = pov

        return type_map, value_map

    # ------------------------------------------------------
    # Variant group seeding
    # ------------------------------------------------------
    def _seed_variant_group_from_folder(
        self,
        product,
        product_option_cfg,
        vdir: Path,
        value_map,
        default_price: Decimal,
        start_index: int
    ) -> int:
        var_yml = vdir / "variant.yml"
        if not var_yml.exists():
            return start_index

        group_cfg = yaml.safe_load(var_yml.read_text()) or {}
        variant_meta = group_cfg.get("Variant", {}) or {}
        options_cfg = group_cfg.get("options", {}) or {}

        group_name = variant_meta.get("name") or vdir.name
        is_group_display = bool(variant_meta.get("is_display_variant", False))
        group_price = Decimal(str(variant_meta.get("price", default_price)))

        share_image_across = list(variant_meta.get("share_image_across") or [])

        # STRICT: require image_key for shop variants
        image_key = variant_meta.get("image_key")
        if not image_key:
            self.stdout.write(self.style.WARNING(f"      (Variant group '{group_name}' missing required 'image_key' in {var_yml})"))
            image_key = ""

        self.stdout.write(f"      • Variant group: {group_name}")

        type_order = list(product_option_cfg.keys())

        dimension_values: dict[str, list[str]] = {}
        for type_name, all_values in product_option_cfg.items():
            if type_name in options_cfg:
                dimension_values[type_name] = [options_cfg[type_name]]
            elif type_name in share_image_across:
                dimension_values[type_name] = list(all_values or [])
            else:
                dimension_values[type_name] = []

        active_dims = [(t, vals) for t, vals in dimension_values.items() if vals]
        if not active_dims:
            self.stdout.write(self.style.WARNING(f"        (No active option dimensions for group '{group_name}' in {vdir})"))
            return start_index

        dim_names = [t for t, _ in active_dims]
        dim_values_lists = [vals for _, vals in active_dims]

        group_image_obj = None
        if image_key:
            try:
                normalized_key = self._normalize_media_key(str(image_key))
                group_image_obj = self._get_or_create_product_image(normalized_key)
            except FileNotFoundError as e:
                self.stdout.write(self.style.WARNING(f"        ({e})"))

        created_variants = []

        for combo_values in itertools.product(*dim_values_lists):
            combo = dict(zip(dim_names, combo_values, strict=True))

            ordered_value_names = []
            for tname in type_order:
                vname = combo.get(tname)
                if vname:
                    ordered_value_names.append(vname)
            variant_name = " / ".join(ordered_value_names) if ordered_value_names else group_name

            prod_slug = slugify(product.name)
            index = start_index
            start_index += 1
            sku = f"{prod_slug.upper()}-{index:03d}"

            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                sku=sku,
                defaults={
                    "name": variant_name,
                    "price": group_price,
                    "active": True,
                    "is_display_variant": False
                }
            )
            if not created:
                variant.name = variant_name
                if not variant.price:
                    variant.price = group_price
                variant.save(update_fields=["name", "price"])

            if created or not variant.option_values.exists():
                ovs = []
                for tname, vname in combo.items():
                    pov = value_map.get((tname, vname))
                    if not pov:
                        self.stdout.write(self.style.WARNING(f"        (No ProductOptionValue for {tname}={vname} on {product.name})"))
                        continue
                    ovs.append(pov)
                if ovs:
                    variant.option_values.set(ovs)

            InventoryItem.objects.get_or_create(variant=variant, defaults={"on_hand": 25, "reserved": 0})

            if group_image_obj and (created or self._needs_file(variant.image)):
                variant.image = group_image_obj
                variant.save(update_fields=["image"])

            created_variants.append(variant)

        if is_group_display and created_variants:
            if not product.variants.filter(is_display_variant=True).exists():
                dv = created_variants[0]
                dv.is_display_variant = True
                dv.save(update_fields=["is_display_variant"])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"        (Group '{group_name}' requested display variant, but product already has one; ignoring.)"
                    )
                )

        return start_index

    # ------------------------------------------------------
    # Media + ProductImage helpers
    # ------------------------------------------------------
    @staticmethod
    def _needs_file(fieldfile) -> bool:
        if not fieldfile:
            return True

        ff = cast(ImageFieldFile, fieldfile)
        try:
            if not ff.name:
                return True
            return not ff.storage.exists(ff.name)
        except Exception:
            return True

    @staticmethod
    def _normalize_media_key(key: str) -> str:
        k = (key or "").strip().replace("\\", "/").lstrip("/")
        if k.startswith("media/"):
            k = k.removeprefix("media/")
        return k

    def _open_media(self, key: str):
        """
        Try local MEDIA_ROOT first, otherwise storage.
        """
        k = self._normalize_media_key(key)

        local_path = Path(settings.MEDIA_ROOT) / k
        if local_path.exists():
            return local_path.open("rb")

        if default_storage.exists(k):
            return default_storage.open(k, "rb")

        raise FileNotFoundError(f"Media not found (local or storage) for key: {k}")

    def _get_or_create_product_image(self, image_key: str) -> ProductImage | None:
        """
        Create (or reuse) a ProductImage for a variant group, keyed by full storage path.

        Idempotency rules:
          - If a ProductImage exists with image.name == image_key and file exists -> reuse
          - If row exists but file missing -> re-save the file into the same row
          - Else -> create new row and save file
        """

        if not image_key:
            return None

        k = self._normalize_media_key(image_key)

        existing = ProductImage.objects.filter(image=k).first()
        if existing:
            if not self._needs_file(existing.image):
                return existing

            with self._open_media(k) as f:
                attach_image_if_missing(existing, 'image', k, f)
            if not existing.alt_text:
                existing.alt_text = Path(k).name
                existing.save(update_fields=["alt_text"])
            return existing

        img = ProductImage(alt_text=Path(k).name)
        with self._open_media(k) as f:
            attach_image_if_missing(img, 'image', k, f)
        return img
