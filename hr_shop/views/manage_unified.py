# hr_shop/views/manage_unified.py

"""
Product Manager views.

URL map (all under /shop/manage/):
    GET  /             -> product_manager_shell   (full page, first load only)
    GET  /panels/      -> product_manager_panels  (both panels, HTMX swap target)
    POST /product/save/      -> save_product
    POST /variant/save/      -> save_variant
    POST /option-type/save/  -> save_option_type
    POST /option-value/save/ -> save_option_value
    POST /delete/            -> delete_confirmed

All POST views return fresh panels HTML targeting #pmu-panels, plus
HX-Trigger-After-Settle for user-facing messages. Validation failures
return the same panels with the bound form and a 422 status.
"""

from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from hr_common.utils.http.htmx import merge_hx_trigger_after_settle
from hr_common.utils.http.messages import show_message
from hr_shop.forms import (
    ProductManagerOptionTypeForm,
    ProductManagerOptionValueForm,
    ProductManagerProductForm,
    ProductManagerVariantForm,
)
from hr_shop.models import Product, ProductImage, ProductOptionType, ProductOptionValue
from hr_shop.views.manage_helpers import (
    _object_for_delete,
    _parse_filter_value_ids,
    _related_exists_for_soft_delete,
    _resolve_selection,
    _resolve_selection_from_get,
    _to_int,
    build_panels_context, SelectionIds
)

_PANELS_TEMPLATE = "hr_shop/manage/_panels.html"
_SHELL_TEMPLATE = "hr_shop/manage/_shell.html"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_panels(request: HttpRequest, ctx: dict, status: int = 200) -> HttpResponse:
    return render(request, _PANELS_TEMPLATE, ctx, status=status)


# noinspection PyTypeChecker
def _ctx_from_get(request: HttpRequest) -> dict:
    selection = _resolve_selection_from_get(request)
    filter_value_ids = _parse_filter_value_ids(request.GET, selection["product"])
    include_disabled = request.GET.get("include_disabled") == "1"
    panel = request.GET.get("panel", "")
    mode = request.GET.get("mode", "")
    ctx = build_panels_context(selection, filter_value_ids, include_disabled, panel, mode)
    ctx["is_superuser"] = request.user.is_superuser
    return ctx


# ---------------------------------------------------------------------------
# GET views
# ---------------------------------------------------------------------------

@staff_member_required
@require_GET
def product_manager_shell(request: HttpRequest) -> HttpResponse:
    """Full-page shell. Renders panels inline on first load."""
    ctx = _ctx_from_get(request)
    return render(request, _SHELL_TEMPLATE, ctx)


@staff_member_required
@require_GET
def product_manager_panels(request: HttpRequest) -> HttpResponse:
    """ Returns left and right panels of the unified product manager. """
    ctx = _ctx_from_get(request)
    return _render_panels(request, ctx)


# ---------------------------------------------------------------------------
# POST views
# ---------------------------------------------------------------------------

@staff_member_required
@require_POST
def save_product(request: HttpRequest) -> HttpResponse:
    product_id = _to_int(request.POST.get("product_id"))
    instance = Product.objects.filter(pk=product_id).first() if product_id else None
    form = ProductManagerProductForm(request.POST, request.FILES, instance=instance)

    include_disabled = request.POST.get("include_disabled") == "1"

    if form.is_valid():
        product = form.save()
        selection = _resolve_selection(SelectionIds(product_id=product.id)).to_dict()
        ctx = build_panels_context(selection, [], include_disabled, "product", "")
        ctx["is_superuser"] = request.user.is_superuser
        resp = _render_panels(request, ctx)
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(f"Saved product '{product.name}'.")})

    selection = _resolve_selection(SelectionIds(product_id=product_id)).to_dict()
    filter_value_ids = _parse_filter_value_ids(request.POST, selection["product"])
    ctx = build_panels_context(selection, filter_value_ids, include_disabled, "product", "", form)
    ctx["is_superuser"] = request.user.is_superuser
    resp = _render_panels(request, ctx, status=422)
    return merge_hx_trigger_after_settle(resp, {"showMessage": show_message("Please correct the product form errors.")})


@staff_member_required
@require_POST
def save_variant(request: HttpRequest) -> HttpResponse:
    product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id")))
    variant_id = _to_int(request.POST.get("variant_id"))
    instance = product.variants.filter(pk=variant_id).first() if variant_id else None
    form = ProductManagerVariantForm(request.POST, request.FILES, instance=instance, product=product)

    include_disabled = request.POST.get("include_disabled") == "1"
    filter_value_ids = _parse_filter_value_ids(request.POST, product)

    if form.is_valid():
        variant = form.save(commit=False)
        variant.product = product
        new_image_file = form.cleaned_data.get("new_image_file")
        if new_image_file:
            variant.image = ProductImage.objects.create(image=new_image_file, alt_text=variant.name or product.name)
        variant.save()
        form.save_m2m()
        selection = _resolve_selection(SelectionIds(product_id=product.id, variant_id=variant.id)).to_dict()
        ctx = build_panels_context(selection, filter_value_ids, include_disabled, "variant", "")
        ctx["is_superuser"] = request.user.is_superuser
        resp = _render_panels(request, ctx)
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(f"Saved variant '{variant.name}'.")})

    selection = _resolve_selection(SelectionIds(product_id=product.id, variant_id=variant_id)).to_dict()
    ctx = build_panels_context(selection, filter_value_ids, include_disabled, "variant", "", form)
    ctx["is_superuser"] = request.user.is_superuser
    resp = _render_panels(request, ctx, status=422)
    return merge_hx_trigger_after_settle(resp, {"showMessage": show_message("Please correct the variant form errors.")})


