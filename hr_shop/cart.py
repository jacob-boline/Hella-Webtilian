from hr_shop.models import Product, Price

# SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class CartItemExistsError(Exception):
    def __init__(self, product_id, message="You cannot add an already existing item to a cart. To make changes to an "
                                           "existing item, see <cart.update_item()>"):
        self.product = Product.objects.get(id=product_id)
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.product} -> {self.message}'


class CartItemNotFoundError(Exception):
    def __init__(self, product_id, message="Item must first be present in a cart in order to be updated. See "
                                           "<cart.new_item()>"):
        self.product = Product.objects.get(id=product_id)
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.product} -> {self.message}'


class Cart:

    def __init__(self, request):
        self.session = request.session
        self.session.cart_items = {}
        self.session.cart_id = self.session.session_key
        self.session.set_expiry(3600)
        if not self.session:
            self.session = request.session.create()
            self.session.cart_items = {}
            self.session.cart_id = self.session.session_key
            self.session.set_expiry(3600)

    def __iter__(self):
        for item in self.session.cart_items.all():
            yield item

    def new_item(self, product_id, quantity=1):
        if product_id in self.session.cart_id:
            raise CartItemExistsError(product_id=product_id)
        else:
            if quantity < 0:
                quantity = 0
            self.session.cart_items[product_id] = quantity
            self.session.save()
            message = 'Item added to cart.'
            return message

    def update_item(self, product_id, quantity=None, increment=False, decrement=False):
        if product_id not in self.session.cart_id:
            raise CartItemNotFoundError(product_id=product_id)
        else:
            if not any([quantity, increment, decrement]):
                message= f'Update value not given, your cart has not been modified.'
                return message
            elif quantity:
                if quantity < 0:
                    quantity = 0
                self.session.cart_items[product_id] = quantity
                self.session.save()
            elif increment:
                self.session.cart_items[product_id] += 1
                self.session.save()
            elif decrement:
                if self.session.cart_items[product_id] > 0:
                    self.session.cart_items[product_id] -= 1
                    self.session.save()
            message = 'Cart Updated'
            return message

    def delete_item(self, product_id):
        if product_id not in self.session.cart_items:
            raise CartItemNotFoundError(product_id=product_id)
        else:
            self.session.cart_items.pop(product_id)
            self.session.save()
            message = 'Item removed from cart.'
            return message

    def clear(self):
        self.session.flush()

    def get_item_subtotal(self, product_id):
        quantity = self.session.cart_items[product_id]
        unit_price = Price.objects.get(product__id=product_id).price
        subtotal = (unit_price * quantity)/100
        return subtotal

    def get_cart_subtotal(self):
        cart_subtotal = 0
        for item in self.session.cart_items:
            cart_subtotal += self.get_item_subtotal(item)
        return cart_subtotal

    def num_items(self):
        return self.session.cart_items.len()