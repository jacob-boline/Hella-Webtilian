# hr_shop/services/order_receipt.py

from __future__ import annotations

from django.template.loader import render_to_string

from hr_core.utils.urls import build_external_absolute_url
from hr_email.service import send_app_email
from hr_shop.models import Order
from hr_shop.tokens.order_receipt_token import generate_order_receipt_token


def send_order_receipt_email(*, order: Order, request=None, custom_id: str | None = None) -> None:
    receipt_token = generate_order_receipt_token(order_id=order.id, email=order.email)
    receipt_url = (
        build_external_absolute_url(request, "/", query={
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