@staff_member_required
@require_POST
def save_option_type(request: HttpRequest) -> HttpResponse:
    product = get_object_or_404(Product, pk=_to_int(request.POST.get("product_id")))
    option_type_id = _to_int(request.POST.get("option_type_id"))
    instance = (
        ProductOptionType.objects.filter(pk=option_type_id, product=product).first()
        if option_type_id else None
    )
    form = ProductManagerOptionTypeForm(request.POST, instance=instance, product=product)

    include_disabled = request.POST.get("include_disabled") == "1"
    filter_value_ids = _parse_filter_value_ids(request.POST, product)

    if form.is_valid():
        option_type = form.save(commit=False)
        option_type.product = product
        option_type.save()
        selection = _resolve_selection(SelectionIds(product_id=product.id, option_type_id=option_type.id)).to_dict()
        ctx = build_panels_context(selection, filter_value_ids, include_disabled, "option_type", "")
        ctx["is_superuser"] = request.user.is_superuser
        resp = _render_panels(request, ctx)
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(f"Saved option type '{option_type.name}'.")})

    selection = _resolve_selection(SelectionIds(product_id=product.id, option_type_id=option_type_id)).to_dict()
    ctx = build_panels_context(selection, filter_value_ids, include_disabled, "option_type", "", form)
    ctx["is_superuser"] = request.user.is_superuser
    resp = _render_panels(request, ctx, status=422)
    return merge_hx_trigger_after_settle(resp, {"showMessage": show_message("Please correct the option type form errors.")})


@staff_member_required
@require_POST
def save_option_value(request: HttpRequest) -> HttpResponse:
    option_type = get_object_or_404(ProductOptionType, pk=_to_int(request.POST.get("option_type_id")))
    value_id = _to_int(request.POST.get("option_value_id"))
    instance = (
        ProductOptionValue.objects.filter(pk=value_id, option_type=option_type).first()
        if value_id else None
    )
    form = ProductManagerOptionValueForm(request.POST, instance=instance)

    include_disabled = request.POST.get("include_disabled") == "1"
    filter_value_ids = _parse_filter_value_ids(request.POST, option_type.product)

    if form.is_valid():
        option_value = form.save(commit=False)
        option_value.option_type = option_type
        option_value.save()
        selection = _resolve_selection(SelectionIds(product_id=int(option_type.product_id), option_type_id=option_type.id, option_value_id=option_value.id)).to_dict()
        ctx = build_panels_context(selection, filter_value_ids, include_disabled, "option_value", "")
        ctx["is_superuser"] = request.user.is_superuser
        resp = _render_panels(request, ctx)
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(f"Saved option value '{option_value.name}'.")})

    selection = _resolve_selection(SelectionIds(product_id=int(option_type.product_id), option_type_id=option_type.id, option_value_id=value_id)).to_dict()
    ctx = build_panels_context(selection, filter_value_ids, include_disabled, "option_value", "", form)
    ctx["is_superuser"] = request.user.is_superuser
    resp = _render_panels(request, ctx, status=422)
    return merge_hx_trigger_after_settle(resp, {"showMessage": show_message("Please correct the option value form errors.")})


# noinspection PyTypeChecker
@staff_member_required
@require_POST
def delete_confirmed(request: HttpRequest) -> HttpResponse:
    product_id = _to_int(request.POST.get("product_id"))
    include_disabled = request.POST.get("include_disabled") == "1"

    def _panels_with_msg(message: str, pid=product_id, status: int = 200) -> HttpResponse:
        selection = _resolve_selection(SelectionIds(product_id=pid)).to_dict()
        fv_ids = _parse_filter_value_ids(request.POST, selection["product"])
        ctx = build_panels_context(selection, fv_ids, include_disabled, "browser", "")
        ctx["is_superuser"] = request.user.is_superuser
        resp = _render_panels(request, ctx, status=status)
        return merge_hx_trigger_after_settle(resp, {"showMessage": show_message(message)})

    if not request.user.is_superuser:
        return _panels_with_msg("Only superusers can delete records.", status=403)

    kind = request.POST.get("delete_kind", "")
    object_id = _to_int(request.POST.get("delete_id"))
    obj = _object_for_delete(kind, object_id)

    if obj is None:
        return _panels_with_msg("Invalid delete request.", status=400)

    soft = _related_exists_for_soft_delete(obj)
    if soft:
        obj.deactivate()
        msg = f"{kind.replace('_', ' ').title()} had related records and was set inactive."
    else:
        obj.delete()
        msg = f"Deleted {kind.replace('_', ' ')}."

    # After deleting a product clear product selection; otherwise stay on product
    new_product_id = None if kind == "product" else product_id
    return _panels_with_msg(msg, pid=new_product_id)
