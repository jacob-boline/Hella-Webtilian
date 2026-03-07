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

from dataclasses import dataclass, replace
from typing import Any, cast, TypeVar
from urllib.parse import urlencode

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse

from hr_shop.forms import ProductManagerOptionTypeForm, ProductManagerOptionValueForm, ProductManagerProductForm, ProductManagerVariantForm
from hr_shop.models import Product, ProductOptionType, ProductOptionValue, ProductVariant, ProductVariantOption


@dataclass(frozen=True, slots=True)
class SelectionIds:
    product_id: int | None = None
    variant_id: int | None = None
    option_type_id: int | None = None
    option_value_id: int | None = None


@dataclass(frozen=True, slots=True)
class SelectionResolved:
    ids: SelectionIds
    product: Product | None = None
    variant: ProductVariant | None = None
    option_type: ProductOptionType | None = None
    option_value: ProductOptionValue | None = None

    def to_dict(self) -> dict:
        return {
            "product":      self.product,
            "variant":      self.variant,
            "option_type":  self.option_type,
            "option_value": self.option_value
        }


@dataclass(slots=True)
class _ProductScope:
    option_types: Any
    variants: Any
    filtered_variants: Any
    selected_filter_by_type: dict[int, int]
    option_filter_rows: list[dict]
    has_drives_image_option_type: bool
    display_variant: ProductVariant | None
    variant_value_ids: set[int]


def _products_list_qs():
    return Product.objects.order_by("name")


def _init_empty_product_scope():
    return _ProductScope(
        option_types=ProductOptionType.objects.none(),
        variants=ProductVariant.objects.none(),
        filtered_variants=ProductVariant.objects.none(),
        selected_filter_by_type={},
        option_filter_rows=[],
        has_drives_image_option_type=False,
        display_variant=None,
        variant_value_ids=set()
    )


def _get_product_option_types(selected_product: Product):
    return (
        selected_product.option_types
        .prefetch_related("values")
        .order_by("position", "name")
    )


def _compute_selected_filter_by_type(selected_product: Product, filter_value_ids: list[int]) -> dict[int, int]:
    """
    Map option_type_id -> option_value_id for the currently selected filter pills
    Only includes values that belong to the selected product.
    """
    if not filter_value_ids:
        return {}

    filter_value_objects = (
        ProductOptionValue.objects
        .filter(id__in=filter_value_ids, option_type__product=selected_product)
        .select_related("option_type")
    )
    return { v.option_type_id: v.id for v in filter_value_objects }


def _get_product_variants(selected_product: Product):
    return (
        selected_product.variants
        .select_related("image", "product", "product__default_image")
        .prefetch_related("option_values__option_type")
        .order_by("name")
    )


def _filtered_variants_for_filters(variants_qs, selected_filter_by_type: dict[int, int]):
    return _filter_variant_queryset(variants_qs, list(selected_filter_by_type.values()))


def _auto_resolve_variant_from_filters(
        selected_product: Product, selected_variant: ProductVariant | None, panel: str, selected_filter_by_type: dict[int, int], filtered_variants_qs
) -> ProductVariant | None:

    if not selected_filter_by_type:
        return selected_variant

    # If the currently selected variant doesn't match this product, treat as absent.
    if selected_variant and selected_variant.product_id != selected_product.id:
        selected_variant = None

    # Case 1: filters uniquely identify a variant no explicit variant is set
    if selected_variant is None and filtered_variants_qs.count() == 1:
        return filtered_variants_qs.first()

    # Case 2: panel=variant requested without explicity variant
    if panel == "variant" and selected_variant is None and filtered_variants_qs.count() == 1:
        return filtered_variants_qs.first()

    return selected_variant


def _variant_value_ids(selected_variant: ProductVariant | None) -> set[int]:
    if not selected_variant:
        return set()
    return set(selected_variant.option_values.values_list("id", flat=True))


