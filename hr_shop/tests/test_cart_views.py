# hr_shop/tests/test_cart_views.py

# Integration tests for the cart views in hr_shop/views/cart.py.
#
# Strategy:
#   - All tests use Django's test `client`, which gives us a real session
#     and real HTTP request/response cycle.
#   - We're not testing template rendering in detail — we assert on response
#     status codes, HX-Trigger headers, and session state.
#   - The idempotency tests use the X-Idempotency-Key header, which the
#     views read to prevent double-add on rapid repeat requests.

import json

from hr_shop.cart import CART_SESSION_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cart_session(client):
    """Return the raw cart dict from the test client's session."""
    return client.session.get(CART_SESSION_KEY, {})


def add_url(variant):
    return f"/shop/cart/add/{variant.slug}/"


def update_url(variant):
    return f"/shop/cart/update/{variant.id}/"


def remove_url(variant):
    return f"/shop/cart/remove/{variant.id}/"


# ---------------------------------------------------------------------------
# add_variant_to_cart
# ---------------------------------------------------------------------------

class TestAddVariantToCart:
    def test_adds_variant_and_returns_204(self, client, variant):
        resp = client.post(add_url(variant))

        assert resp.status_code == 204
        assert str(variant.id) in cart_session(client)

    def test_adds_correct_quantity(self, client, variant):
        client.post(add_url(variant), {"quantity": "3"})

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 3

    def test_repeated_add_increments_quantity(self, client, variant):
        client.post(add_url(variant), {"quantity": "2"})
        client.post(add_url(variant), {"quantity": "2"})

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 4

    def test_hx_trigger_header_contains_update_cart(self, client, variant):
        resp = client.post(add_url(variant))

        trigger = json.loads(resp.get("HX-Trigger", "{}"))
        assert "updateCart" in trigger

    def test_inactive_variant_returns_404(self, client, inactive_variant):
        resp = client.post(add_url(inactive_variant))

        assert resp.status_code == 404

    def test_idempotency_key_prevents_double_add(self, client, variant):
        """
        Two rapid POSTs with the same X-Idempotency-Key should only add once.
        """
        headers = {"HTTP_X_IDEMPOTENCY_KEY": "test-idem-key-001"}

        client.post(add_url(variant), **headers)
        client.post(add_url(variant), **headers)

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 1

    def test_different_idempotency_keys_both_add(self, client, variant):
        """
        Two POSTs with different idempotency keys should both increment.
        """
        client.post(add_url(variant), HTTP_X_IDEMPOTENCY_KEY="key-aaa")
        client.post(add_url(variant), HTTP_X_IDEMPOTENCY_KEY="key-bbb")

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 2


# ---------------------------------------------------------------------------
# set_cart_quantity
# ---------------------------------------------------------------------------

class TestSetCartQuantity:
    def test_updates_quantity_in_session(self, client, variant):
        client.post(add_url(variant), {"quantity": "1"})
        client.post(update_url(variant), {"quantity": "5"})

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 5

    def test_setting_quantity_to_zero_removes_item(self, client, variant):
        client.post(add_url(variant), {"quantity": "2"})
        client.post(update_url(variant), {"quantity": "0"})

        assert str(variant.id) not in cart_session(client)

    def test_item_not_in_cart_returns_400(self, client, variant):
        """Setting qty on an item that was never added should return 400."""
        resp = client.post(update_url(variant), {"quantity": "3"})

        assert resp.status_code == 400

    def test_item_not_in_cart_with_qty_zero_is_idempotent(self, client, variant):
        """
        If qty=0 and the item isn't in the cart (already removed / never added),
        the view treats it as a no-op rather than an error — graceful handling
        for multi-tab scenarios where the user removed it in another tab.
        """
        resp = client.post(update_url(variant), {"quantity": "0"})

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# remove_from_cart
# ---------------------------------------------------------------------------

class TestRemoveFromCart:
    def test_removes_item_from_session(self, client, variant):
        client.post(add_url(variant), {"quantity": "2"})
        client.post(remove_url(variant))

        assert str(variant.id) not in cart_session(client)

    def test_removing_absent_item_is_idempotent(self, client, variant):
        """
        Removing an item that's no longer in the cart (e.g. already removed
        in another tab) should return 200, not 400 or 500.
        """
        resp = client.post(remove_url(variant))

        assert resp.status_code == 200

    def test_remove_returns_updated_cart_html(self, client, db):
        """
        remove_from_cart renders the cart partial — confirm we get HTML back,
        not an empty 204.
        """
        v1 = ProductVariantFactory(price="10.00")
        v2 = ProductVariantFactory(price="20.00")

        client.post(add_url(v1))
        client.post(add_url(v2))
        resp = client.post(remove_url(v1))

        assert resp.status_code == 200
        assert b"html" in resp.content.lower() or len(resp.content) > 0


