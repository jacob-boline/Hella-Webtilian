from functools import lru_cache

import stripe
from django.conf import settings


@lru_cache(maxsize=1)
def get_stripe_client():
    """
    Returns either the real Stripe SDK or a lightweight mock, based on settings.
    The client is cached so stateful mocks can be inspected across calls.
    """
    if getattr(settings, "STRIPE_USE_MOCK", False):
        from hr_payment.stripe_mock import MockStripeClient

        return MockStripeClient()

    import stripe

    stripe.api_key = settings.STRIPE_API_KEY
    return stripe


def get_signature_verification_error():
    if getattr(settings, "STRIPE_USE_MOCK", False):
        from hr_payment.stripe_mock import MockSignatureVerificationError
        return MockSignatureVerificationError

    #  Apparently exposing this is not Stripe's jimjam
    if hasattr(stripe, 'error') and hasattr(stripe.error, 'SignatureVerificationError'):
        return stripe.error.SignatureVerificationError

    raise RuntimeError('Stripe SignatureVerificationError not found.')
