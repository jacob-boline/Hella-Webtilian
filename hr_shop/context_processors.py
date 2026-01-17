# hr_shop/context_processors.py


from hr_shop.cart import get_cart_item_count


def cart_context(request):
    return {'cart_item_count': get_cart_item_count(request)}

