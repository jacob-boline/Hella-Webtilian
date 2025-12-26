# hr_payment/providers/__init__.py

from django.conf import settings
from hr_payment.providers.mock_stripe import MockStripePaymentProvider
from hr_payment.providers.stripe import StripeEmbeddedCheckoutProvider


def get_payment_provider():
    backend = getattr(settings, "SHOP_PAYMENT_BACKEND", "stripe")

    if backend == "mock_stripe":
        return MockStripePaymentProvider()
    if backend == "stripe":
        return StripeEmbeddedCheckoutProvider()

    raise ValueError(f"Unknown SHOP_PAYMENT_BACKEND: {backend}")
