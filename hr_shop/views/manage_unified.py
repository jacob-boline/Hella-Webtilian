# hr_shop/views/manage_unified.py
from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from hr_shop.forms import ProductManagerOptionTypeForm, ProductManagerOptionValueForm, ProductManagerProductForm, ProductManagerVariantForm
from hr_shop.models import Product, ProductImage, ProductOptionType, ProductOptionValue, ProductVariant


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


def _selection_from_request(request: HttpRequest):
    product_id = _to_int(request.GET.get("product", ""))
    variant_id = _to_int(request.GET.get("variant", ""))
    option_type_id = _to_int(request.GET.get("option_type", ""))
    option_value_id = _to_int(request.GET.get("option_value", ""))

    selected_product = Product.objects.filter(pk=product_id).first() if product_id else None

    selected_variant = None
    if selected_product and variant_id:
        selected_variant = ProductVariant.objects.filter(pk=variant_id, product=selected_product).first()

    selected_option_type = None
    if selected_product and option_type_id:
        selected_option_type = ProductOptionType.objects.filter(pk=option_type_id, product=selected_product).first()

    selected_option_value = None
    if selected_option_type and option_value_id:
        selected_option_value = ProductOptionValue.objects.filter(pk=option_value_id, option_type=selected_option_type).first()

    return {
        "product": selected_product,
        "variant": selected_variant,
        "option_type": selected_option_type,
        "option_value": selected_option_value,
    }


def _selection_from_post(
    selected_product_id: int | None,
    selected_variant_id: int | None,
    selected_option_type_id: int | None,
    selected_option_value_id: int | None,
):
    selected_product = Product.objects.filter(pk=selected_product_id).first() if selected_product_id else None

    selected_variant = None
    if selected_product and selected_variant_id:
        selected_variant = ProductVariant.objects.filter(pk=selected_variant_id, product=selected_product).first()

    selected_option_type = None
    if selected_product and selected_option_type_id:
        selected_option_type = ProductOptionType.objects.filter(pk=selected_option_type_id, product=selected_product).first()

    selected_option_value = None
    if selected_option_type and selected_option_value_id:
        selected_option_value = ProductOptionValue.objects.filter(pk=selected_option_value_id, option_type=selected_option_type).first()

    return {
        "product": selected_product,
        "variant": selected_variant,
        "option_type": selected_option_type,
        "option_value": selected_option_value,
    }


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
    if isinstance(obj, Product):
        obj.active = False
        obj.save(update_fields=["active"])
        obj.variants.update(active=False)
        obj.option_types.update(active=False)
        ProductOptionValue.objects.filter(option_type__product=obj).update(active=False)
        return
    if isinstance(obj, ProductVariant):
        obj.active = False
        obj.save(update_fields=["active"])
        return
    if isinstance(obj, ProductOptionType):
        obj.active = False
        obj.save(update_fields=["active"])
        obj.values.update(active=False)
        return
    if isinstance(obj, ProductOptionValue):
        obj.active = False
        obj.save(update_fields=["active"])


def _object_for_delete(kind: str, object_id: int):
    mapping = {
        "product": Product,
        "variant": ProductVariant,
        "option_type": ProductOptionType,
        "option_value": ProductOptionValue,
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
                "url": _build_manage_url_pairs(*tile_pairs),
            })

    grouped_variant_tiles = defaultdict(list)
    for tile in variant_tiles:
        grouped_variant_tiles[tile["group_label"] or "All"].append(tile)

    clear_all_filter_url = _build_manage_url_pairs(("product", selected_product.id), ("include_disabled", int(include_disabled))) if selected_product else ""
    edit_product_url = _build_manage_url_pairs(("product", selected_product.id), ("panel", "product"), ("mode", "edit_product"), ("include_disabled", int(include_disabled)), *(("fv", v) for v in selected_filter_by_type.values())) if selected_product else ""

    if not selected_product:
        panel_state = "empty"
    elif panel_state not in {"delete", "option_value", "option_type", "variant", "product"}:
        panel_state = "browser"

    return render(
        request,
        "hr_shop/manage/_unified_product_manager.html",
        {
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
            "is_superuser": request.user.is_superuser,
        },
    )