def _next_filter_for_value(selected_filter_by_type: dict[int, int], option_type_id: int, value_id: int) -> dict[int, int]:
    """
    Return the filter mapping after clicking a pill for (option_type_id, value_id).
    Toggle off if already active, else set/replace,
    """
    next_filter = dict(selected_filter_by_type)
    if next_filter.get(option_type_id) == value_id:
        next_filter.pop(option_type_id, None)
    else:
        next_filter[option_type_id] = value_id
    return next_filter


def _filter_pairs(selected_product_id: int, include_disabled: bool, panel: str, filter_value_ids: list[int]) -> list[tuple[str, int | str]]:
    """ Shared 'base' pairs for pills/links that preserve filter state. """
    pairs: list[tuple[str, int | str]] = [
        ("product", selected_product_id),
        ("include_disabled", int(include_disabled))
    ]
    if panel == "variant":
        pairs.append(("panel", "variant"))
    for fv_id in filter_value_ids:
        pairs.append(("fv", fv_id))
    return pairs


def _clear_type_filter_value_ids(selected_filter_by_type: dict[int, int], option_type_id_to_clear: int) -> list[int]:
    """ Return the fv IDs after clearing the selection for a single option type. """
    return [ov_id for ot_id, ov_id in selected_filter_by_type.items() if ot_id != option_type_id_to_clear]


def _option_value_pill_dict(*, value: ProductOptionValue, active_filter_value_id: int | None, variant_value_ids: set[int], url: str) -> dict:
    return {
        "id": value.id,
        "name": value.name,
        "is_active_filter": active_filter_value_id == value.id,
        "is_variant_value": value.id in variant_value_ids,
        "disabled": not value.active,
        "url": url
    }


def _build_option_filter_row(
        *, selected_product: Product, option_type: ProductOptionType, selected_filter_by_type: dict[int, int], include_disabled: bool, panel: str, variant_value_ids: set[int]
) -> dict:

    active_filter_value_id = selected_filter_by_type.get(option_type.id)

    values_qs = option_type.values.order_by("position", "name")
    if not include_disabled:
        values_qs = values_qs.filter(active=True)

    row_values: list[dict] = []
    for value in values_qs:
        next_filter = _next_filter_for_value(selected_filter_by_type, option_type.id, value.id)
        pill_pairs = _filter_pairs(
            selected_product_id=selected_product.id,
            include_disabled=include_disabled,
            panel=panel,
            filter_value_ids=list(next_filter.values())
        )
        row_values.append(
            _option_value_pill_dict(
                value=value,
                active_filter_value_id=active_filter_value_id,
                variant_value_ids=variant_value_ids,
                url=_panels_url_pairs(*pill_pairs)
            )
        )

    clear_pairs = _filter_pairs(
        selected_product_id=selected_product.id,
        include_disabled=include_disabled,
        panel=panel,
        filter_value_ids=_clear_type_filter_value_ids(selected_filter_by_type, option_type.id)
    )

    manage_pairs: list[tuple[str, int | str]] = [
        ("product", selected_product.id),
        ("panel", "option_type"),
        ("option_type", option_type.id),
        ("include_disabled", int(include_disabled))
    ]

    for fv_id in selected_filter_by_type.values():
        manage_pairs.append(("fv", fv_id))

    return {
        "option_type": option_type,
        "active_value_id": active_filter_value_id,
        "values": row_values,
        "clear_url": _panels_url_pairs(*clear_pairs),
        "manage_url": _panels_url_pairs(*manage_pairs)
    }


def _build_option_filter_rows(*, selected_product: Product, option_types_qs, selected_filter_by_type: dict[int, int], include_disabled: bool, panel: str, variant_value_ids: set[int]) -> list[dict]:
    return [
        _build_option_filter_row(
            selected_product=selected_product,
            option_type=option_type,
            selected_filter_by_type=selected_filter_by_type,
            include_disabled=include_disabled,
            panel=panel,
            variant_value_ids=variant_value_ids
        )
        for option_type in option_types_qs
    ]


