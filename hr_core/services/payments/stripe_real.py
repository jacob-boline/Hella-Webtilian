# hr_shop/gateways/stripe_real.py
import stripe
from .base import PaymentGateway, CheckoutSession

class StripeGateway(PaymentGateway):
    def __init__(self, api_key, webhook_secret):
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret

    def create_checkout_session(self, **kw):
        sess = stripe.checkout.Session.create(
            mode="payment",
            line_items=kw["line_items"],
            success_url=kw["success_url"],
            cancel_url=kw["cancel_url"],
            customer_email=kw.get("customer_email"),
            metadata=kw.get("metadata") or {},
        )
        return CheckoutSession(sess.id, sess.url)

    def verify_webhook(self, request):
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        event = stripe.Webhook.construct_event(payload, sig, self.webhook_secret)
        return event.to_dict()
