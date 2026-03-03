# hr_shop/views/manage_helpers.py

"""
Shared helpers for the product manager views.

Layout:
  - Low-level utilities (_to_int, URL builder)
  - Selection resolution
  - Filter value parsing
  - Delete / soft-delete helpers
  - Variant option group builder (for variant form checkboxes)
  - build_panels_context() — single source of truth for all panel rendering
"""

from __future__ import annotations

from urllib.parse import urlencode

from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse

from hr_shop.forms import (
    ProductManagerOptionTypeForm,
    ProductManagerOptionValueForm,
    ProductManagerProductForm,
    ProductManagerVariantForm
)
from hr_shop.models import (
    Product,
    ProductOptionType,
    ProductOptionValue,
    ProductVariant,
    ProductVariantOption
)


# ---------------------------------------------------------------------------
# Low-level utilities
# ---------------------------------------------------------------------------


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _panels_url_pairs(*pairs: tuple[str, str | int]) -> str:
    """Build a URL to the panels endpoint from an ordered sequence of (key, value) pairs."""
    base = reverse("hr_shop:product_manager_panels")
    normalized = [(k, v) for k, v in pairs if v not in (None, "")]
    if not normalized:
        return base
    return f"{base}?{urlencode(normalized, doseq=True)}"


# ---------------------------------------------------------------------------
# Selection resolution
# ---------------------------------------------------------------------------


def _resolve_selection(
    product_id: int | None,
    variant_id: int | None,
    option_type_id: int | None,
    option_value_id: int | None
) -> dict:
    """
    Resolve a selection across the model graph.

    Validation rules:
    - Variant must belong to selected product (or derives product when product_id absent).
    - OptionType must belong to selected product (or derives product when absent).
    - OptionValue must belong to selected option_type.
    - If both variant and option_value are present, option_value must be part of that variant.
    """
    selected_product: Product | None = None
    selected_variant: ProductVariant | None = None
    selected_option_type: ProductOptionType | None = None
    selected_option_value: ProductOptionValue | None = None

    if product_id:
        selected_product = Product.objects.filter(pk=product_id).first()

    if variant_id:
        v_qs = ProductVariant.objects.filter(pk=variant_id).select_related("product")
        if selected_product:
            v_qs = v_qs.filter(product=selected_product)
        selected_variant = v_qs.first()
        if selected_variant and not selected_product:
            selected_product = selected_variant.product

    if option_type_id:
        ot_qs = ProductOptionType.objects.filter(pk=option_type_id).select_related("product")
        if selected_product:
            ot_qs = ot_qs.filter(product=selected_product)
        selected_option_type = ot_qs.first()
        if selected_option_type and not selected_product:
            selected_product = selected_option_type.product

    if option_value_id and selected_option_type:
        selected_option_value = ProductOptionValue.objects.filter(
            pk=option_value_id, option_type=selected_option_type
        ).first()

    if selected_variant and selected_option_value:
        if not ProductVariantOption.objects.filter(
            variant=selected_variant, option_value=selected_option_value
        ).exists():
            selected_option_value = None

    return {
        "product": selected_product,
        "variant": selected_variant,
        "option_type": selected_option_type,
        "option_value": selected_option_value
    }


def _resolve_selection_from_get(request: HttpRequest) -> dict:
    return _resolve_selection(
        _to_int(request.GET.get("product")),
        _to_int(request.GET.get("variant")),
        _to_int(request.GET.get("option_type")),
        _to_int(request.GET.get("option_value"))
    )


# ---------------------------------------------------------------------------
# Filter value parsing
# ---------------------------------------------------------------------------


def _parse_filter_value_ids(source, selected_product: Product | None) -> list[int]:
    """
    Parse fv[] from a GET or POST QueryDict and validate against the selected product.
    Returns a deduplicated, ordered list of valid option value IDs.
    """
    raw_values = source.getlist("fv")
    valid_ids = [v for v in (_to_int(r) for r in raw_values) if v]
    if not selected_product or not valid_ids:
        return []
    allowed = set(
        ProductOptionValue.objects
        .filter(option_type__product=selected_product)
        .values_list("id", flat=True)
    )
    seen: set[int] = set()
    result: list[int] = []
    for vid in valid_ids:
        if vid in allowed and vid not in seen:
            result.append(vid)
            seen.add(vid)
    return result


def _filter_variant_queryset(variants_qs, filter_value_ids: list[int]):
    qs = variants_qs
    for vid in filter_value_ids:
        qs = qs.filter(option_values__id=vid)
    return qs.distinct()


