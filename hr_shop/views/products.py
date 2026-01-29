# hr_shop/views/products.py

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from typing import cast

from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from hr_common.utils.http.htmx import hx_trigger
from hr_common.utils.unified_logging import log_event
from hr_shop.models import Product
from hr_shop.utils.image_resolver import (
    PreviewImagePayload,
    resolve_variant_for_values,
    resolve_variant_preview_image_payload,
)

logger = logging.getLogger(__name__)


# ------------------------------
# Small helpers (view-local)
# ------------------------------
def _parse_int_set(values: Iterable[str]) -> set[int]:
    out: set[int] = set()
    for x in values:
        try:
            out.add(int(x))
        except (TypeError, ValueError):
            continue
    return out


def _parse_selected_value_ids_from_post(request: HttpRequest) -> list[int]:
    """
    Extract selected option value IDs from POST keys like opt_<option_type_id>=<value_id>.
    Ignores invalid values instead of hard failing the request.
    """
    selected: list[int] = []
    # noinspection PyArgumentList
    for key, value in request.POST.items():
        if not key.startswith("opt_") or not value:
            continue
        try:
            selected.append(int(value))
        except (TypeError, ValueError):
            continue
    return selected


@require_GET
def get_product_modal_partial(request: HttpRequest, product_slug: str):
    """
    Returns modal HTML intended to swap into #modal-content.

    Assumption: This is an HTMX-driven modal load (SPA flow).
    """
    product = get_object_or_404(Product, slug=product_slug)
    option_types = product.option_types.prefetch_related("values")
    display_variant = product.display_variant

    if display_variant:
        display_values = display_variant.option_values.select_related("option_type")

        # Map each option type to the option value used by the display variant.
        # Template can use opt.default_value_id to preselect defaults.
        mapping = {ov.option_type_id: ov.id for ov in display_values}
        for opt in option_types:
            opt.default_value_id = mapping.get(opt.id)

    variants_data: list[dict[str, object]] = []
    for v in product.variants.filter(active=True).prefetch_related("option_values", "image"):
        img_payload = resolve_variant_preview_image_payload(v, fallback_alt=product.name)

        variants_data.append({
            "id": v.id,
            "slug": v.slug,
            "price": str(v.price),
            "image_url": img_payload["url"],
            "option_value_ids": list(v.option_values.values_list("id", flat=True))
        })

    context = {
        "product": product,
        "option_types": option_types,
        "display_variant": display_variant,
        "variants_json": json.dumps(variants_data)
    }

    return render(request, "hr_shop/shop/_product_detail_modal.html", context)


@require_POST
def update_details_modal(request: HttpRequest, product_slug: str):
    """
    Given a product and posted opt_... values, emit a trigger-only response (204)
    so the client can update UI (image/price/variant slug) without swapping HTML.
    """
    product = get_object_or_404(Product, slug=product_slug)

    selected_value_ids = _parse_selected_value_ids_from_post(request)

    if not selected_value_ids:
        log_event(logger, logging.WARNING, "product.variant_selection.missing_options", product_slug=product_slug)
        # Preserving existing behavior/status: hard 400 is useful for diagnosing
        # client-side selection bugs.
        return HttpResponseBadRequest("No options selected")

    variant = resolve_variant_for_values(product, selected_value_ids)

    # Assumption: variants should have images. If not, we show the placeholder.
    img_payload: PreviewImagePayload = resolve_variant_preview_image_payload(variant, fallback_alt=product.name) if variant else {"url": "", "alt": product.name}

    payload = {
        "variantPreviewUpdated": {
            "image_url": img_payload["url"],
            "price": str(variant.price) if variant else "",
            "variant_slug": variant.slug if variant else ""
        }
    }

    return hx_trigger(payload, status=204)


@require_GET
def product_image_for_selection(request: HttpRequest, product_slug: str):
    """
    Given ?ov=<option_value_id>&ov=<option_value_id>...,
    resolve a preview image URL + alt for the current selection.

    Note: Returns JSON (not modal HTML). Typically used by client JS.
    """
    product = get_object_or_404(Product, slug=product_slug)
    q = cast(QueryDict, request.GET)
    ov_list = q.getlist("ov")
    selected_ids = _parse_int_set(ov_list)

    variant = resolve_variant_for_values(product, selected_ids)

    img_payload: PreviewImagePayload = resolve_variant_preview_image_payload(
        variant,
        fallback_alt=product.name
    )

    return JsonResponse({
        "url": img_payload["url"],
        "alt": img_payload["alt"]
    })
