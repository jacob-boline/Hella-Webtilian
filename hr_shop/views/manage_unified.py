# hr_shop/views/manage_unified.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence, Type, TypeVar, Union
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from hr_shop.forms import (
    ProductManagerOptionTypeForm,
    ProductManagerOptionValueForm,
    ProductManagerProductForm,
    ProductManagerVariantForm
)
from hr_shop.models import (
    Product,
    ProductImage,
    ProductOptionType,
    ProductOptionValue,
    ProductVariant
)


# ---------------------------------------------------------------------------
# Low-level utilities
# ---------------------------------------------------------------------------


def _to_int(value: object) -> int | None:
    """Convert any value to int, returning None on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_int(source: QueryDict, key: str) -> int | None:
    """Read a single query/post param and coerce to int."""
    return _to_int(source.get(key))


def _get_int_list(source: QueryDict, key: str) -> list[int]:
    """Read a multi-valued param and return only the valid integer entries."""
    return [v for x in source.getlist(key) if (v := _to_int(x)) is not None]


# ---------------------------------------------------------------------------
# URL builder
# ---------------------------------------------------------------------------

_UrlPair = tuple[str, Union[str, int]]


def _urlencode_pairs(pairs: Sequence[_UrlPair]) -> str:
    # Normalize everything to str so urlencode is happy and IDEs stop whining.
    normalized: list[tuple[str, str]] = [(k, str(v)) for k, v in pairs if v not in (None, "")]
    return urlencode(normalized, doseq=True)


def _manage_url(*pairs: _UrlPair, **kwargs: Union[str, int, None]) -> str:
    """Build the product-manager URL with any mix of single and multi-valued params.
    Example::
        _manage_url(("fv", 1), ("fv", 2), product=5)
    """
    kw_pairs: list[_UrlPair] = [(k, v) for k, v in kwargs.items() if v is not None]
    all_pairs: list[_UrlPair] = list(pairs) + kw_pairs
    qs = _urlencode_pairs(all_pairs)
    base = reverse("hr_shop:product_manager")
    return f"{base}?{qs}" if qs else base


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SelectionIds:
    product_id: int | None
    variant_id: int | None
    option_type_id: int | None
    option_value_id: int | None


@dataclass
class Selection:
    product: Product | None
    variant: ProductVariant | None
    option_type: ProductOptionType | None
    option_value: ProductOptionValue | None


@dataclass
class PostState:
    action: str
    mode: str
    ids: SelectionIds
    selected_filter_value_ids: list[int] = field(default_factory=list)


@dataclass
class ProductContext:
    """Everything computed from a selected product + filter state."""

    option_types: QuerySet
    variants: QuerySet
    filtered_variants: QuerySet
    selected_filter_by_type: dict[int, int]
    selected_filter_value_ids: list[int]
    selected_variant: ProductVariant | None
    option_filter_rows: list[dict[str, Any]]
    has_drives_image_option_type: bool
    display_variant: ProductVariant | None


def _empty_product_context() -> ProductContext:
    return ProductContext(
        option_types=ProductOptionType.objects.none(),
        variants=ProductVariant.objects.none(),
        filtered_variants=ProductVariant.objects.none(),
        selected_filter_by_type={},
        selected_filter_value_ids=[],
        selected_variant=None,
        option_filter_rows=[],
        has_drives_image_option_type=False,
        display_variant=None
    )


# ---------------------------------------------------------------------------
# Request parsing
# ---------------------------------------------------------------------------


def _parse_selection_ids(source: QueryDict, *, prefix: str = "") -> SelectionIds:
    """Parse SelectionIds from a GET or POST dict.

    Pass ``prefix="selected_"`` for POST hidden fields.
    """
    return SelectionIds(
        product_id=_get_int(source, f"{prefix}product"),
        variant_id=_get_int(source, f"{prefix}variant"),
        option_type_id=_get_int(source, f"{prefix}option_type"),
        option_value_id=_get_int(source, f"{prefix}option_value")
    )


def _parse_post_state(post: QueryDict) -> PostState:
    return PostState(
        action=post.get("action", "") or "",
        mode=post.get("mode", "") or "",
        ids=_parse_selection_ids(post, prefix="selected_"),
        selected_filter_value_ids=_get_int_list(post, "selected_fv")
    )


# ---------------------------------------------------------------------------
# Selection hydration
# ---------------------------------------------------------------------------


def _hydrate_selection(ids: SelectionIds) -> Selection:
    """Fetch model instances for each id, respecting ownership constraints."""
    product = Product.objects.filter(pk=ids.product_id).first() if ids.product_id else None

    variant = (
        ProductVariant.objects.filter(pk=ids.variant_id, product=product).first()
        if product and ids.variant_id
        else None
    )
    option_type = (
        ProductOptionType.objects.filter(pk=ids.option_type_id, product=product).first()
        if product and ids.option_type_id
        else None
    )
    option_value = (
        ProductOptionValue.objects.filter(pk=ids.option_value_id, option_type=option_type).first()
        if option_type and ids.option_value_id
        else None
    )

    return Selection(product=product, variant=variant, option_type=option_type, option_value=option_value)


# ---------------------------------------------------------------------------
# Variant filter helpers
# ---------------------------------------------------------------------------


def _validate_filter_value_ids(value_ids: list[int], product: Product) -> list[int]:
    """Remove ids that don't belong to the given product, preserving order."""
    allowed = set(
        ProductOptionValue.objects.filter(option_type__product=product, active=True).values_list("id", flat=True)
    )
    seen: set[int] = set()
    result: list[int] = []
    for vid in value_ids:
        if vid in allowed and vid not in seen:
            seen.add(vid)
            result.append(vid)
    return result


