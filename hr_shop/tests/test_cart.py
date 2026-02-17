# hr_shop/tests/test_cart.py

# Unit tests for the Cart class in hr_shop/cart.py.
#
# Strategy:
#   - Cart logic that only touches the session (add, remove, set_quantity,
#     clear, __len__, distinct_count) is tested with a mock request and needs
#     no DB access — these are the fastest tests in the suite.
#   - Cart.__iter__ and Cart.total() query ProductVariant from the DB, so
#     those tests use the `db` fixture via the `variant` fixture.

from decimal import Decimal

import pytest

from hr_shop.cart import Cart, CART_SESSION_KEY, CartItemNotFoundError
from hr_shop.tests.conftest import make_session_request
from tests.factories import ProductVariantFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_cart(session_data=None):
    """Return a Cart backed by a mock session."""
    return Cart(make_session_request(session_data))


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestCartInit:
    def test_empty_session_creates_empty_cart(self):
        cart = make_cart()
        assert cart.cart == {}

    def test_existing_session_data_is_loaded(self):
        session = {CART_SESSION_KEY: {"1": {"quantity": 2, "unit_price": "9.99"}}}
        cart = make_cart(session)
        assert "1" in cart.cart


# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------

class TestCartAdd:
    def test_add_new_item(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=1)

        assert str(variant.id) in cart.cart
        assert cart.cart[str(variant.id)]["quantity"] == 1
        assert cart.cart[str(variant.id)]["unit_price"] == str(variant.price)

    def test_add_increments_existing_item(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=2)
        cart.add(variant, quantity=3)

        assert cart.cart[str(variant.id)]["quantity"] == 5

    def test_add_override_sets_exact_quantity(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=5)
        cart.add(variant, quantity=2, override=True)

        assert cart.cart[str(variant.id)]["quantity"] == 2

    def test_add_quantity_below_1_is_clamped_to_1(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=0)

        assert cart.cart[str(variant.id)]["quantity"] == 1

    def test_add_negative_quantity_is_clamped_to_1(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=-5)

        assert cart.cart[str(variant.id)]["quantity"] == 1

    def test_add_marks_session_modified(self, db, variant):
        request = make_session_request()
        cart = Cart(request)
        cart.add(variant, quantity=1)

        assert request.session.modified is True


# ---------------------------------------------------------------------------
# set_quantity()
# ---------------------------------------------------------------------------

class TestCartSetQuantity:
    def test_set_quantity_updates_value(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=1)
        cart.set_quantity(variant.id, 4)

        assert cart.cart[str(variant.id)]["quantity"] == 4

    def test_set_quantity_to_zero_removes_item(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=2)
        cart.set_quantity(variant.id, 0)

        assert str(variant.id) not in cart.cart

    def test_set_quantity_on_missing_item_raises(self, db, variant):
        cart = make_cart()

        with pytest.raises(CartItemNotFoundError):
            cart.set_quantity(variant.id, 3)


# ---------------------------------------------------------------------------
# remove()
# ---------------------------------------------------------------------------

class TestCartRemove:
    def test_remove_existing_item(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=2)
        cart.remove(variant.id)

        assert str(variant.id) not in cart.cart

    def test_remove_missing_item_raises(self, db, variant):
        cart = make_cart()

        with pytest.raises(CartItemNotFoundError):
            cart.remove(variant.id)


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------

class TestCartClear:
    def test_clear_removes_cart_from_session(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=1)
        cart.clear()

        assert CART_SESSION_KEY not in cart.session

    def test_clear_on_empty_cart_is_safe(self):
        cart = make_cart()
        cart.clear()  # should not raise

        assert CART_SESSION_KEY not in cart.session


# ---------------------------------------------------------------------------
# __len__ and distinct_count()
# ---------------------------------------------------------------------------

class TestCartCounts:
    def test_len_returns_total_units(self, db):
        v1 = ProductVariantFactory(price="10.00")
        v2 = ProductVariantFactory(price="20.00")

        cart = make_cart()
        cart.add(v1, quantity=3)
        cart.add(v2, quantity=2)

        assert len(cart) == 5

    def test_len_on_empty_cart_is_zero(self):
        assert len(make_cart()) == 0

    def test_distinct_count_counts_lines_not_units(self, db):
        v1 = ProductVariantFactory(price="10.00")
        v2 = ProductVariantFactory(price="20.00")

        cart = make_cart()
        cart.add(v1, quantity=5)
        cart.add(v2, quantity=1)

        assert cart.distinct_count() == 2


# ---------------------------------------------------------------------------
# __iter__ and total()
# ---------------------------------------------------------------------------

class TestCartIter:
    def test_iter_yields_expected_shape(self, db, variant):
        cart = make_cart()
        cart.add(variant, quantity=2)

        items = list(cart)

        assert len(items) == 1
        item = items[0]
        assert item["variant"] == variant
        assert item["quantity"] == 2
        assert item["unit_price"] == Decimal("19.99")
        assert item["subtotal"] == Decimal("39.98")

    def test_iter_skips_deleted_variants(self, db, variant):
        """
        If a variant ID in the session no longer exists in the DB
        (e.g. it was deleted after being added), __iter__ should skip it
        rather than raise.
        """
        cart = make_cart()
        cart.add(variant, quantity=1)

        variant_id = variant.id
        variant.delete()

        items = list(cart)
        assert items == []

    def test_iter_handles_corrupt_price_gracefully(self, db, variant):
        """
        If unit_price in the session is malformed, __iter__ should fall back
        to 0.00 rather than raising.
        """
        cart = make_cart()
        cart.add(variant, quantity=1)
        # Corrupt the stored price
        cart.cart[str(variant.id)]["unit_price"] = "not-a-number"

        items = list(cart)
        assert items[0]["unit_price"] == Decimal("0.00")

    def test_total_sums_all_line_subtotals(self, db):
        v1 = ProductVariantFactory(price="10.00")
        v2 = ProductVariantFactory(price="5.50")

        cart = make_cart()
        cart.add(v1, quantity=2)   # 20.00
        cart.add(v2, quantity=4)   # 22.00

        assert cart.total() == Decimal("42.00")

    def test_total_on_empty_cart_is_zero(self):
        assert make_cart().total() == Decimal("0.00")