def _drives_image_types(option_types_qs):
    drives_types = list(option_types_qs.filter(drives_image=True, active=True).order_by("id"))
    primary_type = drives_types[0] if drives_types else None
    secondary_candidates = [ot for ot in option_types_qs if not primary_type or ot.id != primary_type.id]
    secondary_type = sorted(secondary_candidates, key=lambda ot: ot.id)[0]if secondary_candidates else None
    return primary_type, secondary_type


def _variant_tiles_and_groups(
        *, selected_product: Product, selected_variant: ProductVariant|None, option_types_qs, filtered_variants_qs, selected_filter_by_type: dict[int, int], include_disabled: bool
) -> tuple[list[dict], dict[str, list]]:

    variant_tiles: list[dict] = []
    grouped_variant_tiles: dict[str, list] = {}

    primary_type, secondary_type = _drives_image_types(option_types_qs)

    def _sort_key(v: ProductVariant) -> tuple:
        opt_map = {ov.option_type_id: ov.name for ov in v.option_values.all()}
        return (
            opt_map.get(primary_type.id, "") if primary_type else "",
            opt_map.get(secondary_type.id, "") if secondary_type else "",
            v.name.lower(),
            v.id
        )

    for variant in sorted(list(filtered_variants_qs), key=_sort_key):
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
            ("include_disabled", int(include_disabled))
        ]

        for ov in variant.option_values.all():
            tile_pairs.append(("fv", ov.id))

        group_label = opt_map.get(primary_type.id, "") if primary_type else ""

        variant_tiles.append({
            "variant": variant,
            "label": option_labels,
            "group_label": group_label,
            "is_selected": bool(selected_variant and selected_variant.id == variant.id),
            "url": _panels_url_pairs(*tile_pairs)
        })

    for tile in variant_tiles:
        key = tile["group_label"] or "All"
        grouped_variant_tiles.setdefault(key, []).append(tile)

    return variant_tiles, grouped_variant_tiles


def _select_forms_and_panel_state(
    *, panel: str, mode: str, bound_form,
    selected_product: Product                 | None,
    selected_variant: ProductVariant          | None,
    selected_option_type: ProductOptionType   | None,
    selected_option_value: ProductOptionValue | None
):
    panel_state = panel or ""

    product_form      = None
    variant_form      = None
    option_type_form  = None
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
                variant_form = ProductManagerVariantForm(instance=selected_variant, product=selected_product)
            elif selected_product and mode == "new_variant":
                variant_form = ProductManagerVariantForm(product=selected_product)

        elif panel_state == "option_type" or mode == "new_option_type":
            panel_state = "option_type"
            if selected_option_type and selected_product and mode != "new_option_type":
                option_type_form = ProductManagerOptionTypeForm(instance=selected_option_type, product=selected_product)
            elif selected_product:
                option_type_form = ProductManagerOptionTypeForm(product=selected_product)

        elif panel_state == "option_value" or mode == "new_option_value":
            panel_state = "option_value"
            if selected_option_value and mode != "new_option_value":
                option_value_form = ProductManagerOptionValueForm(instance=selected_option_value)
            else:
                option_value_form = ProductManagerOptionValueForm()

    return panel_state, product_form, variant_form, option_type_form, option_value_form


def _delete_plan_from_mode(
    *, mode: str, selected_product: Product|None, selected_variant: ProductVariant|None, selected_option_type: ProductOptionType|None, selected_option_value: ProductOptionValue|None
):
    if not mode or not mode.startswith("confirm_delete_"):
        return None

    delete_kind = mode.replace("confirm_delete_", "")
    obj_map = {
        "product": selected_product,
        "variant": selected_variant,
        "option_type": selected_option_type,
        "option_value": selected_option_value
    }
    obj = obj_map.get(delete_kind)
    if obj is None:
        return None

    return {
        "kind": delete_kind,
        "id": obj.id,
        "label": str(obj),
        "soft_delete": _related_exists_for_soft_delete(obj),
        "cascades": _cascade_labels(obj)
    }


def _normalize_panel_state(*, selected_product: Product | None, panel_state: str, variant_form):
    if not selected_product:
        return "empty"

    # panel=variant requested but we couldn't resolve a unique variant / produce form
    if panel_state == "variant" and not variant_form:
        return "browser"

    if panel_state not in ("delete", "option_value", "option_type", "variant", "product"):
        return "browser"

    return panel_state