def _parse_filter_value_ids(get: QueryDict, product: Product | None) -> list[int]:
    """Read ``fv`` params, falling back to a comma-separated single value."""
    raw = get.getlist("fv") or [x.strip() for x in (get.get("fv") or "").split(",") if x.strip()]
    value_ids = [v for x in raw if (v := _to_int(x)) is not None]
    if not product or not value_ids:
        return []
    return _validate_filter_value_ids(value_ids, product)


def _filter_variants(qs: QuerySet[ProductVariant], value_ids: list[int]) -> QuerySet[ProductVariant]:
    """Narrow a variant queryset to only those matching all given option value ids."""
    for vid in value_ids:
        qs = qs.filter(option_values__id=vid)
    return qs.distinct()


def _infer_filters_from_variant(variant: ProductVariant) -> dict[int, int]:
    """Return ``{option_type_id: option_value_id}`` derived from a variant's option values."""
    return {ov.option_type_id: ov.id for ov in variant.option_values.select_related("option_type").all()}


def _auto_resolve_variant(
    filtered_variants: QuerySet[ProductVariant],
    filter_by_type: dict[int, int],
    current_variant: ProductVariant | None,
    product: Product,
) -> ProductVariant | None:
    """Return the lone matching variant when filters yield exactly one result."""
    if not filter_by_type:
        return None
    if current_variant and current_variant.product_id == product.id:
        return None
    return filtered_variants.first() if filtered_variants.count() == 1 else None


# ---------------------------------------------------------------------------
# Option filter row builder
# ---------------------------------------------------------------------------


def _build_option_filter_rows(
    option_types: QuerySet[ProductOptionType],
    selected_filter_by_type: dict[int, int],
    product_id: int,
) -> list[dict[str, Any]]:
    """Build the option-filter UI data for the template."""
    rows: list[dict[str, Any]] = []

    for option_type in option_types:
        active_value_id = selected_filter_by_type.get(option_type.id)
        row_values: list[dict[str, Any]] = []

        for value in option_type.values.filter(active=True).order_by("position", "name"):
            next_selected = dict(selected_filter_by_type)
            if active_value_id == value.id:
                next_selected.pop(option_type.id, None)
            else:
                next_selected[option_type.id] = value.id

            fv_pairs: list[_UrlPair] = [("fv", vid) for vid in next_selected.values()]
            row_values.append({
                "id": value.id,
                "name": value.name,
                "active": active_value_id == value.id,
                "url": _manage_url(*fv_pairs, product=product_id)
            })

        clear_pairs: list[_UrlPair] = [
            ("fv", ov_id)
            for ot_id, ov_id in selected_filter_by_type.items()
            if ot_id != option_type.id
        ]
        rows.append({
            "option_type": option_type,
            "active_value_id": active_value_id,
            "values": row_values,
            "clear_url": _manage_url(*clear_pairs, product=product_id),
            "manage_url": _manage_url(product=product_id, option_type=option_type.id)
        })

    return rows


