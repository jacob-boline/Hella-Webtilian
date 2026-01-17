# hr_core/services/payments/base.py

class CheckoutSession:
    def __init__(self, id, url):
        self.id = id
        self.url = url


class PaymentGateway:
    def create_checkout_session(self, *, line_items, success_url, cancel_url, customer_email=None, metadata=None) -> CheckoutSession:
        raise NotImplementedError

    def verify_webhook(self, request) -> dict:
        """Return parsed event dict or raise."""
        raise NotImplementedError