# ---------------------------------------------------------------------------
# Delete / soft-delete helpers
# ---------------------------------------------------------------------------


def _related_exists_for_soft_delete(obj) -> bool:
    if isinstance(obj, Product):
        return (
            ProductVariant.objects.filter(product=obj)
            .filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False))
            .exists()
        )
    if isinstance(obj, ProductVariant):
        return (
            ProductVariant.objects.filter(pk=obj.pk)
            .filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False))
            .exists()
        )
    if isinstance(obj, ProductOptionType):
        return ProductOptionValue.objects.filter(
            option_type=obj, variant_options__isnull=False
        ).exists()
    if isinstance(obj, ProductOptionValue):
        return obj.variant_options.exists()
    return False


def _cascade_labels(obj) -> list[str]:
    if isinstance(obj, Product):
        labels = [
            f"Variant: {n}"
            for n in obj.variants.order_by("name").values_list("name", flat=True)
        ]
        labels += [
            f"Option Type: {n}"
            for n in obj.option_types.order_by("position", "name").values_list("name", flat=True)
        ]
        return labels
    if isinstance(obj, ProductOptionType):
        return [
            f"Option Value: {n}"
            for n in obj.values.order_by("position", "name").values_list("name", flat=True)
        ]
    return []


def _set_inactive(obj) -> None:
    obj.active = False
    obj.save(update_fields=["active"])
    if isinstance(obj, (ProductOptionValue, ProductVariant)):
        return
    if isinstance(obj, ProductOptionType):
        obj.values.update(active=False)
        return
    if isinstance(obj, Product):
        obj.variants.update(active=False)
        obj.option_types.update(active=False)
        ProductOptionValue.objects.filter(option_type__product=obj).update(active=False)


def _object_for_delete(kind: str, object_id: int | None):
    mapping = {
        "product": Product,
        "variant": ProductVariant,
        "option_type": ProductOptionType,
        "option_value": ProductOptionValue
    }
    model = mapping.get(kind)
    if model is None or object_id is None:
        return None
    return get_object_or_404(model, pk=object_id)


# ---------------------------------------------------------------------------
# Variant option groups (for variant form checkboxes)
# ---------------------------------------------------------------------------


def _grouped_variant_option_values(
    variant_form, selected_product: Product | None, include_disabled: bool
) -> list[dict]:
    """
    Build grouped option value rows for the variant form checkbox grid.

    Pre-selection priority:
      1. If the form was submitted with errors (is_bound) — use POST data.
      2. If the form has a saved instance with a PK — read M2M directly from DB.
         (Django ModelForm does NOT populate form.initial with M2M values for
          existing instances; they live on form.instance.option_values.)
      3. New form — check form.initial as a last resort.
    """
    if not variant_form or not selected_product:
        return []

    if variant_form.is_bound:
        # Failed POST — reflect what the user actually submitted
        raw_list = variant_form.data.getlist("option_values")
        selected_ids: set[int] = {v for r in raw_list if (v := _to_int(r))}
    elif (
        hasattr(variant_form, "instance")
        and variant_form.instance
        and variant_form.instance.pk
    ):
        # Existing saved variant — pull M2M from the database
        selected_ids = set(
            variant_form.instance.option_values.values_list("id", flat=True)
        )
    else:
        # New form — fall back to initial dict
        raw_initial = variant_form.initial.get("option_values", [])
        selected_ids = {v for r in (list(raw_initial) if raw_initial else []) if (v := _to_int(r))}

    groups = []
    for opt_type in selected_product.option_types.order_by("position", "id"):
        values_qs = opt_type.values.order_by("position", "id")
        if not include_disabled:
            values_qs = values_qs.filter(active=True)
        row = [
            {"id": v.id, "name": v.name,"active": v.active, "checked": v.id in selected_ids}
            for v in values_qs
        ]

        if row:
            groups.append({"type": opt_type, "values": row})
    return groups


# ---------------------------------------------------------------------------
# Main context builder
# ---------------------------------------------------------------------------