# ---------------------------------------------------------------------------
# Variant tile builder
# ---------------------------------------------------------------------------


def _build_variant_tiles(
    filtered_variants: QuerySet[ProductVariant],
    selected_filter_by_type: dict[int, int],
    selected_variant: ProductVariant | None,
    product_id: int
) -> list[dict[str, Any]]:
    """Build variant tile data for the template."""
    fv_base_pairs: list[_UrlPair] = [("fv", vid) for vid in selected_filter_by_type.values()]
    tiles: list[dict[str, Any]] = []

    for variant in filtered_variants:
        option_labels = ", ".join(
            variant.option_values.order_by("option_type__position", "position").values_list("name", flat=True)
        )
        tiles.append({
            "variant": variant,
            "label": option_labels,
            "is_selected": bool(selected_variant and selected_variant.id == variant.id),
            "url": _manage_url(*fv_base_pairs, product=product_id, variant=variant.id)
        })

    return tiles


# ---------------------------------------------------------------------------
# Product context builder
# ---------------------------------------------------------------------------


def _build_product_context(product: Product, initial_filter_value_ids: list[int], initial_variant: ProductVariant | None) -> ProductContext:
    """Compute all product-scoped context in one place."""
    option_types = product.option_types.prefetch_related("values").order_by("position", "name")
    has_drives_image = option_types.filter(drives_image=True, active=True).exists()
    display_variant = product.display_variant

    selected_filter_values = (
        ProductOptionValue.objects.filter(id__in=initial_filter_value_ids, option_type__product=product)
        .select_related("option_type")
    )
    filter_by_type: dict[int, int] = {v.option_type_id: v.id for v in selected_filter_values}

    variants = (
        product.variants.select_related("image")
        .prefetch_related("option_values__option_type")
        .order_by("name")
    )
    filtered_variants = _filter_variants(variants, list(filter_by_type.values()))
    selected_variant = initial_variant

    # Infer filters from the selected variant when no filters are set
    if selected_variant and selected_variant.product_id == product.id and not filter_by_type:
        filter_by_type = _infer_filters_from_variant(selected_variant)
        filtered_variants = _filter_variants(variants, list(filter_by_type.values()))

    # Auto-resolve to a single matching variant
    if resolved := _auto_resolve_variant(filtered_variants, filter_by_type, selected_variant, product):
        selected_variant = resolved

    option_filter_rows = _build_option_filter_rows(option_types, filter_by_type, product.id)

    return ProductContext(
        option_types=option_types,
        variants=variants,
        filtered_variants=filtered_variants,
        selected_filter_by_type=filter_by_type,
        selected_filter_value_ids=list(filter_by_type.values()),
        selected_variant=selected_variant,
        option_filter_rows=option_filter_rows,
        has_drives_image_option_type=has_drives_image,
        display_variant=display_variant
    )


# ---------------------------------------------------------------------------
# Model-behaviour helpers
# ---------------------------------------------------------------------------


def _related_exists_for_soft_delete(obj: object) -> bool:
    if isinstance(obj, (Product, ProductVariant)):
        qs = ProductVariant.objects.filter(product=obj) if isinstance(obj, Product) else ProductVariant.objects.filter(pk=obj.pk)
        return qs.filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False)).exists()
    if isinstance(obj, ProductOptionType):
        return ProductOptionValue.objects.filter(option_type=obj, variant_options__isnull=False).exists()
    if isinstance(obj, ProductOptionValue):
        return obj.variant_options.exists()
    return False


def _cascade_labels(obj: object) -> list[str]:
    if isinstance(obj, Product):
        labels = [f"Variant: {n}" for n in obj.variants.order_by("name").values_list("name", flat=True)]
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


