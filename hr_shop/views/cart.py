# hr_shop/views/cart.py

import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from hr_shop.cart import get_cart, Cart, add_to_cart, CartItemNotFoundError
from hr_shop.models import Product


def _merge_hx_trigger(response: HttpResponse, extra: dict) -> HttpResponse:
    """
    Merge `extra` into an existing HX-Trigger header JSON object.
    If none exists, set it.
    """
    existing_raw = response.get('HX-Trigger')
    existing = {}

    if existing_raw:
        try:
            existing = json.loads(existing_raw)
        except (TypeError, ValueError):
            existing = {}

    existing.update(extra)
    response['HX-Trigger'] = json.dumps(existing)
    return response


def _parse_qty_min1(request, default=1):
    try:
        q = int(request.POST.get('quantity', default))
    except (TypeError, ValueError):
        q = default
    return max(q, 1)


def _parse_qty_allow0(request, default=1):
    try:
        q = int(request.POST.get('quantity', default))
    except (TypeError, ValueError):
        q = default
    return max(q, 0)


@require_POST
def add_variant_to_cart(request, variant_slug):
    quantity = _parse_qty_min1(request)
    cart, variant, line_qty = add_to_cart(request, variant_slug, quantity)

    resp = HttpResponse(status=204)
    resp['HX-Trigger'] = json.dumps({
        'showMessage': {'message': f"Added {variant.product.name} x{line_qty} to cart"},
        'updateCart': {'item_count': len(cart)},
    })
    return resp


@require_POST
def add_to_cart_by_options(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    selected_value_ids = []

    for key, value in request.POST.items():
        if key.startswith('opt_') and value:
            try:
                selected_value_ids.append(int(value))
            except (TypeError, ValueError):
                pass

    if not selected_value_ids:
        return HttpResponseBadRequest('No options selected')

    selected_set = set(selected_value_ids)
    variants = product.variants.filter(active=True).prefetch_related('option_values')

    chosen_variant = None
    for variant in variants:
        if variant.option_value_ids_set == selected_set:
            chosen_variant = variant
            break

    if not chosen_variant:
        return HttpResponseBadRequest("No variant for selected options")

    quantity = _parse_qty_min1(request)
    cart, variant, line_qty = add_to_cart(request, chosen_variant.slug, quantity)
    item_count = len(cart)

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showMessage': {
            'message': f'Added {variant.product.name} x{line_qty} to cart'
        },
        'updateCart': {
            'item_count': item_count
        }
    })

    return response


def view_cart(request):
    cart = get_cart(request)
    resp = render(request, 'hr_shop/shop/_view_cart.html', {'cart': list(cart), 'total': cart.total()})
    resp['HX-Trigger'] = json.dumps({'updateCart': {'item_count': len(cart)}})
    return resp


@require_POST
def set_cart_quantity(request, variant_id: int):
    cart = Cart(request)
    quantity = _parse_qty_allow0(request)
    cart.set_quantity(variant_id, quantity)
    return view_cart(request)


@require_POST
def remove_from_cart(request, variant_id: int):
    cart = Cart(request)
    try:
        cart.remove(variant_id)
        msg = 'Removed item from cart.'
    except CartItemNotFoundError:
        msg = 'Item was already removed.'

    resp = view_cart(request)
    _merge_hx_trigger(resp, {'showMessage': {'message': msg}})
    return resp
