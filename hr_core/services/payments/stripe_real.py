# hr_core/services/payments/stripe_real.py

import logging
from logging import getLogger

import stripe

from hr_common.utils.unified_logging import log_event
from .base import PaymentGateway, CheckoutSession

logger = getLogger()


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
        log_event(
            logger,
            logging.INFO,
            "payments.stripe.checkout_session.created",
            session_id=sess.id,
            has_customer_email=bool(kw.get("customer_email")),
        )
        return CheckoutSession(sess.id, sess.url)

    def verify_webhook(self, request):
        payload = request.body
        sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig, self.webhook_secret)
        except Exception:
            log_event(
                logger,
                logging.ERROR,
                "payments.stripe.webhook.verify_failed",
                has_signature=bool(sig),
                exc_info=True,
            )
            raise
        event_dict = event.to_dict()
        log_event(
            logger,
            logging.INFO,
            "payments.stripe.webhook.verified",
            event_id=event_dict.get("id"),
            event_type=event_dict.get("type"),
        )
        return event_dict
