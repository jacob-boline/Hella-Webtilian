# from cart.cart import Cart
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from hr_shop.cart import Cart
from .models import Product
import stripe
import urllib.parse
import json
import logging

log = logging.getLogger(__name__)


def clear_cart(request):
    pass


def product_gallery(request):
    # import stripe
    # stripe.api_key = stripe_test_private_key
    #
    # def get_all_stripe_objects(stripe_listable):
    #     objects = []
    #     get_more = True
    #     starting_after = None
    #     while get_more:
    #         # stripe.Customer implements ListableAPIResource(APIResource):
    #         resp = stripe_listable.list(limit=100, starting_after=starting_after)
    #         objects.extend(resp['data'])
    #         get_more = resp['has_more']
    #         if len(resp['data']) > 0:
    #             starting_after = resp['data'][-1]['id']
    #     return objects
    #
    # all_stripe_products = get_all_stripe_objects(stripe.Product)
    # all_stripe_prices = get_all_stripe_objects(stripe.Price)

    cart = Cart(request)
    # prices = stripe.Price.search(query="active:'true'", expand=['data.product'])  # product data is attainable by expansion on prices data, though not prices via product expansion
    prices = stripe.Price.list(expand=['data.product'])
    # log.info(msg=f'prices object in product_gallery = {prices}')
    return render(request, 'hr_shop/product_gallery.html', {'prices': prices, 'cart': cart})


def product_detail(request, encoded_name):
    cart = Cart(request)
    decoded_name = urllib.parse.unquote_plus(encoded_name)
    product = stripe.Product.search(query=f"name:'{decoded_name}'", expand=['data.default_price'])
    unit_price = float(product.default_price.unit_amount_decimal)/100
    return render(request, 'hr_shop/product_detail.html', {'product': product, 'cart': cart, 'unit_price': unit_price})


def cart_detail(request):
    cart = Cart(request)
    cart_items = cart.session.cart_items.all()
    for item in cart_items:
        item['quantity'] = cart_items[item.id]
        item['subtotal'] = cart.get_item_subtotal(item.id)
    cart.session.save()
    return render (request, 'hr_shop/view_cart.html', {'cart_items': cart_items, 'cart': cart})


def add_product(request, encoded_name, quantity=1):
    cart = Cart(request)
    decoded_name = urllib.parse.unquote_plus(encoded_name)
    product = stripe.Product.search(query=f"name:'{decoded_name}'", expand=['data.default_price'])
    result = cart.new_item(product_id=product.id, quantity=quantity)
    messages.info(request, message=result)
    response = redirect(request, 'product_gallery', {'cart': cart})
    headers_dict = {'cartChanged': None}
    response.headers['HX-Trigger'] = json.dumps(headers_dict)
    return response


def update_product(request, product_id, quantity=None, increment=False, decrement=False):
    cart = Cart(request)
    result = cart.update_item(product_id=product_id, quantity=quantity, increment=increment, decrement=decrement)
    messages.info(request, message=result)
    return redirect(request, 'cart_detail', {'cart': cart})


def remove_product(request, product_id):
    cart = Cart(request)
    result = cart.delete_item(product_id=product_id)
    messages.info(request, message=result)
    return redirect(request, 'cart_detail', {'cart': cart})


def checkout(request):
    cart = Cart(request)
    return redirect(request, 'payment_entry', {'cart': cart})


def cart_counter(request):
    cart = Cart(request)
    item_count = cart.num_items()
    return render(request, 'hr_shop/cart_counter.html', {'item_count': item_count})
