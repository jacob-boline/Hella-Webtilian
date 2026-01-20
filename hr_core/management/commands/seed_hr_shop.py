# hr_core/management/commands/seed_hr_shop.py

from decimal import Decimal
from pathlib import Path
import itertools

import yaml
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from hr_shop.models import (
    Product,
    ProductOptionType,
    ProductOptionValue,
    ProductVariant,
    InventoryItem,
    ProductImage,   # <-- NEW
)


class Command(BaseCommand):
    help = "Seed hr_shop data only."

    def handle(self, *args, **options):
        self._seed_hr_shop()

    # ==============================
    # hr_shop seeding (data-driven)
    # ==============================
    def _seed_hr_shop(self):
        """
        Seed hr_shop using YAML + images under:
            _seed_data/hr_shop/<ProductName>/
        """
        self.stdout.write("  → hr_shop…")

        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_shop"
        if not base.exists():
            self.stdout.write(
                self.style.WARNING(f"    • No seed_data/hr_shop directory found at {base}")
            )
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
            self.stdout.write(
                self.style.WARNING(f"    • Skipping {product_dir.name}: no product.yml")
            )
            return

        cfg = yaml.safe_load(product_yml.read_text()) or {}

        # Product name – YAML wins, else folder name
        product_name = cfg.get("Product") or product_dir.name

        # Basic metadata with sane defaults
        description = cfg.get("description") or f"{product_name} (seeded product)"
        default_price = Decimal(str(cfg.get("default_price", "0.00")))
        active = cfg.get("active", True)

        # Create/update Product
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                "description": description,
                "active": active
            }
        )
        if not created:
            product.description = description
            product.active = active
            product.save(update_fields=["description", "active"])

        self.stdout.write(f"    • Seeding product: {product.name}")

        # Ensure option types/values from option_types config
        option_cfg = cfg.get("option_types", {}) or {}
        type_map, value_map = self._ensure_product_option_types_and_values(
            product, option_cfg
        )

        # Seed variant groups: each subfolder with a variant.yml
        variant_dirs = [d for d in product_dir.iterdir() if d.is_dir()]

        # Keep deterministic SKU indexing across re-runs:
        existing_variants = (
            product.variants.order_by("id")
            .values_list("sku", flat=True)
        )
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

        # If nothing marked display, choose first variant
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
        """
        option_cfg example (from product.yml):

            option_types:
              Size: ["S", "M", "L", "XL"]
              Color: ["Black", "Cream", "Orange"]

        We create ProductOptionType + ProductOptionValue from these.
        """
        type_map = {}   # "Size" -> ProductOptionType
        value_map = {}  # ("Size", "S") -> ProductOptionValue

        # Preserve order as in YAML
        for type_name, values in option_cfg.items():
            type_code = slugify(type_name)  # 'size', 'color'
            pot, _ = ProductOptionType.objects.get_or_create(
                product=product,
                code=type_code,
                defaults={
                    "name": type_name,
                    "active": True,
                },
            )
            type_map[type_name] = pot

            for value_name in values or []:
                value_code = slugify(value_name)  # 's', 'black'
                pov, _ = ProductOptionValue.objects.get_or_create(
                    option_type=pot,
                    code=value_code,
                    defaults={
                        "name": value_name,
                        "active": True,
                    },
                )
                value_map[(type_name, value_name)] = pov

        return type_map, value_map

    # ------------------------------------------------------
    # Variant group seeding (one folder = one image group)
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
        """
        Each folder under the product dir like:

            Divine Hoodie/
              Clouds/
                variant.yml
                Cloud Hoodie.png

        defines a *group* of variants that all share the same image and
        base config, and may fan out across some option types
        (e.g. all Sizes).
        """
        var_yml = vdir / "variant.yml"
        if not var_yml.exists():
            # Not a variant folder, just ignore
            return start_index

        group_cfg = yaml.safe_load(var_yml.read_text()) or {}
        variant_meta = group_cfg.get("Variant", {}) or {}
        options_cfg = group_cfg.get("options", {}) or {}

        group_name = variant_meta.get("name") or vdir.name
        is_group_display = bool(variant_meta.get("is_display_variant", False))
        group_price = Decimal(str(variant_meta.get("price", default_price)))

        share_image_across = variant_meta.get("share_image_across") or []
        share_image_across = list(share_image_across)

        self.stdout.write(f"      • Variant group: {group_name}")

        # Build the expansion spec across option types
        type_order = list(product_option_cfg.keys())

        # Map of type_name -> list of value names to use in this group
        dimension_values: dict[str, list[str]] = {}
        for type_name, all_values in product_option_cfg.items():
            if type_name in options_cfg:
                # Fixed value for this type
                val = options_cfg[type_name]
                dimension_values[type_name] = [val]
            elif type_name in share_image_across:
                # Fan out across all product values for this type
                dimension_values[type_name] = list(all_values or [])
            else:
                # No contribution from this type for this group
                dimension_values[type_name] = []

        active_dims = [
            (t, vals)
            for t, vals in dimension_values.items()
            if vals
        ]

        if not active_dims:
            self.stdout.write(
                self.style.WARNING(
                    f"        (No active option dimensions for group '{group_name}' in {vdir})"
                )
            )
            return start_index

        # Cartesian product of all selected values
        dim_names = [t for t, _ in active_dims]
        dim_values_lists = [vals for _, vals in active_dims]

        # --- Create or reuse a ProductImage for this group's image file ---
        group_image_path = self._find_first_image_file(vdir)
        group_image_obj = None
        if group_image_path:
            group_image_obj = self._get_or_create_product_image(group_image_path)

        created_variants = []

        for combo_values in itertools.product(*dim_values_lists):
            combo = dict(zip(dim_names, combo_values))

            # Build a human-readable variant name in option type order
            ordered_value_names = []
            for tname in type_order:
                vname = combo.get(tname)
                if vname:
                    ordered_value_names.append(vname)
            variant_name = " / ".join(ordered_value_names) if ordered_value_names else group_name

            # Deterministic SKU: <PRODUCT-SLUG>-NNN
            prod_slug = slugify(product.name)
            index = start_index
            start_index += 1
            sku = f"{prod_slug.upper()}-{index:03d}"

            # Create or get the variant
            variant, created = ProductVariant.objects.get_or_create(
                product=product,
                sku=sku,
                defaults={
                    "name":               variant_name,
                    "price":              group_price,
                    "active":             True,
                    "is_display_variant": False
                }
            )
            if not created:
                variant.name = variant_name
                if not variant.price:
                    variant.price = group_price
                variant.save(update_fields=["name", "price"])

            # Attach option values
            if created or not variant.option_values.exists():
                ovs = []
                for tname, vname in combo.items():
                    pov = value_map.get((tname, vname))
                    if not pov:
                        self.stdout.write(
                            self.style.WARNING(
                                f"        (No ProductOptionValue for {tname}={vname} on {product.name})"
                            )
                        )
                        continue
                    ovs.append(pov)
                if ovs:
                    variant.option_values.set(ovs)

            # Ensure inventory
            InventoryItem.objects.get_or_create(
                variant=variant,
                defaults={"on_hand": 25, "reserved": 0}
            )

            # 🔴 IMPORTANT: attach the shared group image to this variant
            if group_image_obj and (created or not variant.image):
                variant.image = group_image_obj
                variant.save(update_fields=["image"])

            created_variants.append(variant)

        # If this group requested display variant and none set yet for the product,
        # we mark the first variant in this group as display.
        if is_group_display and created_variants:
            if not product.variants.filter(is_display_variant=True).exists():
                dv = created_variants[0]
                dv.is_display_variant = True
                dv.save(update_fields=["is_display_variant"])
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"        (Group '{group_name}' requested display variant, "
                        f"but product already has one; ignoring.)"
                    )
                )

        return start_index

    # ------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------

    @staticmethod
    def _find_first_image_file(vdir: Path):
        """Return the first non-YAML file in a variant group folder, or None."""
        for p in vdir.iterdir():
            if p.is_file() and not p.name.lower().endswith((".yml", ".yaml")):
                return p
        return None

    @staticmethod
    def _get_or_create_product_image(img_path: Path) -> ProductImage | None:
        """
        Create (or reuse) a ProductImage for a variant group folder.

        For idempotency, we try to reuse by filename:
          - If a ProductImage already exists whose image name ends with this filename,
            reuse it.
          - Otherwise, create a new ProductImage and save the file.
        """
        filename = img_path.name

        # Try to reuse an existing ProductImage with the same filename
        existing = ProductImage.objects.filter(image__endswith=filename).first()
        if existing:
            return existing

        img = ProductImage(alt_text=filename)
        with img_path.open("rb") as f:
            img.image.save(filename, File(f))

        return img
