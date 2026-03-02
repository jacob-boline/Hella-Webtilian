# hr_shop/views/manage_unified.py
from __future__ import annotations

from typing import TypedDict
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from hr_shop.forms import ProductManagerOptionTypeForm, ProductManagerOptionValueForm, ProductManagerProductForm, ProductManagerVariantForm
from hr_shop.models import Product, ProductImage, ProductOptionType, ProductOptionValue, ProductVariant, ProductVariantOption


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_manage_url(**params):
    base = reverse("hr_shop:product_manager")
    filtered = {k: v for k, v in params.items() if v not in (None, "")}
    if not filtered:
        return base
    return f"{base}?{urlencode(filtered)}"


def _build_manage_url_pairs(*pairs: tuple[str, str | int]) -> str:
    base = reverse("hr_shop:product_manager")
    normalized = [(k, v) for k, v in pairs if v not in (None, "")]
    if not normalized:
        return base
    return f"{base}?{urlencode(normalized, doseq=True)}"


class Selection(TypedDict):
    product: Product | None
    variant: ProductVariant | None
    option_type: ProductOptionType | None
    option_value: ProductOptionValue | None


def _resolve_selection(
    product_id: int | None,
    variant_id: int | None,
    option_type_id: int | None,
    option_value_id: int | None,
) -> Selection:
    """
    Resolve a selection across your model graph:

      Product -> Variant
      Product -> OptionType -> OptionValue
      Variant <-> OptionValue (M2M through ProductVariantOption)

    Validation rules:
    - If product_id is provided, Product must exist.
    - Variant must belong to selected product (when product is known).
      If product is unknown but variant is provided, derive product from variant.
    - OptionType must belong to selected product (when product is known).
      If product is unknown but option_type is provided, derive product from option_type.
    - OptionValue must belong to selected option_type.
    - If both variant and option_value are present, option_value must be part of variant.option_values.
    """
    selected_product: Product | None = None
    selected_variant: ProductVariant | None = None
    selected_option_type: ProductOptionType | None = None
    selected_option_value: ProductOptionValue | None = None

    # 1) Product (if given)
    if product_id:
        selected_product = Product.objects.filter(pk=product_id).first()

    # 2) Variant (validate against product when known; otherwise derive product)
    if variant_id:
        v_qs = ProductVariant.objects.filter(pk=variant_id).select_related("product")
        if selected_product:
            v_qs = v_qs.filter(product=selected_product)
        selected_variant = v_qs.first()
        if selected_variant and not selected_product:
            selected_product = selected_variant.product

    # 3) OptionType (validate against product when known; otherwise derive product)
    if option_type_id:
        ot_qs = ProductOptionType.objects.filter(pk=option_type_id).select_related("product")
        if selected_product:
            ot_qs = ot_qs.filter(product=selected_product)
        selected_option_type = ot_qs.first()
        if selected_option_type and not selected_product:
            selected_product = selected_option_type.product

    # 4) OptionValue (must belong to option_type)
    if option_value_id and selected_option_type:
        selected_option_value = ProductOptionValue.objects.filter(
            pk=option_value_id,
            option_type=selected_option_type
        ).first()

    # 5) Cross-check: option_value must be allowed for this variant (if both provided)
    if selected_variant and selected_option_value:
        allowed = ProductVariantOption.objects.filter(
            variant=selected_variant,
            option_value=selected_option_value
        ).exists()
        if not allowed:
            selected_option_value = None

    return {
        "product": selected_product,
        "variant": selected_variant,
        "option_type": selected_option_type,
        "option_value": selected_option_value
    }


def _selection_from_request(request: HttpRequest) -> Selection:
    return _resolve_selection(
        _to_int(request.GET.get("product", "")),
        _to_int(request.GET.get("variant", "")),
        _to_int(request.GET.get("option_type", "")),
        _to_int(request.GET.get("option_value", ""))
    )


def _selection_from_post(
    selected_product_id: int | None,
    selected_variant_id: int | None,
    selected_option_type_id: int | None,
    selected_option_value_id: int | None
) -> Selection:
    return _resolve_selection(
        selected_product_id,
        selected_variant_id,
        selected_option_type_id,
        selected_option_value_id
    )


# def _selection_from_request(request: HttpRequest):
#     product_id = _to_int(request.GET.get("product", ""))
#     variant_id = _to_int(request.GET.get("variant", ""))
#     option_type_id = _to_int(request.GET.get("option_type", ""))
#     option_value_id = _to_int(request.GET.get("option_value", ""))
#
#     selected_product = Product.objects.filter(pk=product_id).first() if product_id else None
#
#     selected_variant = None
#     if selected_product and variant_id:
#         selected_variant = ProductVariant.objects.filter(pk=variant_id, product=selected_product).first()
#
#     selected_option_type = None
#     if selected_product and option_type_id:
#         selected_option_type = ProductOptionType.objects.filter(pk=option_type_id, product=selected_product).first()
#
#     selected_option_value = None
#     if selected_option_type and option_value_id:
#         selected_option_value = ProductOptionValue.objects.filter(pk=option_value_id, option_type=selected_option_type).first()
#
#     return {
#         "product": selected_product,
#         "variant": selected_variant,
#         "option_type": selected_option_type,
#         "option_value": selected_option_value
#     }
#
#
# def _selection_from_post(
#     selected_product_id: int | None,
#     selected_variant_id: int | None,
#     selected_option_type_id: int | None,
#     selected_option_value_id: int | None
# ):
#     selected_product = Product.objects.filter(pk=selected_product_id).first() if selected_product_id else None
#
#     selected_variant = None
#     if selected_product and selected_variant_id:
#         selected_variant = ProductVariant.objects.filter(pk=selected_variant_id, product=selected_product).first()
#
#     selected_option_type = None
#     if selected_product and selected_option_type_id:
#         selected_option_type = ProductOptionType.objects.filter(pk=selected_option_type_id, product=selected_product).first()
#
#     selected_option_value = None
#     if selected_option_type and selected_option_value_id:
#         selected_option_value = ProductOptionValue.objects.filter(pk=selected_option_value_id, option_type=selected_option_type).first()
#
#     return {
#         "product": selected_product,
#         "variant": selected_variant,
#         "option_type": selected_option_type,
#         "option_value": selected_option_value
#     }


