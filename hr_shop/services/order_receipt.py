# hr_shop/services/order_receipt.py

from __future__ import annotations

from django.conf import settings
from django.template.loader import render_to_string

from hr_core.utils.urls import build_external_absolute_url
from hr_email.service import send_app_email
from hr_shop.models import Order
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token


def send_order_receipt_email(*, order: Order, request=None, custom_id: str | None = None) -> None:
    receipt_token = generate_order_receipt_token(order_id=order.id, email=order.email)

    request_for_url = request
    if request_for_url is None and not getattr(settings, "EXTERNAL_BASE_URL", ""):
        fallback_base = getattr(settings, "SITE_URL", "")
        if fallback_base:
            class _RequestLike:
                def __init__(self, base: str):
                    self._base = base.rstrip("/")
                def build_absolute_uri(self, path_with_qs: str) -> str:
                    return f"{self._base}{path_with_qs}"

            request_for_url = _RequestLike(fallback_base)

    receipt_url = (
        build_external_absolute_url(request_for_url, "/", query={
            "modal": "order_payment_result",
            "handoff": "order_payment_result",
            "t": receipt_token
        }) + "#parallax-section-shows"
    )

    subject = f"Hella Reptilian Order #{order.id} receipt"
    html_body = render_to_string("hr_shop/emails/order_receipt.html", {"order": order, "receipt_url": receipt_url})

    send_app_email(
        to_emails=[order.email],
        subject=subject,
        html_body=html_body,
        custom_id=custom_id or f"order_receipt_{order.id}"
    )
