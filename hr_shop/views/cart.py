import json

from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from hr_shop.cart import get_cart, Cart, add_to_cart
from hr_shop.models import Product
from hr_core.utils import http


def add_variant_to_cart(request, variant_slug):
    quantity = request.POST.get('quantity', 1)

    cart, variant, line_qty = add_to_cart(request, variant_slug, quantity)

    item_count = len(cart)

    response = HttpResponse(status=204)

    response['HX-Trigger'] = json.dumps({
        'showMessage': {
            'message': f"Added {variant.product.name} x{line_qty} to cart"
        },
        'updateCart': {
            'item_count': item_count
        }
    })

    return response
#
# def add_to_cart(request, variant_slug):
#     quantity = int(request.POST.get('quantity', 1))
#
#     variant = get_object_or_404(ProductVariant, slug=variant_slug)
#
#     cart = get_or_create_cart(request)
#     cart.add(variant, quantity)
#
#     response = HttpResponse(status=204)
#     response['HX-Trigger'] = json.dumps({
#         'showMessage': {'message': f"Added {variant.product.name} to cart"}
#     })
#     return response


# ------------------ CRUD PRODUCT --------------------- #


@require_POST
def add_to_cart_by_options(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    selected_value_ids = []
    for key, value in request.POST.items():
        if key.startswith('opt_') and value:
            try:
                selected_value_ids.append(int(value))
            except ValueError:
                pass

    if not selected_value_ids:
        return HttpResponseBadRequest('No options selected')

    selected_set = set(selected_value_ids)

    variants = product.variants.prefetch_related('option_values')

    chosen_variant = None
    for variant in variants:
        if variant.option_value_ids_set == selected_set:
            chosen_variant = variant
            break

    if not chosen_variant:
        return HttpResponseBadRequest("No variant for selected options")

    quantity = request.POST.get('quantity', 1)

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
    cart_items = list(cart)
    context = {
        'cart': cart_items,
        'total': cart.total()
    }

    if http.is_htmx(request):
        return render(request, 'hr_shop/_view_cart.html', context)

    return render(request, 'hr_shop/view_cart.html', context)


@require_POST
def set_cart_quantity(request, variant_id: int):
    cart = Cart(request)
    quantity = request.POST.get('quantity', 1)
    cart.set_quantity(variant_id, quantity)

    return view_cart(request)


@require_POST
def remove_from_cart(request, variant_id: int):
    cart = Cart(request)
    cart.remove(variant_id)

    return view_cart(request)