def _related_exists_for_soft_delete(obj):
    if isinstance(obj, Product):
        return ProductVariant.objects.filter(product=obj).filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False)).exists()
    if isinstance(obj, ProductVariant):
        return ProductVariant.objects.filter(pk=obj.pk).filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False)).exists()
    if isinstance(obj, ProductOptionType):
        return ProductOptionValue.objects.filter(option_type=obj, variant_options__isnull=False).exists()
    if isinstance(obj, ProductOptionValue):
        return obj.variant_options.exists()
    return False


def _cascade_labels(obj):
    if isinstance(obj, Product):
        variants = list(obj.variants.order_by("name").values_list("name", flat=True))
        option_types = list(obj.option_types.order_by("position", "name").values_list("name", flat=True))
        labels = []
        labels.extend([f"Variant: {name}" for name in variants])
        labels.extend([f"Option Type: {name}" for name in option_types])
        return labels
    if isinstance(obj, ProductOptionType):
        values = list(obj.values.order_by("position", "name").values_list("name", flat=True))
        return [f"Option Value: {name}" for name in values]
    return []


def _set_inactive(obj):
    obj.active = False
    obj.save(update_fields=["active"])

    if isinstance(obj, (ProductOptionValue or ProductVariant)):
        return

    if isinstance(obj, ProductOptionType):
        obj.values.update(active=False)
        return

    if isinstance(obj, Product):
        obj.variants.update(active=False)
        obj.option_types.update(active=False)
        ProductOptionValue.objects.filter(option_type__product=obj).update(active=False)


def _object_for_delete(kind: str, object_id: int):
    mapping = {
        "product": Product,
        "variant": ProductVariant,
        "option_type": ProductOptionType,
        "option_value": ProductOptionValue
    }
    model = mapping.get(kind)
    if model is None:
        return None
    return get_object_or_404(model, pk=object_id)


def _selected_filter_value_ids(request: HttpRequest, selected_product: Product | None) -> list[int]:
    raw_values = request.GET.getlist("fv")
    if not raw_values and request.GET.get("fv", ""):
        raw_values = [x.strip() for x in request.GET.get("fv", "").split(",") if x.strip()]

    value_ids = [_to_int(v) for v in raw_values]
    valid_value_ids = [v for v in value_ids if v]
    if not selected_product or not valid_value_ids:
        return []

    allowed_ids = set(ProductOptionValue.objects.filter(option_type__product=selected_product).values_list("id", flat=True))
    deduped: list[int] = []
    seen = set()
    for value_id in valid_value_ids:
        if value_id in allowed_ids and value_id not in seen:
            deduped.append(value_id)
            seen.add(value_id)
    return deduped


def _filter_variant_queryset(variants_qs, selected_filter_value_ids: list[int]):
    filtered = variants_qs
    for value_id in selected_filter_value_ids:
        filtered = filtered.filter(option_values__id=value_id)
    return filtered.distinct()


def _grouped_variant_option_values(variant_form, selected_product: Product | None, include_disabled: bool):
    if not variant_form or not selected_product:
        return []
    selected_ids = set()
    bound_values = variant_form.data.getlist("option_values") if variant_form.is_bound else variant_form.initial.get("option_values", [])
    for raw in bound_values:
        val = _to_int(raw)
        if val:
            selected_ids.add(val)

    groups = []
    for opt_type in selected_product.option_types.order_by("position", "id"):
        values = opt_type.values.order_by("position", "id")
        if not include_disabled:
            values = values.filter(active=True)
        row = []
        for val in values:
            row.append({"id": val.id, "name": val.name, "active": val.active, "checked": val.id in selected_ids})
        if row:
            groups.append({"type": opt_type, "values": row})
    return groups


