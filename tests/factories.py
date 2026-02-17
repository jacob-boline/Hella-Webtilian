# tests/factories.py

# Shared factory definitions imported by app-level conftest files.
# Keep this file to cross-cutting models only (Customer, Order, Address, etc.)
# App-specific factories (PaymentAttempt, ProductVariant, etc.) live in their
# own app's tests/conftest.py.

from datetime import timedelta

import factory
from django.utils import timezone

from hr_common.models import Address
from hr_shop.models import (
    CheckoutDraft,
    Customer,
    Order,
    PaymentStatus,
    Product,
    ProductVariant
)


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address
        # Address.save() computes fingerprint from content fields.
        # Each unique street_address (via Sequence) produces a unique row.

    street_address = factory.Sequence(lambda n: f"{100 + n} Test Street")
    city = "Minneapolis"
    subdivision = "MN"
    postal_code = "55401"
    country = "US"


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"customer{n}@example.com")
    first_name = "Test"
    last_name = "Customer"


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Test Product {n}")
    active = True
    # slug is auto-computed from name in Product.save()


class ProductVariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductVariant

    product = factory.SubFactory(ProductFactory)
    sku = factory.Sequence(lambda n: f"SKU-{n:04d}")
    name = factory.Sequence(lambda n: f"Variant {n}")
    price = "19.99"
    active = True
    # slug is auto-computed from product.name + variant.name in ProductVariant.save()


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    email = factory.LazyAttribute(lambda obj: obj.customer.email)
    total = "29.99"
    payment_status = PaymentStatus.UNPAID


class CheckoutDraftFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CheckoutDraft

    customer = factory.SubFactory(CustomerFactory)
    email = factory.LazyAttribute(lambda obj: obj.customer.email)
    address = factory.SubFactory(AddressFactory)
    cart = factory.LazyFunction(list)
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    order = None
