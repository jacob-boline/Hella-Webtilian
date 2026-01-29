# hr_core/services/payments/__init__.py
from django.conf import settings

from .stripe_mock import MockGateway
from .stripe_real import StripeGateway


def get_gateway():
    if getattr(settings, "PAYMENT_PROVIDER", "MOCK") == "STRIPE":
        return StripeGateway(settings.STRIPE_API_KEY, settings.STRIPE_WEBHOOK_SECRET)
    return MockGateway()