@staff_member_required
def product_manager(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        action = request.POST.get("action", "")

        selected_product_id = _to_int(request.POST.get("selected_product", ""))
        selected_variant_id = _to_int(request.POST.get("selected_variant", ""))
        selected_option_type_id = _to_int(request.POST.get("selected_option_type", ""))
        selected_option_value_id = _to_int(request.POST.get("selected_option_value", ""))
        include_disabled = request.POST.get("include_disabled") == "1"

        selected_fv_ids = [_to_int(v) for v in request.POST.getlist("selected_fv")]
        selected_fv_ids = [v for v in selected_fv_ids if v]

        if action == "save_product":
            product_id = _to_int(request.POST.get("product_id", ""))
            instance = Product.objects.filter(pk=product_id).first() if product_id else None
            form = ProductManagerProductForm(request.POST, request.FILES, instance=instance)
            if form.is_valid():
                product = form.save()
                messages.success(request, f"Saved product '{product.name}'.")
                return redirect(_build_manage_url_pairs(("product", product.id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))
            messages.error(request, "Please correct the product form errors.")
            selected_product = instance
            selected_variant_id = None
            selected_option_type_id = None
            selected_option_value_id = None
        elif action == "save_variant":
            product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id", "")))
            variant_id = _to_int(request.POST.get("variant_id", ""))
            instance = ProductVariant.objects.filter(pk=variant_id, product=product).first() if variant_id else None
            form = ProductManagerVariantForm(request.POST, request.FILES, instance=instance, product=product)
            if form.is_valid():
                variant = form.save(commit=False)
                variant.product = product
                new_image_file = form.cleaned_data.get("new_image_file")
                if new_image_file:
                    variant.image = ProductImage.objects.create(image=new_image_file, alt_text=variant.name or product.name)
                variant.save()
                form.save_m2m()
                messages.success(request, f"Saved variant '{variant.name}'.")
                return redirect(_build_manage_url_pairs(("product", product.id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))
            messages.error(request, "Please correct the variant form errors.")
            selected_product = product
            selected_product_id = product.id
            selected_variant_id = variant_id
            selected_option_type_id = None
            selected_option_value_id = None
        elif action == "save_option_type":
            product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id", "")))
            option_type_id = _to_int(request.POST.get("option_type_id", ""))
            instance = ProductOptionType.objects.filter(pk=option_type_id, product=product).first() if option_type_id else None
            form = ProductManagerOptionTypeForm(request.POST, instance=instance, product=product)
            if form.is_valid():
                option_type = form.save(commit=False)
                option_type.product = product
                option_type.save()
                messages.success(request, f"Saved option type '{option_type.name}'.")
                return redirect(_build_manage_url_pairs(("product", product.id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))
            messages.error(request, "Please correct the option type form errors.")
            selected_product = product
            selected_product_id = product.id
            selected_option_type_id = option_type_id
        elif action == "save_option_value":
            option_type = get_object_or_404(ProductOptionType, pk=_to_int(request.POST.get("option_type_id", "")))
            value_id = _to_int(request.POST.get("option_value_id", ""))
            instance = ProductOptionValue.objects.filter(pk=value_id, option_type=option_type).first() if value_id else None
            form = ProductManagerOptionValueForm(request.POST, instance=instance)
            if form.is_valid():
                option_value = form.save(commit=False)
                option_value.option_type = option_type
                option_value.save()
                messages.success(request, f"Saved option value '{option_value.name}'.")
                return redirect(_build_manage_url_pairs(("product", option_type.product_id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))
            messages.error(request, "Please correct the option value form errors.")
            selected_product = option_type.product
            selected_product_id = option_type.product_id
            selected_option_type_id = option_type.id
            selected_option_value_id = value_id
        elif action == "delete_confirmed":
            if not request.user.is_superuser:
                messages.error(request, "Only superusers can delete records.")
                return redirect(_build_manage_url_pairs(("product", selected_product_id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))

            kind = request.POST.get("delete_kind", "")
            object_id = _to_int(request.POST.get("delete_id", ""))
            obj = _object_for_delete(kind, object_id)
            if obj is None:
                messages.error(request, "Invalid delete request.")
                return redirect(_build_manage_url_pairs(("product", selected_product_id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))

            should_soft_delete = _related_exists_for_soft_delete(obj)
            if should_soft_delete:
                _set_inactive(obj)
                messages.warning(request, f"{kind.replace('_', ' ').title()} had related records and was set inactive instead.")
            else:
                obj.delete()
                messages.success(request, f"Deleted {kind.replace('_', ' ')}.")

            if kind == "product":
                return redirect(_build_manage_url())
            return redirect(_build_manage_url_pairs(("product", selected_product_id), *(("fv", v) for v in selected_fv_ids), ("include_disabled", int(include_disabled))))
        else:
            form = None
            selected_product = Product.objects.filter(pk=selected_product_id).first() if selected_product_id else None

        selection = _selection_from_post(
            selected_product.id if "selected_product" in locals() and selected_product else selected_product_id,
            selected_variant_id,
            selected_option_type_id,
            selected_option_value_id,
        )
        mode = request.POST.get("mode", "")
        panel = request.POST.get("panel", "")
        selected_filter_value_ids = selected_fv_ids
    else:
        selection = _selection_from_request(request)
        mode = request.GET.get("mode", "")
        panel = request.GET.get("panel", "")
        form = None
        selected_filter_value_ids = _selected_filter_value_ids(request, selection["product"])
        include_disabled = request.GET.get("include_disabled") == "1"

    selected_product = selection["product"]
    selected_variant = selection["variant"]
    selected_option_type = selection["option_type"]
    selected_option_value = selection["option_value"]

    products = Product.objects.order_by("name")

    option_types = ProductOptionType.objects.none()
    variants = ProductVariant.objects.none()
    filtered_variants = ProductVariant.objects.none()
    selected_filter_by_type: dict[int, int] = {}
    option_filter_rows = []
    has_drives_image_option_type = False
    display_variant = None

    if selected_product:
        option_types = selected_product.option_types.prefetch_related("values").order_by("position", "name")
        has_drives_image_option_type = option_types.filter(drives_image=True, active=True).exists()
        display_variant = selected_product.display_variant

        selected_filter_values = ProductOptionValue.objects.filter(id__in=selected_filter_value_ids, option_type__product=selected_product).select_related("option_type")
        selected_filter_by_type = {v.option_type_id: v.id for v in selected_filter_values}

        variants = selected_product.variants.select_related("image", "product", "product__image").prefetch_related("option_values__option_type").order_by("name")
        filtered_variants = _filter_variant_queryset(variants, list(selected_filter_by_type.values()))

        if selected_filter_by_type and (not selected_variant or selected_variant.product_id != selected_product.id):
            resolved = filtered_variants.first() if filtered_variants.count() == 1 else None
            if resolved:
                selected_variant = resolved

        for option_type in option_types:
            active_value_id = selected_filter_by_type.get(option_type.id)
            row_values = []
            values_qs = option_type.values.order_by("position", "name")
            if not include_disabled:
                values_qs = values_qs.filter(active=True)
            for value in values_qs:
                row_pairs = [("product", selected_product.id), ("include_disabled", int(include_disabled))]
                next_selected = dict(selected_filter_by_type)
                if active_value_id == value.id:
                    next_selected.pop(option_type.id, None)
                else:
                    next_selected[option_type.id] = value.id

                for selected_value_id in next_selected.values():
                    row_pairs.append(("fv", selected_value_id))

                row_values.append({"id": value.id, "name": value.name, "active": active_value_id == value.id, "url": _build_manage_url_pairs(*row_pairs), "disabled": not value.active})

            clear_pairs = [("product", selected_product.id), ("include_disabled", int(include_disabled))]
            for ot_id, ov_id in selected_filter_by_type.items():
                if ot_id != option_type.id:
                    clear_pairs.append(("fv", ov_id))

            option_filter_rows.append({
                "option_type": option_type,
                "active_value_id": active_value_id,
                "values": row_values,
                "clear_url": _build_manage_url_pairs(*clear_pairs),
                "manage_url": _build_manage_url_pairs(("product", selected_product.id), ("panel", "option_type"), ("option_type", option_type.id), ("include_disabled", int(include_disabled)), *(("fv", v) for v in selected_filter_by_type.values())),
            })

    panel_state = panel or ""

    if form is not None and isinstance(form, ProductManagerProductForm):
        product_form = form
        panel_state = "product"
    elif mode in {"new_product", "edit_product"}:
        product_form = ProductManagerProductForm(instance=selected_product) if mode == "edit_product" else ProductManagerProductForm()
        panel_state = "product"
    else:
        product_form = None

    if form is not None and isinstance(form, ProductManagerVariantForm):
        variant_form = form
        panel_state = "variant"
    elif mode == "new_variant" and selected_product:
        variant_form = ProductManagerVariantForm(product=selected_product)
        panel_state = "variant"
    elif panel_state == "variant" and selected_variant and selected_product:
        variant_form = ProductManagerVariantForm(instance=selected_variant, product=selected_product)
    else:
        variant_form = None

    if form is not None and isinstance(form, ProductManagerOptionTypeForm):
        option_type_form = form
        panel_state = "option_type"
    elif mode == "new_option_type" and selected_product:
        option_type_form = ProductManagerOptionTypeForm(product=selected_product)
        panel_state = "option_type"
    elif panel_state == "option_type" and selected_option_type and selected_product:
        option_type_form = ProductManagerOptionTypeForm(instance=selected_option_type, product=selected_product)
    else:
        option_type_form = None

    if form is not None and isinstance(form, ProductManagerOptionValueForm):
        option_value_form = form
        panel_state = "option_value"
    elif mode == "new_option_value" and selected_option_type:
        option_value_form = ProductManagerOptionValueForm()
        panel_state = "option_value"
    elif panel_state == "option_value" and selected_option_value:
        option_value_form = ProductManagerOptionValueForm(instance=selected_option_value)
    else:
        option_value_form = None

    delete_plan = None
    if mode.startswith("confirm_delete_"):
        panel_state = "delete"
        delete_kind = mode.replace("confirm_delete_", "")
        selected_map = {"product": selected_product, "variant": selected_variant, "option_type": selected_option_type, "option_value": selected_option_value}
        obj = selected_map.get(delete_kind)
        if obj is not None:
            delete_plan = {"kind": delete_kind, "id": obj.id, "label": str(obj), "soft_delete": _related_exists_for_soft_delete(obj), "cascades": _cascade_labels(obj)}

    variant_option_groups = _grouped_variant_option_values(variant_form, selected_product, include_disabled)

    # build deterministic grouped tiles
    variant_tiles = []
    if selected_product:
        drives_types = list(option_types.filter(drives_image=True, active=True).order_by("id"))
        primary_type = drives_types[0] if drives_types else None
        secondary_candidates = [ot for ot in option_types if (not primary_type or ot.id != primary_type.id)]
        secondary_type = sorted(secondary_candidates, key=lambda ot: ot.id)[0] if secondary_candidates else None

        def _variant_sort_meta(variant: ProductVariant):
            opt_map = {ov.option_type_id: ov.name for ov in variant.option_values.all()}
            group_label = opt_map.get(primary_type.id) if primary_type else None
            second_label = opt_map.get(secondary_type.id) if secondary_type else None
            return group_label or "", second_label or "", variant.name.lower(), variant.id

        sorted_variants = sorted(list(filtered_variants), key=_variant_sort_meta)

        for variant in sorted_variants:
            opt_map = {ov.option_type_id: ov.name for ov in variant.option_values.all()}
            option_labels = ", ".join(variant.option_values.order_by("option_type__position", "position").values_list("name", flat=True))
            tile_pairs = [("product", selected_product.id), ("panel", "variant"), ("variant", variant.id), ("include_disabled", int(include_disabled))]
            for selected_id in selected_filter_by_type.values():
                tile_pairs.append(("fv", selected_id))
            variant_tiles.append({
                "variant": variant,
                "label": option_labels,
                "group_label": opt_map.get(primary_type.id, "") if primary_type else "",
                "is_selected": bool(selected_variant and selected_variant.id == variant.id),
                "url": _build_manage_url_pairs(*tile_pairs)
            })

    grouped_variant_tiles = {}

    for tile in variant_tiles:
        key = tile.get("group_label") or "All"
        grouped_variant_tiles.setdefault(key, []).append(tile)

    clear_all_filter_url = _build_manage_url_pairs(("product", selected_product.id), ("include_disabled", int(include_disabled))) if selected_product else ""
    edit_product_url = _build_manage_url_pairs(("product", selected_product.id), ("panel", "product"), ("mode", "edit_product"), ("include_disabled", int(include_disabled)), *(("fv", v) for v in selected_filter_by_type.values())) if selected_product else ""

    if not selected_product:
        panel_state = "empty"
    elif panel_state not in {"delete", "option_value", "option_type", "variant", "product"}:
        panel_state = "browser"

    return render(request, "hr_shop/manage/_unified_product_manager.html", {
        "products": products,
        "variants": variants,
        "filtered_variants": filtered_variants,
        "option_types": option_types,
        "selected_product": selected_product,
        "selected_variant": selected_variant,
        "selected_option_type": selected_option_type,
        "selected_option_value": selected_option_value,
        "selected_filter_value_ids": list(selected_filter_by_type.values()),
        "option_filter_rows": option_filter_rows,
        "variant_tiles": variant_tiles,
        "grouped_variant_tiles": grouped_variant_tiles,
        "variant_option_groups": variant_option_groups,
        "clear_all_filter_url": clear_all_filter_url,
        "edit_product_url": edit_product_url,
        "display_variant": display_variant,
        "has_drives_image_option_type": has_drives_image_option_type,
        "include_disabled": include_disabled,
        "product_form": product_form,
        "variant_form": variant_form,
        "option_type_form": option_type_form,
        "option_value_form": option_value_form,
        "mode": mode,
        "panel_state": panel_state,
        "delete_plan": delete_plan,
        "is_superuser": request.user.is_superuser
    })
























# # hr_shop/views/manage_unified.py
#
# from __future__ import annotations
#
# from dataclasses import dataclass, field
# from typing import Any, Callable, Sequence, Type, TypeVar, Union
# from urllib.parse import urlencode
#
# from django.contrib import messages
# from django.contrib.admin.views.decorators import staff_member_required
# from django.db.models import Q, QuerySet
# from django.http import HttpRequest, HttpResponse, QueryDict
# from django.shortcuts import get_object_or_404, redirect, render
# from django.urls import reverse
#
# from hr_shop.forms import (
#     ProductManagerOptionTypeForm,
#     ProductManagerOptionValueForm,
#     ProductManagerProductForm,
#     ProductManagerVariantForm
# )
# from hr_shop.models import (
#     Product,
#     ProductImage,
#     ProductOptionType,
#     ProductOptionValue,
#     ProductVariant
# )
#
#
# # ---------------------------------------------------------------------------
# # Low-level utilities
# # ---------------------------------------------------------------------------
#
#
# def _to_int(value: object) -> int | None:
#     """Convert any value to int, returning None on failure."""
#     try:
#         return int(value)
#     except (TypeError, ValueError):
#         return None
#
#
# def _get_int(source: QueryDict, key: str) -> int | None:
#     """Read a single query/post param and coerce to int."""
#     return _to_int(source.get(key))
#
#
# def _get_int_list(source: QueryDict, key: str) -> list[int]:
#     """Read a multi-valued param and return only the valid integer entries."""
#     return [v for x in source.getlist(key) if (v := _to_int(x)) is not None]
#
#
# # ---------------------------------------------------------------------------
# # URL builder
# # ---------------------------------------------------------------------------
#
# _UrlPair = tuple[str, Union[str, int]]
#
#
# def _urlencode_pairs(pairs: Sequence[_UrlPair]) -> str:
#     # Normalize everything to str so urlencode is happy and IDEs stop whining.
#     normalized: list[tuple[str, str]] = [(k, str(v)) for k, v in pairs if v not in (None, "")]
#     return urlencode(normalized, doseq=True)
#
#
# def _manage_url(*pairs: _UrlPair, **kwargs: Union[str, int, None]) -> str:
#     """Build the product-manager URL with any mix of single and multi-valued params.
#     Example::
#         _manage_url(("fv", 1), ("fv", 2), product=5)
#     """
#     kw_pairs: list[_UrlPair] = [(k, v) for k, v in kwargs.items() if v is not None]
#     all_pairs: list[_UrlPair] = list(pairs) + kw_pairs
#     qs = _urlencode_pairs(all_pairs)
#     base = reverse("hr_shop:product_manager")
#     return f"{base}?{qs}" if qs else base
#
#
# # ---------------------------------------------------------------------------
# # Data containers
# # ---------------------------------------------------------------------------
#
#
# @dataclass(frozen=True)
# class SelectionIds:
#     product_id: int | None
#     variant_id: int | None
#     option_type_id: int | None
#     option_value_id: int | None
#
#
# @dataclass
# class Selection:
#     product: Product | None
#     variant: ProductVariant | None
#     option_type: ProductOptionType | None
#     option_value: ProductOptionValue | None
#
#
# @dataclass
# class PostState:
#     action: str
#     mode: str
#     ids: SelectionIds
#     selected_filter_value_ids: list[int] = field(default_factory=list)
#
#
# @dataclass
# class ProductContext:
#     """Everything computed from a selected product + filter state."""
#
#     option_types: QuerySet
#     variants: QuerySet
#     filtered_variants: QuerySet
#     selected_filter_by_type: dict[int, int]
#     selected_filter_value_ids: list[int]
#     selected_variant: ProductVariant | None
#     option_filter_rows: list[dict[str, Any]]
#     has_drives_image_option_type: bool
#     display_variant: ProductVariant | None
#
#
# def _empty_product_context() -> ProductContext:
#     return ProductContext(
#         option_types=ProductOptionType.objects.none(),
#         variants=ProductVariant.objects.none(),
#         filtered_variants=ProductVariant.objects.none(),
#         selected_filter_by_type={},
#         selected_filter_value_ids=[],
#         selected_variant=None,
#         option_filter_rows=[],
#         has_drives_image_option_type=False,
#         display_variant=None
#     )
#
#
# # ---------------------------------------------------------------------------
# # Request parsing
# # ---------------------------------------------------------------------------
#
#
# def _parse_selection_ids(source: QueryDict, *, prefix: str = "") -> SelectionIds:
#     """Parse SelectionIds from a GET or POST dict.
#
#     Pass ``prefix="selected_"`` for POST hidden fields.
#     """
#     return SelectionIds(
#         product_id=_get_int(source, f"{prefix}product"),
#         variant_id=_get_int(source, f"{prefix}variant"),
#         option_type_id=_get_int(source, f"{prefix}option_type"),
#         option_value_id=_get_int(source, f"{prefix}option_value")
#     )
#
#
# def _parse_post_state(post: QueryDict) -> PostState:
#     return PostState(
#         action=post.get("action", "") or "",
#         mode=post.get("mode", "") or "",
#         ids=_parse_selection_ids(post, prefix="selected_"),
#         selected_filter_value_ids=_get_int_list(post, "selected_fv")
#     )
#
#
# # ---------------------------------------------------------------------------
# # Selection hydration
# # ---------------------------------------------------------------------------
#
#
# def _hydrate_selection(ids: SelectionIds) -> Selection:
#     """Fetch model instances for each id, respecting ownership constraints."""
#     product = Product.objects.filter(pk=ids.product_id).first() if ids.product_id else None
#
#     variant = (
#         ProductVariant.objects.filter(pk=ids.variant_id, product=product).first()
#         if product and ids.variant_id
#         else None
#     )
#     option_type = (
#         ProductOptionType.objects.filter(pk=ids.option_type_id, product=product).first()
#         if product and ids.option_type_id
#         else None
#     )
#     option_value = (
#         ProductOptionValue.objects.filter(pk=ids.option_value_id, option_type=option_type).first()
#         if option_type and ids.option_value_id
#         else None
#     )
#
#     return Selection(product=product, variant=variant, option_type=option_type, option_value=option_value)
#
#
# # ---------------------------------------------------------------------------
# # Variant filter helpers
# # ---------------------------------------------------------------------------
#
#
# def _validate_filter_value_ids(value_ids: list[int], product: Product) -> list[int]:
#     """Remove ids that don't belong to the given product, preserving order."""
#     allowed = set(
#         ProductOptionValue.objects.filter(option_type__product=product, active=True).values_list("id", flat=True)
#     )
#     seen: set[int] = set()
#     result: list[int] = []
#     for vid in value_ids:
#         if vid in allowed and vid not in seen:
#             seen.add(vid)
#             result.append(vid)
#     return result
#
#
# def _parse_filter_value_ids(get: QueryDict, product: Product | None) -> list[int]:
#     """Read ``fv`` params, falling back to a comma-separated single value."""
#     raw = get.getlist("fv") or [x.strip() for x in (get.get("fv") or "").split(",") if x.strip()]
#     value_ids = [v for x in raw if (v := _to_int(x)) is not None]
#     if not product or not value_ids:
#         return []
#     return _validate_filter_value_ids(value_ids, product)
#
#
# def _filter_variants(qs: QuerySet[ProductVariant], value_ids: list[int]) -> QuerySet[ProductVariant]:
#     """Narrow a variant queryset to only those matching all given option value ids."""
#     for vid in value_ids:
#         qs = qs.filter(option_values__id=vid)
#     return qs.distinct()
#
#
# def _infer_filters_from_variant(variant: ProductVariant) -> dict[int, int]:
#     """Return ``{option_type_id: option_value_id}`` derived from a variant's option values."""
#     return {ov.option_type_id: ov.id for ov in variant.option_values.select_related("option_type").all()}
#
#
# def _auto_resolve_variant(
#     filtered_variants: QuerySet[ProductVariant],
#     filter_by_type: dict[int, int],
#     current_variant: ProductVariant | None,
#     product: Product,
# ) -> ProductVariant | None:
#     """Return the lone matching variant when filters yield exactly one result."""
#     if not filter_by_type:
#         return None
#     if current_variant and current_variant.product_id == product.id:
#         return None
#     return filtered_variants.first() if filtered_variants.count() == 1 else None
#
#
# # ---------------------------------------------------------------------------
# # Option filter row builder
# # ---------------------------------------------------------------------------
#
#
# def _build_option_filter_rows(
#     option_types: QuerySet[ProductOptionType],
#     selected_filter_by_type: dict[int, int],
#     product_id: int,
# ) -> list[dict[str, Any]]:
#     """Build the option-filter UI data for the template."""
#     rows: list[dict[str, Any]] = []
#
#     for option_type in option_types:
#         active_value_id = selected_filter_by_type.get(option_type.id)
#         row_values: list[dict[str, Any]] = []
#
#         for value in option_type.values.filter(active=True).order_by("position", "name"):
#             next_selected = dict(selected_filter_by_type)
#             if active_value_id == value.id:
#                 next_selected.pop(option_type.id, None)
#             else:
#                 next_selected[option_type.id] = value.id
#
#             fv_pairs: list[_UrlPair] = [("fv", vid) for vid in next_selected.values()]
#             row_values.append({
#                 "id": value.id,
#                 "name": value.name,
#                 "active": active_value_id == value.id,
#                 "url": _manage_url(*fv_pairs, product=product_id)
#             })
#
#         clear_pairs: list[_UrlPair] = [
#             ("fv", ov_id)
#             for ot_id, ov_id in selected_filter_by_type.items()
#             if ot_id != option_type.id
#         ]
#         rows.append({
#             "option_type": option_type,
#             "active_value_id": active_value_id,
#             "values": row_values,
#             "clear_url": _manage_url(*clear_pairs, product=product_id),
#             "manage_url": _manage_url(product=product_id, option_type=option_type.id)
#         })
#
#     return rows
#
#
# # ---------------------------------------------------------------------------
# # Variant tile builder
# # ---------------------------------------------------------------------------
#
#
# def _build_variant_tiles(
#     filtered_variants: QuerySet[ProductVariant],
#     selected_filter_by_type: dict[int, int],
#     selected_variant: ProductVariant | None,
#     product_id: int
# ) -> list[dict[str, Any]]:
#     """Build variant tile data for the template."""
#     fv_base_pairs: list[_UrlPair] = [("fv", vid) for vid in selected_filter_by_type.values()]
#     tiles: list[dict[str, Any]] = []
#
#     for variant in filtered_variants:
#         option_labels = ", ".join(
#             variant.option_values.order_by("option_type__position", "position").values_list("name", flat=True)
#         )
#         tiles.append({
#             "variant": variant,
#             "label": option_labels,
#             "is_selected": bool(selected_variant and selected_variant.id == variant.id),
#             "url": _manage_url(*fv_base_pairs, product=product_id, variant=variant.id)
#         })
#
#     return tiles
#
#
# # ---------------------------------------------------------------------------
# # Product context builder
# # ---------------------------------------------------------------------------
#
#
# def _build_product_context(product: Product, initial_filter_value_ids: list[int], initial_variant: ProductVariant | None) -> ProductContext:
#     """Compute all product-scoped context in one place."""
#     option_types = product.option_types.prefetch_related("values").order_by("position", "name")
#     has_drives_image = option_types.filter(drives_image=True, active=True).exists()
#     display_variant = product.display_variant
#
#     selected_filter_values = (
#         ProductOptionValue.objects.filter(id__in=initial_filter_value_ids, option_type__product=product)
#         .select_related("option_type")
#     )
#     filter_by_type: dict[int, int] = {v.option_type_id: v.id for v in selected_filter_values}
#
#     variants = (
#         product.variants.select_related("image")
#         .prefetch_related("option_values__option_type")
#         .order_by("name")
#     )
#     filtered_variants = _filter_variants(variants, list(filter_by_type.values()))
#     selected_variant = initial_variant
#
#     # Infer filters from the selected variant when no filters are set
#     if selected_variant and selected_variant.product_id == product.id and not filter_by_type:
#         filter_by_type = _infer_filters_from_variant(selected_variant)
#         filtered_variants = _filter_variants(variants, list(filter_by_type.values()))
#
#     # Auto-resolve to a single matching variant
#     if resolved := _auto_resolve_variant(filtered_variants, filter_by_type, selected_variant, product):
#         selected_variant = resolved
#
#     option_filter_rows = _build_option_filter_rows(option_types, filter_by_type, product.id)
#
#     return ProductContext(
#         option_types=option_types,
#         variants=variants,
#         filtered_variants=filtered_variants,
#         selected_filter_by_type=filter_by_type,
#         selected_filter_value_ids=list(filter_by_type.values()),
#         selected_variant=selected_variant,
#         option_filter_rows=option_filter_rows,
#         has_drives_image_option_type=has_drives_image,
#         display_variant=display_variant
#     )
#
#
# # ---------------------------------------------------------------------------
# # Model-behaviour helpers
# # ---------------------------------------------------------------------------
#
#
# def _related_exists_for_soft_delete(obj: object) -> bool:
#     if isinstance(obj, (Product, ProductVariant)):
#         qs = ProductVariant.objects.filter(product=obj) if isinstance(obj, Product) else ProductVariant.objects.filter(pk=obj.pk)
#         return qs.filter(Q(orderitem__isnull=False) | Q(inventory__isnull=False)).exists()
#     if isinstance(obj, ProductOptionType):
#         return ProductOptionValue.objects.filter(option_type=obj, variant_options__isnull=False).exists()
#     if isinstance(obj, ProductOptionValue):
#         return obj.variant_options.exists()
#     return False
#
#
# def _cascade_labels(obj: object) -> list[str]:
#     if isinstance(obj, Product):
#         labels = [f"Variant: {n}" for n in obj.variants.order_by("name").values_list("name", flat=True)]
#         labels += [
#             f"Option Type: {n}"
#             for n in obj.option_types.order_by("position", "name").values_list("name", flat=True)
#         ]
#         return labels
#     if isinstance(obj, ProductOptionType):
#         return [
#             f"Option Value: {n}"
#             for n in obj.values.order_by("position", "name").values_list("name", flat=True)
#         ]
#     return []
#
#
# def _set_inactive(obj: object) -> None:
#     """Soft-delete: mark the object and its children inactive."""
#     if isinstance(obj, Product):
#         obj.active = False
#         obj.save(update_fields=["active"])
#         obj.variants.update(active=False)
#         obj.option_types.update(active=False)
#         ProductOptionValue.objects.filter(option_type__product=obj).update(active=False)
#         return
#
#     if isinstance(obj, ProductOptionType):
#         obj.active = False
#         obj.save(update_fields=["active"])
#         obj.values.update(active=False)
#         return
#
#     if isinstance(obj, (ProductVariant, ProductOptionValue)):
#         obj.active = False
#         obj.save(update_fields=["active"])
#
#
# # ---------------------------------------------------------------------------
# # Delete plan builder
# # ---------------------------------------------------------------------------
#
#
# def _build_delete_plan(mode: str, selection: Selection) -> dict[str, Any] | None:
#     """Return the delete-confirmation context dict, or None if mode isn't a delete."""
#     if not mode.startswith("confirm_delete_"):
#         return None
#
#     delete_kind = mode.removeprefix("confirm_delete_")
#     obj = {
#         "product": selection.product,
#         "variant": selection.variant,
#         "option_type": selection.option_type,
#         "option_value": selection.option_value
#     }.get(delete_kind)
#
#     if obj is None:
#         return None
#
#     return {
#         "kind": delete_kind,
#         "id": obj.id,
#         "label": str(obj),
#         "soft_delete": _related_exists_for_soft_delete(obj),
#         "cascades": _cascade_labels(obj)
#     }
#
#
# # ---------------------------------------------------------------------------
# # Form selection (simplified)
# # ---------------------------------------------------------------------------
#
# F = TypeVar("F")
#
#
# def _pick_form(bound_form: object | None, form_type: Type[F], factory: Callable[[], F | None]) -> F | None:
#     """Prefer the bound (invalid POST) form; otherwise create a new one via factory()."""
#     if isinstance(bound_form, form_type):
#         return bound_form
#     return factory()
#
#
# def _select_forms(
#     bound_form: object | None,
#     mode: str,
#     selection: Selection,
# ) -> tuple[
#     ProductManagerProductForm | None,
#     ProductManagerVariantForm | None,
#     ProductManagerOptionTypeForm | None,
#     ProductManagerOptionValueForm | None,
# ]:
#     """Return the four optional forms for the template."""
#     product = selection.product
#     variant = selection.variant
#     option_type = selection.option_type
#     option_value = selection.option_value
#
#     product_form = _pick_form(
#         bound_form,
#         ProductManagerProductForm,
#         lambda: (
#             ProductManagerProductForm()
#             if mode == "new_product"
#             else ProductManagerProductForm(instance=product)
#             if mode == "edit_product" and product
#             else None
#         ),
#     )
#
#     variant_form = _pick_form(
#         bound_form,
#         ProductManagerVariantForm,
#         lambda: (
#             ProductManagerVariantForm(product=product)
#             if mode == "new_variant" and product
#             else ProductManagerVariantForm(instance=variant, product=product)
#             if product and variant
#             else None
#         ),
#     )
#
#     option_type_form = _pick_form(
#         bound_form,
#         ProductManagerOptionTypeForm,
#         lambda: (
#             ProductManagerOptionTypeForm(product=product)
#             if mode == "new_option_type" and product
#             else ProductManagerOptionTypeForm(instance=option_type, product=product)
#             if product and option_type
#             else None
#         ),
#     )
#
#     option_value_form = _pick_form(
#         bound_form,
#         ProductManagerOptionValueForm,
#         lambda: (
#             ProductManagerOptionValueForm()
#             if mode == "new_option_value" and option_type
#             else ProductManagerOptionValueForm(instance=option_value)
#             if option_value
#             else None
#         ),
#     )
#
#     return product_form, variant_form, option_type_form, option_value_form
#
#
# # ---------------------------------------------------------------------------
# # Individual POST action handlers
# # ---------------------------------------------------------------------------
#
#
# def _handle_save_product(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
#     post = request.POST
#     product_id = _get_int(post, "product_id")
#     instance = Product.objects.filter(pk=product_id).first() if product_id else None
#     form = ProductManagerProductForm(post, instance=instance)
#
#     if form.is_valid():
#         product = form.save()
#         messages.success(request, f"Saved product '{product.name}'.")
#         return redirect(_manage_url(product=product.id)), _hydrate_selection(ids), form
#
#     messages.error(request, "Please correct the product form errors.")
#     return None, Selection(product=instance, variant=None, option_type=None, option_value=None), form
#
#
# def _handle_save_variant(request: HttpRequest, ids: SelectionIds, filter_value_ids: list[int]) -> tuple[HttpResponse | None, Selection, object | None]:
#     post = request.POST
#     product = get_object_or_404(Product, pk=_get_int(post, "product_id"))
#     variant_id = _get_int(post, "variant_id")
#     instance = ProductVariant.objects.filter(pk=variant_id, product=product).first() if variant_id else None
#     form = ProductManagerVariantForm(post, request.FILES, instance=instance, product=product)
#
#     if form.is_valid():
#         variant = form.save(commit=False)
#         variant.product = product
#         if new_image := form.cleaned_data.get("new_image_file"):
#             variant.image = ProductImage.objects.create(image=new_image, alt_text=variant.name or product.name)
#         variant.save()
#         form.save_m2m()
#         messages.success(request, f"Saved variant '{variant.name}'.")
#         fv_pairs: list[_UrlPair] = [("fv", v) for v in filter_value_ids]
#         return redirect(_manage_url(*fv_pairs, product=product.id, variant=variant.id)), _hydrate_selection(ids), form
#
#     messages.error(request, "Please correct the variant form errors.")
#     return None, Selection(product=product, variant=instance, option_type=None, option_value=None), form
#
#
# def _handle_save_option_type(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
#     post = request.POST
#     product = get_object_or_404(Product, pk=_get_int(post, "product_id"))
#     option_type_id = _get_int(post, "option_type_id")
#     instance = ProductOptionType.objects.filter(pk=option_type_id, product=product).first() if option_type_id else None
#     form = ProductManagerOptionTypeForm(post, instance=instance, product=product)
#
#     if form.is_valid():
#         option_type = form.save(commit=False)
#         option_type.product = product
#         option_type.save()
#         messages.success(request, f"Saved option type '{option_type.name}'.")
#         return redirect(_manage_url(product=product.id, option_type=option_type.id)), _hydrate_selection(ids), form
#
#     messages.error(request, "Please correct the option type form errors.")
#     return None, Selection(product=product, variant=None, option_type=instance, option_value=None), form
#
#
# def _handle_save_option_value(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, object | None]:
#     post = request.POST
#     option_type = get_object_or_404(ProductOptionType, pk=_get_int(post, "option_type_id"))
#     value_id = _get_int(post, "option_value_id")
#     instance = ProductOptionValue.objects.filter(pk=value_id, option_type=option_type).first() if value_id else None
#     form = ProductManagerOptionValueForm(post, instance=instance)
#
#     if form.is_valid():
#         option_value = form.save(commit=False)
#         option_value.option_type = option_type
#         option_value.save()
#         messages.success(request, f"Saved option value '{option_value.name}'.")
#         owner_product_id: int = int(option_type.product_id)
#         return (
#             redirect(_manage_url(product=owner_product_id, option_type=option_type.id, option_value=option_value.id)),
#             _hydrate_selection(ids),
#             form
#         )
#
#     messages.error(request, "Please correct the option value form errors.")
#     return None, Selection(product=option_type.product, variant=None, option_type=option_type, option_value=instance), form
#
#
# def _handle_delete_confirmed(request: HttpRequest, ids: SelectionIds) -> tuple[HttpResponse | None, Selection, None]:
#     """Handle delete_confirmed action. Always produces a redirect."""
#     fallback_url = _manage_url(
#         product=ids.product_id,
#         variant=ids.variant_id,
#         option_type=ids.option_type_id,
#         option_value=ids.option_value_id
#     )
#     selection = _hydrate_selection(ids)
#
#     if not request.user.is_superuser:
#         messages.error(request, "Only superusers can delete records.")
#         return redirect(fallback_url), selection, None
#
#     post = request.POST
#     kind = post.get("delete_kind") or ""
#     object_id = _get_int(post, "delete_id")
#
#     model_map: dict[str, type] = {
#         "product": Product,
#         "variant": ProductVariant,
#         "option_type": ProductOptionType,
#         "option_value": ProductOptionValue
#     }
#     model = model_map.get(kind)
#     if model is None or object_id is None:
#         messages.error(request, "Invalid delete request.")
#         return redirect(fallback_url), selection, None
#
#     obj = get_object_or_404(model, pk=object_id)
#     if _related_exists_for_soft_delete(obj):
#         _set_inactive(obj)
#         messages.warning(request, f"{kind.replace('_', ' ').title()} had related records and was set inactive instead.")
#     else:
#         obj.delete()
#         messages.success(request, f"Deleted {kind.replace('_', ' ')}.")
#
#     redirect_url = {
#         "product": _manage_url(),
#         "variant": _manage_url(product=ids.product_id),
#         "option_type": _manage_url(product=ids.product_id),
#         "option_value": _manage_url(product=ids.product_id, option_type=ids.option_type_id)
#     }.get(kind, _manage_url())
#
#     return redirect(redirect_url), selection, None
#
#
# # ---------------------------------------------------------------------------
# # POST dispatcher
# # ---------------------------------------------------------------------------
#
#
# def _apply_post_action(request: HttpRequest, state: PostState) -> tuple[HttpResponse | None, Selection, object | None]:
#     """Dispatch the POST action to the appropriate handler."""
#     dispatch: dict[str, Callable[[], tuple[HttpResponse | None, Selection, object | None]]] = {
#         "save_product": lambda: _handle_save_product(request, state.ids),
#         "save_variant": lambda: _handle_save_variant(request, state.ids, state.selected_filter_value_ids),
#         "save_option_type": lambda: _handle_save_option_type(request, state.ids),
#         "save_option_value": lambda: _handle_save_option_value(request, state.ids),
#         "delete_confirmed": lambda: _handle_delete_confirmed(request, state.ids),
#     }
#     handler = dispatch.get(state.action)
#     if handler is None:
#         return None, _hydrate_selection(state.ids), None
#     return handler()
#
#
# # ---------------------------------------------------------------------------
# # Main view
# # ---------------------------------------------------------------------------
#
#
# @staff_member_required
# def product_manager(request: HttpRequest) -> HttpResponse:
#     bound_form: object | None = None
#
#     if request.method == "POST":
#         state = _parse_post_state(request.POST)
#         redirect_response, selection, bound_form = _apply_post_action(request, state)
#         if redirect_response is not None:
#             return redirect_response
#         mode = state.mode
#         filter_value_ids = state.selected_filter_value_ids
#     else:
#         selection = _hydrate_selection(_parse_selection_ids(request.GET))
#         mode = request.GET.get("mode") or ""
#         filter_value_ids = _parse_filter_value_ids(request.GET, selection.product)
#
#     ctx = _build_product_context(selection.product, filter_value_ids, selection.variant) if selection.product else _empty_product_context()
#
#     # Sync the (possibly auto-resolved) variant back into selection
#     selection.variant = ctx.selected_variant
#
#     is_form_mode = mode in {"new_product", "edit_product", "new_variant", "new_option_type", "new_option_value"}
#     product_form, variant_form, option_type_form, option_value_form = _select_forms(bound_form, mode, selection)
#     delete_plan = _build_delete_plan(mode, selection)
#
#     variant_tiles = (
#         _build_variant_tiles(ctx.filtered_variants, ctx.selected_filter_by_type, selection.variant, selection.product.id)
#         if selection.product
#         else []
#     )
#
#     show_variant_browser = bool(
#         selection.product
#         and not delete_plan
#         and not any([variant_form, option_type_form, option_value_form, product_form])
#         and not is_form_mode
#     )
#     show_variant_image_editor = bool(
#         variant_form
#         and selection.product
#         and (
#             ctx.has_drives_image_option_type
#             or (ctx.display_variant and selection.variant and selection.variant.id == ctx.display_variant.id)
#         )
#     )
#
#     return render(request, "hr_shop/manage/_unified_product_manager.html", {
#         "products": Product.objects.order_by("name"),
#         "variants": ctx.variants,
#         "filtered_variants": ctx.filtered_variants,
#         "option_types": ctx.option_types,
#         "selected_product": selection.product,
#         "selected_variant": selection.variant,
#         "selected_option_type": selection.option_type,
#         "selected_option_value": selection.option_value,
#         "selected_filter_value_ids": ctx.selected_filter_value_ids,
#         "option_filter_rows": ctx.option_filter_rows,
#         "variant_tiles": variant_tiles,
#         "clear_all_filter_url": _manage_url(product=selection.product.id) if selection.product else "",
#         "edit_product_url": _manage_url(product=selection.product.id, mode="edit_product") if selection.product else "",
#         "display_variant": ctx.display_variant,
#         "has_drives_image_option_type": ctx.has_drives_image_option_type,
#         "show_variant_browser": show_variant_browser,
#         "show_variant_image_editor": show_variant_image_editor,
#         "product_form": product_form,
#         "variant_form": variant_form,
#         "option_type_form": option_type_form,
#         "option_value_form": option_value_form,
#         "mode": mode,
#         "delete_plan": delete_plan,
#         "is_superuser": request.user.is_superuser
#     })