def _set_inactive(obj: object) -> None:
    """Soft-delete: mark the object and its children inactive."""
    if isinstance(obj, Product):
        obj.active = False
        obj.save(update_fields=["active"])
        obj.variants.update(active=False)
        obj.option_types.update(active=False)
        ProductOptionValue.objects.filter(option_type__product=obj).update(active=False)
        return

    if isinstance(obj, ProductOptionType):
        obj.active = False
        obj.save(update_fields=["active"])
        obj.values.update(active=False)
        return

    if isinstance(obj, (ProductVariant, ProductOptionValue)):
        obj.active = False
        obj.save(update_fields=["active"])


# ---------------------------------------------------------------------------
# Delete plan builder
# ---------------------------------------------------------------------------


def _build_delete_plan(mode: str, selection: Selection) -> dict[str, Any] | None:
    """Return the delete-confirmation context dict, or None if mode isn't a delete."""
    if not mode.startswith("confirm_delete_"):
        return None

    delete_kind = mode.removeprefix("confirm_delete_")
    obj = {
        "product": selection.product,
        "variant": selection.variant,
        "option_type": selection.option_type,
        "option_value": selection.option_value
    }.get(delete_kind)

    if obj is None:
        return None

    return {
        "kind": delete_kind,
        "id": obj.id,
        "label": str(obj),
        "soft_delete": _related_exists_for_soft_delete(obj),
        "cascades": _cascade_labels(obj)
    }


# ---------------------------------------------------------------------------
# Form selection (simplified)
# ---------------------------------------------------------------------------

F = TypeVar("F")


def _pick_form(bound_form: object | None, form_type: Type[F], factory: Callable[[], F | None]) -> F | None:
    """Prefer the bound (invalid POST) form; otherwise create a new one via factory()."""
    if isinstance(bound_form, form_type):
        return bound_form
    return factory()


def _select_forms(
    bound_form: object | None,
    mode: str,
    selection: Selection,
) -> tuple[
    ProductManagerProductForm | None,
    ProductManagerVariantForm | None,
    ProductManagerOptionTypeForm | None,
    ProductManagerOptionValueForm | None,
]:
    """Return the four optional forms for the template."""
    product = selection.product
    variant = selection.variant
    option_type = selection.option_type
    option_value = selection.option_value

    product_form = _pick_form(
        bound_form,
        ProductManagerProductForm,
        lambda: (
            ProductManagerProductForm()
            if mode == "new_product"
            else ProductManagerProductForm(instance=product)
            if mode == "edit_product" and product
            else None
        ),
    )

    variant_form = _pick_form(
        bound_form,
        ProductManagerVariantForm,
        lambda: (
            ProductManagerVariantForm(product=product)
            if mode == "new_variant" and product
            else ProductManagerVariantForm(instance=variant, product=product)
            if product and variant
            else None
        ),
    )

    option_type_form = _pick_form(
        bound_form,
        ProductManagerOptionTypeForm,
        lambda: (
            ProductManagerOptionTypeForm(product=product)
            if mode == "new_option_type" and product
            else ProductManagerOptionTypeForm(instance=option_type, product=product)
            if product and option_type
            else None
        ),
    )

    option_value_form = _pick_form(
        bound_form,
        ProductManagerOptionValueForm,
        lambda: (
            ProductManagerOptionValueForm()
            if mode == "new_option_value" and option_type
            else ProductManagerOptionValueForm(instance=option_value)
            if option_value
            else None
        ),
    )

    return product_form, variant_form, option_type_form, option_value_form


# ---------------------------------------------------------------------------
# Individual POST action handlers
# ---------------------------------------------------------------------------


