# hr_shop/views/manage_unified.py
from __future__ import annotations

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from hr_shop.forms import ProductManagerOptionTypeForm, ProductManagerOptionValueForm, ProductManagerProductForm, ProductManagerVariantForm
from hr_shop.models import Product, ProductOptionType, ProductOptionValue, ProductVariant


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


def _selection_from_request(request: HttpRequest):
    product_id = _to_int(request.GET.get("product"))
    variant_id = _to_int(request.GET.get("variant"))
    option_type_id = _to_int(request.GET.get("option_type"))
    option_value_id = _to_int(request.GET.get("option_value"))

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

    if not selected_variant:
        selected_option_type = None
        selected_option_value = None
    if not selected_option_type:
        selected_option_value = None

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


@staff_member_required
def product_manager(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        action = request.POST.get("action", "")

        selected_product_id = _to_int(request.POST.get("selected_product"))
        selected_variant_id = _to_int(request.POST.get("selected_variant"))
        selected_option_type_id = _to_int(request.POST.get("selected_option_type"))
        selected_option_value_id = _to_int(request.POST.get("selected_option_value"))

        if action == "save_product":
            product_id = _to_int(request.POST.get("product_id"))
            instance = Product.objects.filter(pk=product_id).first() if product_id else None
            form = ProductManagerProductForm(request.POST, instance=instance)
            if form.is_valid():
                product = form.save()
                messages.success(request, f"Saved product '{product.name}'.")
                return redirect(_build_manage_url(product=product.id))
            messages.error(request, "Please correct the product form errors.")
            selected_product = instance
            selected_variant_id = None
            selected_option_type_id = None
            selected_option_value_id = None
        elif action == "save_variant":
            product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id")))
            variant_id = _to_int(request.POST.get("variant_id"))
            instance = ProductVariant.objects.filter(pk=variant_id, product=product).first() if variant_id else None
            form = ProductManagerVariantForm(request.POST, request.FILES, instance=instance, product=product)
            if form.is_valid():
                variant = form.save(commit=False)
                variant.product = product
                variant.save()
                form.save_m2m()
                messages.success(request, f"Saved variant '{variant.name}'.")
                return redirect(_build_manage_url(product=product.id, variant=variant.id))
            messages.error(request, "Please correct the variant form errors.")
            selected_product = product
            selected_product_id = product.id
            selected_variant_id = variant_id
            selected_option_type_id = None
            selected_option_value_id = None
        elif action == "save_option_type":
            product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id")))
            option_type_id = _to_int(request.POST.get("option_type_id"))
            instance = ProductOptionType.objects.filter(pk=option_type_id, product=product).first() if option_type_id else None
            form = ProductManagerOptionTypeForm(request.POST, instance=instance, product=product)
            if form.is_valid():
                option_type = form.save(commit=False)
                option_type.product = product
                option_type.save()
                messages.success(request, f"Saved option type '{option_type.name}'.")
                return redirect(_build_manage_url(product=product.id, variant=selected_variant_id, option_type=option_type.id))
            messages.error(request, "Please correct the option type form errors.")
            selected_product = product
            selected_product_id = product.id
            selected_option_type_id = option_type_id
        elif action == "save_option_value":
            option_type = get_object_or_404(ProductOptionType, pk=_to_int(request.POST.get("option_type_id")))
            value_id = _to_int(request.POST.get("option_value_id"))
            instance = ProductOptionValue.objects.filter(pk=value_id, option_type=option_type).first() if value_id else None
            form = ProductManagerOptionValueForm(request.POST, instance=instance)
            if form.is_valid():
                option_value = form.save(commit=False)
                option_value.option_type = option_type
                option_value.save()
                messages.success(request, f"Saved option value '{option_value.name}'.")
                return redirect(
                    _build_manage_url(
                        product=option_type.product_id,
                        variant=selected_variant_id,
                        option_type=option_type.id,
                        option_value=option_value.id,
                    )
                )
            messages.error(request, "Please correct the option value form errors.")
            selected_product = option_type.product
            selected_product_id = option_type.product_id
            selected_option_type_id = option_type.id
            selected_option_value_id = value_id
        elif action == "delete_confirmed":
            if not request.user.is_superuser:
                messages.error(request, "Only superusers can delete records.")
                return redirect(_build_manage_url(product=selected_product_id, variant=selected_variant_id, option_type=selected_option_type_id, option_value=selected_option_value_id))

            kind = request.POST.get("delete_kind")
            object_id = _to_int(request.POST.get("delete_id"))
            obj = _object_for_delete(kind, object_id)
            if obj is None:
                messages.error(request, "Invalid delete request.")
                return redirect(_build_manage_url(product=selected_product_id, variant=selected_variant_id, option_type=selected_option_type_id, option_value=selected_option_value_id))

            should_soft_delete = _related_exists_for_soft_delete(obj)
            if should_soft_delete:
                _set_inactive(obj)
                messages.warning(request, f"{kind.replace('_', ' ').title()} had related records and was set inactive instead.")
            else:
                obj.delete()
                messages.success(request, f"Deleted {kind.replace('_', ' ')}.")

            if kind == "product":
                return redirect(_build_manage_url())
            if kind == "variant":
                return redirect(_build_manage_url(product=selected_product_id))
            if kind == "option_type":
                return redirect(_build_manage_url(product=selected_product_id, variant=selected_variant_id))
            if kind == "option_value":
                return redirect(_build_manage_url(product=selected_product_id, variant=selected_variant_id, option_type=selected_option_type_id))

        else:
            form = None
            selected_product = Product.objects.filter(pk=selected_product_id).first() if selected_product_id else None

        selection = {
            "product": selected_product if 'selected_product' in locals() else Product.objects.filter(pk=selected_product_id).first() if selected_product_id else None,
            "variant": ProductVariant.objects.filter(pk=selected_variant_id).first() if selected_variant_id else None,
            "option_type": ProductOptionType.objects.filter(pk=selected_option_type_id).first() if selected_option_type_id else None,
            "option_value": ProductOptionValue.objects.filter(pk=selected_option_value_id).first() if selected_option_value_id else None,
        }
        mode = request.POST.get("mode")
    else:
        selection = _selection_from_request(request)
        mode = request.GET.get("mode", "")
        form = None

    selected_product = selection["product"]
    selected_variant = selection["variant"]
    selected_option_type = selection["option_type"]
    selected_option_value = selection["option_value"]

    products = Product.objects.order_by("name")
    variants = selected_product.variants.order_by("name") if selected_product else ProductVariant.objects.none()
    option_types = selected_product.option_types.order_by("position", "name") if selected_product and selected_variant else ProductOptionType.objects.none()
    option_values = selected_option_type.values.order_by("position", "name") if selected_option_type else ProductOptionValue.objects.none()

    if form is not None and isinstance(form, ProductManagerProductForm):
        product_form = form
    elif mode == "new_product":
        product_form = ProductManagerProductForm()
    else:
        product_form = ProductManagerProductForm(instance=selected_product) if selected_product else None

    if form is not None and isinstance(form, ProductManagerVariantForm):
        variant_form = form
    elif mode == "new_variant" and selected_product:
        variant_form = ProductManagerVariantForm(product=selected_product)
    elif selected_variant:
        variant_form = ProductManagerVariantForm(instance=selected_variant, product=selected_product)
    else:
        variant_form = None

    if form is not None and isinstance(form, ProductManagerOptionTypeForm):
        option_type_form = form
    elif mode == "new_option_type" and selected_product:
        option_type_form = ProductManagerOptionTypeForm(product=selected_product)
    elif selected_option_type:
        option_type_form = ProductManagerOptionTypeForm(instance=selected_option_type, product=selected_product)
    else:
        option_type_form = None

    if form is not None and isinstance(form, ProductManagerOptionValueForm):
        option_value_form = form
    elif mode == "new_option_value" and selected_option_type:
        option_value_form = ProductManagerOptionValueForm()
    elif selected_option_value:
        option_value_form = ProductManagerOptionValueForm(instance=selected_option_value)
    else:
        option_value_form = None

    delete_plan = None
    delete_kind = ""
    if mode.startswith("confirm_delete_"):
        delete_kind = mode.replace("confirm_delete_", "")
        selected_map = {
            "product": selected_product,
            "variant": selected_variant,
            "option_type": selected_option_type,
            "option_value": selected_option_value,
        }
        obj = selected_map.get(delete_kind)
        if obj is not None:
            delete_plan = {
                "kind": delete_kind,
                "id": obj.id,
                "label": str(obj),
                "soft_delete": _related_exists_for_soft_delete(obj),
                "cascades": _cascade_labels(obj),
            }

    return render(
        request,
        "hr_shop/manage/_unified_product_manager.html",
        {
            "products": products,
            "variants": variants,
            "option_types": option_types,
            "option_values": option_values,
            "selected_product": selected_product,
            "selected_variant": selected_variant,
            "selected_option_type": selected_option_type,
            "selected_option_value": selected_option_value,
            "product_form": product_form,
            "variant_form": variant_form,
            "option_type_form": option_type_form,
            "option_value_form": option_value_form,
            "mode": mode,
            "delete_plan": delete_plan,
            "is_superuser": request.user.is_superuser,
        },
    )
