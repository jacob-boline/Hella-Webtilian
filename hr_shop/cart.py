# hr_shop/cart.py

from decimal import Decimal

from django.shortcuts import get_object_or_404

from hr_shop.models import ProductVariant


CART_SESSION_KEY = "hr_shop_cart"


class CartItemExistsError(Exception):
    def __init__(self, variant_id, message=None):
        self.variant = ProductVariant.objects.get(id=variant_id)
        self.message = (
            message
            or "You cannot add an already existing item this way. "
               "Use <cart.set_quantity()> or <cart.add(override=True)> instead."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"{self.variant} -> {self.message}"


class CartItemNotFoundError(Exception):
    def __init__(self, variant_id, message=None):
        self.variant = ProductVariant.objects.get(id=variant_id)
        self.message = (
            message
            or "Item must be present in the cart before it can be updated. "
               "Use <cart.add()> first."
        )
        super().__init__(self.message)

    def __str__(self):
        return f"{self.variant} -> {self.message}"


class Cart:
    """
    Session-backed cart.

    Session structure:

        request.session['hr_shop_cart'] = {
            "<variant_id>": {
                "quantity": int,
                "price": "9.99",           # string for JSON safety
            },
            ...
        }
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[CART_SESSION_KEY] = cart
        self.cart = cart

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def __iter__(self):
        """
        Yield cart items with attached ProductVariant objects and line totals.
        """
        variant_ids = [int(v_id) for v_id in self.cart.keys()]
        variants = ProductVariant.objects.filter(id__in=variant_ids).select_related("product")

        variants_map = {v.id: v for v in variants}
        for variant_id_str, data in self.cart.items():
            variant_id = int(variant_id_str)
            variant = variants_map.get(variant_id)
            if not variant:
                continue

            quantity = data.get("quantity", 0)
            price = Decimal(data.get("price", "0.00"))
            yield {
                "variant": variant,
                "product": variant.product,
                "quantity": quantity,
                "unit_price": price,
                "subtotal": price * quantity,
            }

    def __len__(self):
        """Total quantity of items in the cart."""
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, variant, quantity=1, override=False):
        """
        Add a variant to the cart or update its quantity.

        - variant: ProductVariant instance
        - quantity: how many to add
        - override: if True, set quantity exactly; if False, increment
        """
        quantity = int(quantity) if quantity is not None else 1
        if quantity < 1:
            quantity = 1

        key = str(variant.id)
        line = self.cart.get(key)

        if line is None:
            self.cart[key] = {
                "quantity": quantity,
                "price": str(variant.price),
            }
        else:
            if override:
                self.cart[key]["quantity"] = quantity
            else:
                self.cart[key]["quantity"] += quantity

        self.save()

    def set_quantity(self, variant_id, quantity):
        """
        Hard-set a variant's quantity in the cart.
        """
        key = str(variant_id)
        if key not in self.cart:
            raise CartItemNotFoundError(variant_id)

        quantity = int(quantity)
        if quantity < 0:
            quantity = 0

        if quantity == 0:
            self.remove(variant_id)
        else:
            self.cart[key]["quantity"] = quantity
            self.save()

    def remove(self, variant_id):
        key = str(variant_id)
        if key not in self.cart:
            raise CartItemNotFoundError(variant_id)

        self.cart.pop(key)
        self.save()

    def clear(self):
        self.session.pop(CART_SESSION_KEY, None)
        self.session.modified = True

    def total(self):
        """
        Total cart value as Decimal.
        """
        from decimal import Decimal
        total = Decimal("0.00")
        for item in self:
            total += item["subtotal"]
        return total


def add_to_cart(request, variant_slug, quantity=1, *, override=False):
    """
    Helper used by the view: resolve a variant by slug and add it to the cart.

    Returns (cart, variant, line_quantity).
    """
    variant = get_object_or_404(ProductVariant, slug=variant_slug)
    cart = Cart(request)
    cart.add(variant, quantity=quantity, override=override)

    # quantity in cart for this variant after operation
    line = cart.cart[str(variant.id)]
    return cart, variant, line["quantity"]