def _panel_urls(
    *, selected_product: Product|None, selected_variant: ProductVariant|None, selected_option_type: ProductOptionType|None, include_disabled: bool, panel_state: str, selected_filter_by_type: dict[int, int]
):
    active_fv_pairs = [
        ("fv", v) for v in selected_filter_by_type.values()
    ]

    clear_all_filter_url = (
        _panels_url_pairs(("product", selected_product.id), ("include_disabled", int(include_disabled)))
        if selected_product else ""
    )

    edit_product_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "product"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product else ""
    )

    new_variant_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "variant"),
            ("mode", "new_variant"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product else ""
    )

    new_option_type_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", "option_type"),
            ("mode", "new_option_type"),
            ("include_disabled", int(include_disabled)),
            *active_fv_pairs
        )
        if selected_product else ""
    )

    toggle_disabled_url = (
        _panels_url_pairs(
            ("product", selected_product.id),
            ("panel", panel_state),
            ("include_disabled", int(not include_disabled)),
            *([("variant", selected_variant.id)] if selected_variant and panel_state == "variant" else []),
            *active_fv_pairs
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


T = TypeVar("T")

def typed_replace(obj: T, /, **changes) -> T:
    return cast(T, replace(obj, **changes))

# ---------------------------------------------------------------------------
# Low-level utilities
# ---------------------------------------------------------------------------

def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _panels_url_pairs(*pairs: tuple[str, str | int]) -> str:
    """ Build a URL to the panels endpoint from an ordered sequence of (key, value) pairs. """
    base = reverse("hr_shop:product_manager_panels")
    normalized = [(k, v) for k, v in pairs if v not in (None, "")]
    if not normalized:
        return base
    return f"{base}?{urlencode(normalized, doseq=True)}"

# ---------------------------------------------------------------------------
# Selection resolution
# ---------------------------------------------------------------------------

def _resolve_product(sel: SelectionResolved) -> SelectionResolved:
    if sel.product is not None:
        return sel

    pid = sel.ids.product_id
    if not pid:
        return sel

    product = Product.objects.filter(pk=pid).first()
    return typed_replace(sel, product=product)


def _resolve_variant(sel: SelectionResolved) -> SelectionResolved:
    vid = sel.ids.variant_id
    if not vid:
        return sel

    qs = ProductVariant.objects.filter(pk=vid).select_related("product")
    if sel.product:
        qs = qs.filter(product=sel.product)

    variant = qs.first()
    if not variant:
        return sel

    # Derive product from variant if missing
    if sel.product is None:
        return typed_replace(sel, variant=variant, product=variant.product)

    return typed_replace(sel, variant=variant)


def _resolve_option_type(sel: SelectionResolved) -> SelectionResolved:
    otid = sel.ids.option_type_id
    if not otid:
        return sel

    qs = ProductOptionType.objects.filter(pk=otid).select_related("product")
    if sel.product:
        qs = qs.filter(product=sel.product)

    option_type = qs.first()
    if not option_type:
        return sel

    # Derive product from option_type if missing
    if sel.product is None:
        return typed_replace(sel, option_type=option_type, product=option_type.product)

    return typed_replace(sel, option_type=option_type)


def _resolve_option_value(sel: SelectionResolved) -> SelectionResolved:
    ovid = sel.ids.option_value_id
    if not ovid or sel.option_type is None:
        return sel

    option_value = ProductOptionValue.objects.filter(pk=ovid, option_type=sel.option_type).first()
    return typed_replace(sel, option_value=option_value)


def _validate_variant_option_value(sel: SelectionResolved) -> SelectionResolved:
    if sel.variant is None or sel.option_value is None:
        return sel

    allowed = ProductVariantOption.objects.filter(variant=sel.variant, option_value=sel.option_value).exists()
    if allowed:
        return sel

    # If invalid combination, drop option_value (keep option_type)
    return typed_replace(sel, option_value=None)


def _resolve_selection(ids: SelectionIds) -> SelectionResolved:
    sel = SelectionResolved(ids=ids)

    sel = _resolve_product(sel)
    sel = _resolve_variant(sel)
    sel = _resolve_option_type(sel)
    sel = _resolve_option_value(sel)
    sel = _validate_variant_option_value(sel)

    return sel


def _resolve_selection_from_get(request: HttpRequest) -> dict:
    ids = SelectionIds(
        product_id=_to_int(request.GET.get("product")),
        variant_id=_to_int(request.GET.get("variant")),
        option_type_id=_to_int(request.GET.get("option_type")),
        option_value_id=_to_int(request.GET.get("option_value"))
    )

    return _resolve_selection(ids).to_dict()

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
    """ Returns true when hard deletion would break referential intergrity, indicating a soft delete instead"""
    if isinstance(obj, Product):
        return ProductVariant.objects.filter(product=obj).with_orders_or_inventory().exists()

    if isinstance(obj, ProductVariant):
        return obj.has_orders_or_inventory()

    if isinstance(obj, ProductOptionType):
        return ProductOptionValue.objects.filter(option_type=obj, variant_options__isnull=False).exists()

    if isinstance(obj, ProductOptionValue):
        return obj.variant_options.exists()

    return False


def _product_cascade_labels(product: Product) -> list[str]:
    labels = [f"Variant: {n}" for n in product.variants.order_by("name").values_list("name", flat=True)]
    labels += [f"Option Type: {n}" for n in product.option_types.order_by("position", "name").values_list("name", flat=True)]
    return labels


def _option_type_cascade_labels(option_type: ProductOptionType) -> list[str]:
    return [f"Option Value: {n}" for n in option_type.values.order_by("position", "name").values_list("name", flat=True)]


def _cascade_labels(obj) -> list[str]:
    if isinstance(obj, Product):
        return _product_cascade_labels(obj)
    if isinstance(obj, ProductOptionType):
        return _option_type_cascade_labels(obj)
    return []


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


def _variant_form_selected_option_value_ids(variant_form) -> set[int]:
    """
    Determine which option_value IDs should be checked for the variant form grid.

    Priority:
      1) Bound form (failed POST) -> POST data
      2) Existing instance w/ pk -> M2M from DB
      3) New form -> initial
    """
    if not variant_form:
        return set()

    if getattr(variant_form, "is_bound", False):
        raw_list = variant_form.data.getlist("option_values")
        return {v for r in raw_list if (v := _to_int(r))}

    inst = getattr(variant_form, "instance", None)
    if inst is not None and getattr(inst, "pk", None):
        return set(inst.option_values.values_list("id", flat=True))

    raw_initial = getattr(variant_form, "initial", {}).get("option_values", [])
    raw_initial_list = list(raw_initial) if raw_initial else []

    return {v for r in raw_initial_list if (v := _to_int(r))}


def _option_value_groups_for_product(selected_product: Product, selected_ids: set[int], include_disabled: bool,) -> list[dict]:
    """ Build grouped option value rows for the variant checkbox grid. """
    groups: list[dict] = []

    for opt_type in selected_product.option_types.order_by("position", "id"):
        values_qs = opt_type.values.order_by("position", "id")
        if not include_disabled:
            values_qs = values_qs.filter(active=True)

        row = [
            {"id": v.id, "name": v.name, "active": v.active, "checked": v.id in selected_ids}
            for v in values_qs
        ]
        if row:
            groups.append({"type": opt_type, "values": row})

    return groups


# ---------------------------------------------------------------------------
# Main context builder
# ---------------------------------------------------------------------------

def build_panels_context(selection: dict, filter_value_ids: list[int], include_disabled: bool, panel: str, mode: str, bound_form=None) -> dict:
    selected_product: Product | None = selection["product"]
    selected_variant: ProductVariant | None = selection["variant"]
    selected_option_type: ProductOptionType | None = selection["option_type"]
    selected_option_value: ProductOptionValue | None = selection["option_value"]

    products = _products_list_qs()

    scope = _init_empty_product_scope()
    variant_tiles: list[dict] = []
    grouped_variant_tiles: dict[str, list] = {}

    if selected_product:
        scope.option_types = _get_product_option_types(selected_product)
        scope.has_drives_image_option_type = scope.option_types.filter(drives_image=True, active=True).exists()
        scope.display_variant = selected_product.display_variant

        scope.selected_filter_by_type = _compute_selected_filter_by_type(selected_product, filter_value_ids)

        scope.variants = _get_product_variants(selected_product)
        scope.filtered_variants = _filtered_variants_for_filters(scope.variants, scope.selected_filter_by_type)

        selected_variant = _auto_resolve_variant_from_filters(
            selected_product=selected_product,
            selected_variant=selected_variant,
            panel=panel,
            selected_filter_by_type=scope.selected_filter_by_type,
            filtered_variants_qs=scope.filtered_variants
        )

        # if filters were changed and the selected variant no longer matches, drop it
        # _normalize_panel_state will then return 'browser' since variant_form will be None
        if selected_variant and not scope.filtered_variants.filter(pk=selected_variant.pk).exists():
            selected_variant = None

        scope.variant_value_ids = _variant_value_ids(selected_variant)

        scope.option_filter_rows = _build_option_filter_rows(
            selected_product=selected_product,
            option_types_qs=scope.option_types,
            selected_filter_by_type=scope.selected_filter_by_type,
            include_disabled=include_disabled,
            panel=panel,
            variant_value_ids=scope.variant_value_ids
        )

        variant_tiles, grouped_variant_tiles = _variant_tiles_and_groups(
            selected_product=selected_product,
            selected_variant=selected_variant,
            option_types_qs=scope.option_types,
            filtered_variants_qs=scope.filtered_variants,
            selected_filter_by_type=scope.selected_filter_by_type,
            include_disabled=include_disabled
        )

    panel_state, product_form, variant_form, option_type_form, option_value_form = _select_forms_and_panel_state(
        panel=panel,
        mode=mode,
        bound_form=bound_form,
        selected_product=selected_product,
        selected_variant=selected_variant,
        selected_option_type=selected_option_type,
        selected_option_value=selected_option_value
    )

    delete_plan = _delete_plan_from_mode(
        mode=mode,
        selected_product=selected_product,
        selected_variant=selected_variant,
        selected_option_type=selected_option_type,
        selected_option_value=selected_option_value
    )

    if delete_plan is not None:
        panel_state = "delete"

    # Variant checkbox grid groups
    variant_option_groups: list[dict] = []
    if variant_form and selected_product:
        selected_ids = _variant_form_selected_option_value_ids(variant_form)
        variant_option_groups = _option_value_groups_for_product(selected_product, selected_ids, include_disabled)

    panel_state = _normalize_panel_state(
        selected_product=selected_product,
        panel_state=panel_state,
        variant_form=variant_form
    )

    urls = _panel_urls(
        selected_product=selected_product,
        selected_variant=selected_variant,
        selected_option_type=selected_option_type,
        include_disabled=include_disabled,
        panel_state=panel_state,
        selected_filter_by_type=scope.selected_filter_by_type
    )

    return {
        # Products list
        "products": products,

        # Product-scoped data
        "variants": scope.variants,
        "filtered_variants": scope.filtered_variants,
        "option_types": scope.option_types,

        # Selection
        "selected_product": selected_product,
        "selected_variant": selected_variant,
        "selected_option_type": selected_option_type,
        "selected_option_value": selected_option_value,

        # Filter state
        "selected_filter_value_ids": list(scope.selected_filter_by_type.values()),
        "option_filter_rows": scope.option_filter_rows,

        # Right panel display data
        "variant_tiles": variant_tiles,
        "grouped_variant_tiles": grouped_variant_tiles,
        "variant_option_groups": variant_option_groups,
        "has_drives_image_option_type": scope.has_drives_image_option_type,
        "display_variant": scope.display_variant,
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
        **urls
    }