# ---------------------------------------------------------------------------
# add_to_cart_by_options
# ---------------------------------------------------------------------------
#
# This view resolves a variant by matching selected option value IDs against
# active variants on the product. The POST body uses keys like opt_<anything>
# with the ProductOptionValue ID as the value.
#
# Setup for these tests: we need a Product, a ProductVariant, and the
# ProductOptionType + ProductOptionValue rows that define the variant's
# combination. We wire them up with ProductVariantOption (the through table).

from hr_shop.models import ProductOptionType, ProductOptionValue, ProductVariantOption
from tests.factories import ProductFactory, ProductVariantFactory


def options_url(product):
    return f"/shop/cart/add/by-options/{product.slug}/"


def make_product_with_option_variant(price="19.99"):
    """
    Build a Product with one variant linked to one option value (e.g. Color: Black).
    Returns (product, variant, option_value) so tests can POST opt_color=<option_value.id>.
    """
    product = ProductFactory()
    variant = ProductVariantFactory(product=product, price=price)

    option_type = ProductOptionType.objects.create(product=product, name="Color", code="color")
    option_value = ProductOptionValue.objects.create(option_type=option_type, name="Black", code="black")
    ProductVariantOption.objects.create(variant=variant, option_value=option_value)

    return product, variant, option_value


class TestAddToCartByOptions:
    def test_adds_correct_variant_and_returns_204(self, client, db):
        product, variant, option_value = make_product_with_option_variant()

        resp = client.post(options_url(product), {f"opt_color": option_value.id})

        assert resp.status_code == 204
        assert str(variant.id) in cart_session(client)

    def test_adds_correct_quantity(self, client, db):
        product, variant, option_value = make_product_with_option_variant()

        client.post(options_url(product), {"opt_color": option_value.id, "quantity": "3"})

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 3

    def test_no_options_in_post_returns_400(self, client, db):
        """
        POST with no opt_* keys at all should return 400 — the view can't
        resolve a variant without any selected values.
        """
        product = ProductFactory()

        resp = client.post(options_url(product), {})

        assert resp.status_code == 400

    def test_nonexistent_product_returns_404(self, client, db):
        resp = client.post("/shop/cart/add/by-options/no-such-product/", {"opt_x": "1"})

        assert resp.status_code == 404

    def test_no_matching_variant_returns_400(self, client, db):
        """
        Valid option value IDs but no variant matches that exact combination
        should return 400, not 500.
        """
        product, variant, option_value = make_product_with_option_variant()
        # Pass a made-up value ID that doesn't correspond to any variant
        resp = client.post(options_url(product), {"opt_color": option_value.id + 9999})

        assert resp.status_code == 400

    def test_inactive_variant_is_not_matched(self, client, db):
        """
        The view filters variants by active=True. An inactive variant's option
        combination should not be matchable.
        """
        product = ProductFactory()
        variant = ProductVariantFactory(product=product, active=False)

        option_type = ProductOptionType.objects.create(product=product, name="Color", code="color")
        option_value = ProductOptionValue.objects.create(option_type=option_type, name="Black", code="black")
        ProductVariantOption.objects.create(variant=variant, option_value=option_value)

        resp = client.post(options_url(product), {"opt_color": option_value.id})

        assert resp.status_code == 400

    def test_hx_trigger_header_contains_update_cart(self, client, db):
        import json
        product, variant, option_value = make_product_with_option_variant()

        resp = client.post(options_url(product), {"opt_color": option_value.id})

        trigger = json.loads(resp.get("HX-Trigger", "{}"))
        assert "updateCart" in trigger

    def test_idempotency_key_prevents_double_add(self, client, db):
        product, variant, option_value = make_product_with_option_variant()
        headers = {"HTTP_X_IDEMPOTENCY_KEY": "test-options-idem-001"}

        client.post(options_url(product), {"opt_color": option_value.id}, **headers)
        client.post(options_url(product), {"opt_color": option_value.id}, **headers)

        line = cart_session(client)[str(variant.id)]
        assert line["quantity"] == 1