def _handle_save_product(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
    post = request.POST
    product_id = _get_int(post, "product_id")
    instance = Product.objects.filter(pk=product_id).first() if product_id else None
    form = ProductManagerProductForm(post, instance=instance)

    if form.is_valid():
        product = form.save()
        messages.success(request, f"Saved product '{product.name}'.")
        return redirect(_manage_url(product=product.id)), _hydrate_selection(ids), form

    messages.error(request, "Please correct the product form errors.")
    return None, Selection(product=instance, variant=None, option_type=None, option_value=None), form


def _handle_save_variant(request: HttpRequest, ids: SelectionIds, filter_value_ids: list[int]) -> tuple[HttpResponse | None, Selection, object | None]:
    post = request.POST
    product = get_object_or_404(Product, pk=_get_int(post, "product_id"))
    variant_id = _get_int(post, "variant_id")
    instance = ProductVariant.objects.filter(pk=variant_id, product=product).first() if variant_id else None
    form = ProductManagerVariantForm(post, request.FILES, instance=instance, product=product)

    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        if new_image := form.cleaned_data.get("new_image_file"):
            variant.image = ProductImage.objects.create(image=new_image, alt_text=variant.name or product.name)
        variant.save()
        form.save_m2m()
        messages.success(request, f"Saved variant '{variant.name}'.")
        fv_pairs: list[_UrlPair] = [("fv", v) for v in filter_value_ids]
        return redirect(_manage_url(*fv_pairs, product=product.id, variant=variant.id)), _hydrate_selection(ids), form

    messages.error(request, "Please correct the variant form errors.")
    return None, Selection(product=product, variant=instance, option_type=None, option_value=None), form


def _handle_save_option_type(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
    post = request.POST
    product = get_object_or_404(Product, pk=_get_int(post, "product_id"))
    option_type_id = _get_int(post, "option_type_id")
    instance = ProductOptionType.objects.filter(pk=option_type_id, product=product).first() if option_type_id else None
    form = ProductManagerOptionTypeForm(post, instance=instance, product=product)

    if form.is_valid():
        option_type = form.save(commit=False)
        option_type.product = product
        option_type.save()
        messages.success(request, f"Saved option type '{option_type.name}'.")
        return redirect(_manage_url(product=product.id, option_type=option_type.id)), _hydrate_selection(ids), form

    messages.error(request, "Please correct the option type form errors.")
    return None, Selection(product=product, variant=None, option_type=instance, option_value=None), form


def _handle_save_option_value(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
    post = request.POST
    option_type = get_object_or_404(ProductOptionType, pk=_get_int(post, "option_type_id"))
    value_id = _get_int(post, "option_value_id")
    instance = ProductOptionValue.objects.filter(pk=value_id, option_type=option_type).first() if value_id else None
    form = ProductManagerOptionValueForm(post, instance=instance)

    if form.is_valid():
        option_value = form.save(commit=False)
        option_value.option_type = option_type
        option_value.save()
        messages.success(request, f"Saved option value '{option_value.name}'.")
        owner_product_id: int = int(option_type.product_id)
        return (
            redirect(_manage_url(product=owner_product_id, option_type=option_type.id, option_value=option_value.id)),
            _hydrate_selection(ids),
            form
        )

    messages.error(request, "Please correct the option value form errors.")
    return None, Selection(product=option_type.product, variant=None, option_type=option_type, option_value=instance), form


def _handle_delete_confirmed(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, None]:
    """Handle delete_confirmed action. Always produces a redirect."""
    fallback_url = _manage_url(
        product=ids.product_id,
        variant=ids.variant_id,
        option_type=ids.option_type_id,
        option_value=ids.option_value_id
    )
    selection = _hydrate_selection(ids)

    if not request.user.is_superuser:
        messages.error(request, "Only superusers can delete records.")
        return redirect(fallback_url), selection, None

    post = request.POST
    kind = post.get("delete_kind") or ""
    object_id = _get_int(post, "delete_id")

    model_map: dict[str, type] = {
        "product": Product,
        "variant": ProductVariant,
        "option_type": ProductOptionType,
        "option_value": ProductOptionValue
    }
    model = model_map.get(kind)
    if model is None or object_id is None:
        messages.error(request, "Invalid delete request.")
        return redirect(fallback_url), selection, None

    obj = get_object_or_404(model, pk=object_id)
    if _related_exists_for_soft_delete(obj):
        _set_inactive(obj)
        messages.warning(request, f"{kind.replace('_', ' ').title()} had related records and was set inactive instead.")
    else:
        obj.delete()
        messages.success(request, f"Deleted {kind.replace('_', ' ')}.")

    redirect_url = {
        "product": _manage_url(),
        "variant": _manage_url(product=ids.product_id),
        "option_type": _manage_url(product=ids.product_id),
        "option_value": _manage_url(product=ids.product_id, option_type=ids.option_type_id)
    }.get(kind, _manage_url())

    return redirect(redirect_url), selection, None


# ---------------------------------------------------------------------------
# POST dispatcher
# ---------------------------------------------------------------------------


def _apply_post_action(request: HttpRequest, state: PostState) -> tuple[HttpResponse | None, Selection, object | None]:
    """Dispatch the POST action to the appropriate handler."""
    dispatch: dict[str, Callable[[], tuple[HttpResponse | None, Selection, object | None]]] = {
        "save_product": lambda: _handle_save_product(request, state.ids),
        "save_variant": lambda: _handle_save_variant(request, state.ids, state.selected_filter_value_ids),
        "save_option_type": lambda: _handle_save_option_type(request, state.ids),
        "save_option_value": lambda: _handle_save_option_value(request, state.ids),
        "delete_confirmed": lambda: _handle_delete_confirmed(request, state.ids),
    }
    handler = dispatch.get(state.action)
    if handler is None:
        return None, _hydrate_selection(state.ids), None
    return handler()


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------


@staff_member_required
def product_manager(request: HttpRequest) -> HttpResponse:
    bound_form: object | None = None

    if request.method == "POST":
        state = _parse_post_state(request.POST)
        redirect_response, selection, bound_form = _apply_post_action(request, state)
        if redirect_response is not None:
            return redirect_response
        mode = state.mode
        filter_value_ids = state.selected_filter_value_ids
    else:
        selection = _hydrate_selection(_parse_selection_ids(request.GET))
        mode = request.GET.get("mode") or ""
        filter_value_ids = _parse_filter_value_ids(request.GET, selection.product)

    ctx = _build_product_context(selection.product, filter_value_ids, selection.variant) if selection.product else _empty_product_context()

    # Sync the (possibly auto-resolved) variant back into selection
    selection.variant = ctx.selected_variant

    is_form_mode = mode in {"new_product", "edit_product", "new_variant", "new_option_type", "new_option_value"}
    product_form, variant_form, option_type_form, option_value_form = _select_forms(bound_form, mode, selection)
    delete_plan = _build_delete_plan(mode, selection)

    variant_tiles = (
        _build_variant_tiles(ctx.filtered_variants, ctx.selected_filter_by_type, selection.variant, selection.product.id)
        if selection.product
        else []
    )

    show_variant_browser = bool(
        selection.product
        and not delete_plan
        and not any([variant_form, option_type_form, option_value_form, product_form])
        and not is_form_mode
    )
    show_variant_image_editor = bool(
        variant_form
        and selection.product
        and (
            ctx.has_drives_image_option_type
            or (ctx.display_variant and selection.variant and selection.variant.id == ctx.display_variant.id)
        )
    )

    return render(request, "hr_shop/manage/_unified_product_manager.html", {
        "products": Product.objects.order_by("name"),
        "variants": ctx.variants,
        "filtered_variants": ctx.filtered_variants,
        "option_types": ctx.option_types,
        "selected_product": selection.product,
        "selected_variant": selection.variant,
        "selected_option_type": selection.option_type,
        "selected_option_value": selection.option_value,
        "selected_filter_value_ids": ctx.selected_filter_value_ids,
        "option_filter_rows": ctx.option_filter_rows,
        "variant_tiles": variant_tiles,
        "clear_all_filter_url": _manage_url(product=selection.product.id) if selection.product else "",
        "edit_product_url": _manage_url(product=selection.product.id, mode="edit_product") if selection.product else "",
        "display_variant": ctx.display_variant,
        "has_drives_image_option_type": ctx.has_drives_image_option_type,
        "show_variant_browser": show_variant_browser,
        "show_variant_image_editor": show_variant_image_editor,
        "product_form": product_form,
        "variant_form": variant_form,
        "option_type_form": option_type_form,
        "option_value_form": option_value_form,
        "mode": mode,
        "delete_plan": delete_plan,
        "is_superuser": request.user.is_superuser
    })
