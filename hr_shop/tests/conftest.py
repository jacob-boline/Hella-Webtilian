# hr_shop/tests/conftest.py

# Fixtures scoped to the shop app.
# Shared model factories live in tests/factories.py.

from unittest.mock import MagicMock

import pytest

from tests.factories import CustomerFactory, ProductFactory, ProductVariantFactory

# ---------------------------------------------------------------------------
# Re-export shared factories so shop tests import from one place
# ---------------------------------------------------------------------------
__all__ = [
    "CustomerFactory",
    "ProductFactory",
    "ProductVariantFactory"
]


# ---------------------------------------------------------------------------
# Cart session helpers
#
# The Cart class takes a request and reads/writes request.session directly.
# For unit tests of Cart logic we don't need a real HTTP request or a real
# session backend — a MagicMock with a plain dict as .session is enough.
# This keeps Cart unit tests fast and free of DB setup for the session layer.
# (Tests that call Cart.__iter__ or Cart.total() still need `db` because
# those methods query ProductVariant.)
# ---------------------------------------------------------------------------

def make_session_request(session_data=None):
    """
    Return a minimal mock request whose .session behaves like a dict.
    Pass session_data to pre-populate the session (e.g. an existing cart).
    """
    request = MagicMock()
    request.session = session_data if session_data is not None else {}
    return request


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session_request():
    """A fresh mock request with an empty session."""
    return make_session_request()


@pytest.fixture
def product(db):
    return ProductFactory()


@pytest.fixture
def variant(db, product):
    """An active ProductVariant at $19.99."""
    return ProductVariantFactory(product=product, price="19.99")


@pytest.fixture
def inactive_variant(db, product):
    """An inactive ProductVariant — should not be addable via slug lookup."""
    return ProductVariantFactory(product=product, price="19.99", active=False)