def build_panels_context(
    selection: dict,
    filter_value_ids: list[int],
    include_disabled: bool,
    panel: str,
    mode: str,
    bound_form=None
) -> dict:
    """
    Build the complete context dict for rendering both left and right panels.

    Args:
        selection:         Resolved product/variant/option_type/option_value objects.
        filter_value_ids:  Validated fv[] param values.
        include_disabled:  Whether to show inactive records.
        panel:             Which right-panel to show ('browser','variant','product', etc.).
        mode:              Extra mode hint ('new_variant', 'confirm_delete_product', etc.).
        bound_form:        A failed form submission to re-display with validation errors.

    Filter pill → variant navigation contract:
        Pill URLs never carry a variant ID when panel == 'variant'. This lets the
        server auto-resolve the variant from the resulting filter combination:
          - exactly 1 match  → open that variant's detail form
          - 0 or 2+ matches  → fall back to the browser showing filtered results
    """
    selected_product: Product | None = selection["product"]
    selected_variant: ProductVariant | None = selection["variant"]
    selected_option_type: ProductOptionType | None = selection["option_type"]
    selected_option_value: ProductOptionValue | None = selection["option_value"]

    products = Product.objects.order_by("name")

    # --- product-scoped data ---
    option_types = ProductOptionType.objects.none()
    variants = ProductVariant.objects.none()
    filtered_variants = ProductVariant.objects.none()
    selected_filter_by_type: dict[int, int] = {}  # option_type_id -> option_value_id
    option_filter_rows: list[dict] = []
    has_drives_image_option_type = False
    display_variant = None

    if selected_product:
        option_types = (
            selected_product.option_types
            .prefetch_related("values")
            .order_by("position", "name")
        )
        has_drives_image_option_type = option_types.filter(drives_image=True, active=True).exists()
        display_variant = selected_product.display_variant

        filter_value_objects = (
            ProductOptionValue.objects
            .filter(id__in=filter_value_ids, option_type__product=selected_product)
            .select_related("option_type")
        )
        selected_filter_by_type = {v.option_type_id: v.id for v in filter_value_objects}

        variants = (
            selected_product.variants
            .select_related("image", "product", "product__image")
            .prefetch_related("option_values__option_type")
            .order_by("name")
        )
        filtered_variants = _filter_variant_queryset(
            variants, list(selected_filter_by_type.values())
        )

        # --- Auto-resolve variant ---
        # Case 1: filters uniquely identify a variant and no explicit variant is set
        if selected_filter_by_type and (
            not selected_variant or selected_variant.product_id != selected_product.id
        ):
            if filtered_variants.count() == 1:
                selected_variant = filtered_variants.first()

        # Case 2: panel=variant was requested without an explicit variant ID
        #         (happens when a filter pill is clicked from inside the variant form).
        #         Resolve from filters if they produce exactly one match; otherwise
        #         leave selected_variant as None so the right panel falls back to browser.
        if panel == "variant" and not selected_variant and selected_product:
            if filtered_variants.count() == 1:
                selected_variant = filtered_variants.first()

        # Collect this variant's option value IDs so the left panel can visually
        # reflect them independently of the active fv filters.
        variant_value_ids: set[int] = set()
        if selected_variant:
            variant_value_ids = set(
                selected_variant.option_values.values_list("id", flat=True)
            )

        # --- Option filter rows (left panel) ---
        for option_type in option_types:
            active_filter_value_id = selected_filter_by_type.get(option_type.id)
            values_qs = option_type.values.order_by("position", "name")
            if not include_disabled:
                values_qs = values_qs.filter(active=True)

            row_values = []
            for value in values_qs:
                # Compute what the fv selection would look like after clicking this pill
                next_filter = dict(selected_filter_by_type)
                if active_filter_value_id == value.id:
                    next_filter.pop(option_type.id, None)   # toggle off
                else:
                    next_filter[option_type.id] = value.id  # toggle on

                pill_pairs: list[tuple] = [
                    ("product", selected_product.id),
                    ("include_disabled", int(include_disabled))
                ]

                # Signal the server that the user prefers variant mode so it can
                # auto-resolve if the new filter combo produces exactly one match.
                # Deliberately do NOT carry the current variant ID — that would pin
                # the variant and prevent navigation to a different one.
                if panel == "variant":
                    pill_pairs.append(("panel", "variant"))
                for fv_id in next_filter.values():
                    pill_pairs.append(("fv", fv_id))

                row_values.append({
                    "id": value.id,
                    "name": value.name,
                    "is_active_filter": active_filter_value_id == value.id,
                    "is_variant_value": value.id in variant_value_ids,
                    "disabled": not value.active,
                    "url": _panels_url_pairs(*pill_pairs)
                })

            # Clear-this-type URL (same no-variant-ID contract)
            clear_pairs: list[tuple] = [
                ("product", selected_product.id),
                ("include_disabled", int(include_disabled))
            ]
            if panel == "variant":
                clear_pairs.append(("panel", "variant"))
            for ot_id, ov_id in selected_filter_by_type.items():
                if ot_id != option_type.id:
                    clear_pairs.append(("fv", ov_id))

            # Manage (edit) URL for this option type — always navigates away from variant
            manage_pairs: list[tuple] = [
                ("product", selected_product.id),
                ("panel", "option_type"),
                ("option_type", option_type.id),
                ("include_disabled", int(include_disabled))
            ]
            for fv_id in selected_filter_by_type.values():
                manage_pairs.append(("fv", fv_id))

            option_filter_rows.append({
                "option_type": option_type,
                "active_value_id": active_filter_value_id,
                "values": row_values,
                "clear_url": _panels_url_pairs(*clear_pairs),
                "manage_url": _panels_url_pairs(*manage_pairs)
            })

    # --- Variant tiles (right panel browser) ---
    variant_tiles: list[dict] = []
    grouped_variant_tiles: dict[str, list] = {}

    if selected_product:
        drives_types = list(option_types.filter(drives_image=True, active=True).order_by("id"))
        primary_type = drives_types[0] if drives_types else None
        secondary_candidates = [
            ot for ot in option_types
            if not primary_type or ot.id != primary_type.id
        ]
        secondary_type = (
            sorted(secondary_candidates, key=lambda ot: ot.id)[0]
            if secondary_candidates else None
        )

        def _sort_key(v: ProductVariant) -> tuple:
            opt_map = {ov.option_type_id: ov.name for ov in v.option_values.all()}
            return (
                opt_map.get(primary_type.id, "") if primary_type else "",
                opt_map.get(secondary_type.id, "") if secondary_type else "",
                v.name.lower(),
                v.id,
            )

        for variant in sorted(list(filtered_variants), key=_sort_key):
            opt_map = {ov.option_type_id: ov.name for ov in variant.option_values.all()}
            option_labels = ", ".join(
                variant.option_values
                .order_by("option_type__position", "position")
                .values_list("name", flat=True)
            )
            tile_pairs: list[tuple] = [
                ("product", selected_product.id),
                ("panel", "variant"),
                ("variant", variant.id),
                ("include_disabled", int(include_disabled)),
            ]
            for fv_id in selected_filter_by_type.values():
                tile_pairs.append(("fv", fv_id))

            group_label = opt_map.get(primary_type.id, "") if primary_type else ""
            variant_tiles.append({
                "variant": variant,
                "label": option_labels,
                "group_label": group_label,
                "is_selected": bool(selected_variant and selected_variant.id == variant.id),
                "url": _panels_url_pairs(*tile_pairs),
            })

        for tile in variant_tiles:
            key = tile["group_label"] or "All"
            grouped_variant_tiles.setdefault(key, []).append(tile)

    # --- Panel state + form selection ---
    panel_state = panel or ""

    product_form = None
    variant_form = None
    option_type_form = None
    option_value_form = None

    if isinstance(bound_form, ProductManagerProductForm):
        product_form = bound_form
        panel_state = "product"
    elif isinstance(bound_form, ProductManagerVariantForm):
        variant_form = bound_form
        panel_state = "variant"
    elif isinstance(bound_form, ProductManagerOptionTypeForm):
        option_type_form = bound_form
        panel_state = "option_type"
    elif isinstance(bound_form, ProductManagerOptionValueForm):
        option_value_form = bound_form
        panel_state = "option_value"
    else:
        if panel_state == "product" or mode in ("new_product", "edit_product"):
            panel_state = "product"
            if selected_product and mode != "new_product":
                product_form = ProductManagerProductForm(instance=selected_product)
            else:
                product_form = ProductManagerProductForm()

        elif panel_state == "variant" or mode == "new_variant":
            panel_state = "variant"
            if selected_variant and selected_product and mode != "new_variant":
                variant_form = ProductManagerVariantForm(
                    instance=selected_variant, product=selected_product
                )
            elif selected_product:
                variant_form = ProductManagerVariantForm(product=selected_product)

        elif panel_state == "option_type" or mode == "new_option_type":
            panel_state = "option_type"
            if selected_option_type and selected_product and mode != "new_option_type":
                option_type_form = ProductManagerOptionTypeForm(
                    instance=selected_option_type, product=selected_product
                )
            elif selected_product:
                option_type_form = ProductManagerOptionTypeForm(product=selected_product)

        elif panel_state == "option_value" or mode == "new_option_value":
            panel_state = "option_value"
            if selected_option_value and mode != "new_option_value":
                option_value_form = ProductManagerOptionValueForm(instance=selected_option_value)
            else:
                option_value_form = ProductManagerOptionValueForm()

    # Delete plan
    delete_plan = None
    if mode and mode.startswith("confirm_delete_"):
        panel_state = "delete"
        delete_kind = mode.replace("confirm_delete_", "")
        obj_map = {
            "product": selected_product,
            "variant": selected_variant,
            "option_type": selected_option_type,
            "option_value": selected_option_value
        }
        obj = obj_map.get(delete_kind)
        if obj is not None:
            delete_plan = {
                "kind": delete_kind,
                "id": obj.id,
                "label": str(obj),
                "soft_delete": _related_exists_for_soft_delete(obj),
                "cascades": _cascade_labels(obj)
            }

    variant_option_groups = _grouped_variant_option_values(
        variant_form, selected_product, include_disabled
    )

    # Normalise final panel_state.
    # Specifically: panel=variant was requested but we couldn't resolve a unique
    # variant from filters (0 or 2+ matches) — fall back to browser.
    if not selected_product:
        panel_state = "empty"
    elif panel_state == "variant" and not variant_form:
        panel_state = "browser"
    elif panel_state not in ("delete", "option_value", "option_type", "variant", "product"):
        panel_state = "browser"

    # --- URL helpers for templates ---
    active_fv_pairs = [("fv", v) for v in selected_filter_by_type.values()]

    clear_all_filter_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("include_disabled", int(include_disabled)),
        )
        if selected_product else ""
    )

    edit_product_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "product"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs,
        )
        if selected_product else ""
    )

    new_variant_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "variant"),
            ("mode", "new_variant"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs,
        )
        if selected_product else ""
    )

    new_option_type_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "option_type"),
            ("mode", "new_option_type"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs,
        )
        if selected_product else ""
    )

    toggle_disabled_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", panel_state),
            ("include_disabled", int(not include_disabled)),
            *(
                [("variant", selected_variant.id)]
                if selected_variant and panel_state == "variant"
                else []
            ),
            *active_fv_pairs,
        )
        if selected_product else ""
    )

    delete_product_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("mode", "confirm_delete_product"),
            ("include_disabled", int(include_disabled))
        )
        if selected_product else ""
    )

    new_option_value_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "option_value"),
            ("mode", "new_option_value"),
            ("option_type", selected_option_type.id),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product and selected_option_type else ""
    )

    delete_variant_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("variant", selected_variant.id),
            ("mode", "confirm_delete_variant"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product and selected_variant else ""
    )

    delete_option_type_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("option_type", selected_option_type.id),
            ("mode", "confirm_delete_option_type"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product and selected_option_type else ""
    )

    return {
        # Products list
        "products": products,
        # Product-scoped data
        "variants": variants,
        "filtered_variants": filtered_variants,
        "option_types": option_types,
        # Selection
        "selected_product": selected_product,
        "selected_variant": selected_variant,
        "selected_option_type": selected_option_type,
        "selected_option_value": selected_option_value,
        # Filter state
        "selected_filter_value_ids": list(selected_filter_by_type.values()),
        "option_filter_rows": option_filter_rows,
        # Right panel display data
        "variant_tiles": variant_tiles,
        "grouped_variant_tiles": grouped_variant_tiles,
        "variant_option_groups": variant_option_groups,
        "has_drives_image_option_type": has_drives_image_option_type,
        "display_variant": display_variant,
        "include_disabled": include_disabled,
        # Forms
        "product_form": product_form,
        "variant_form": variant_form,
        "option_type_form": option_type_form,
        "option_value_form": option_value_form,
        # Panel routing
        "panel_state": panel_state,
        "mode": mode,
        "delete_plan": delete_plan,
        # URL helpers
        "clear_all_filter_url": clear_all_filter_url,
        "edit_product_url": edit_product_url,
        "new_variant_url": new_variant_url,
        "new_option_type_url": new_option_type_url,
        "toggle_disabled_url": toggle_disabled_url,
        "delete_product_url": delete_product_url,
        "new_option_value_url": new_option_value_url,
        "delete_variant_url": delete_variant_url,
        "delete_option_type_url": delete_option_type_url
    }
