# hr_payments/providers/__init__.py


from django.conf import settings

from hr_payment.providers.mock_stripe import MockStripePaymentProvider
# from .stripe_checkout import StripeCheckoutProvider  # later


def get_payment_provider():
    backend = getattr(settings, "SHOP_PAYMENT_BACKEND", "mock_stripe")

    if backend == "mock_stripe":
        return MockStripePaymentProvider()
    elif backend == "stripe":
        # return StripeCheckoutProvider()
        raise NotImplementedError("Stripe backend not wired yet.")
    else:
        raise ValueError(f"Unknown SHOP_PAYMENT_BACKEND: {backend}")
