# hr_access/services/post_purchase.py

from __future__ import annotations

from django.db import transaction

from hr_access.forms import AccountCreationForm
from hr_access.models import User
from hr_shop.models import Order


def build_post_purchase_form(order: Order, post_data=None) -> AccountCreationForm:
    locked_email = order.email
    if post_data is None:
        return AccountCreationForm(locked_email=locked_email)

    post = post_data.copy()
    post["email"] = locked_email
    return AccountCreationForm(post, locked_email=locked_email)


def create_post_purchase_account(order: Order, post_data) -> tuple[User, list[Order]] | None:
    form = build_post_purchase_form(order, post_data)
    if not form.is_valid():
        return None

    with transaction.atomic():
        user = form.create_user(role=User.Role.USER)

        cust = getattr(order, "customer", None)
        if cust and cust.user_id is None:
            cust.user = user
            cust.save(update_fields=["user", "updated_at"])

        if getattr(order, "user_id", None) is None:
            order.user = user
            order.save(update_fields=["user", "updated_at"])

    other_orders = list(
        Order.objects.filter(email__iexact=order.email, user__isnull=True)
        .exclude(pk=order.id)
        .order_by("-created_at")[:25]
    )
    return user, other_orders


def get_post_purchase_unclaimed_orders(email: str, *, exclude_order_id: int) -> list[Order]:
    return list(
        Order.objects.filter(email__iexact=email, user__isnull=True)
        .exclude(pk=exclude_order_id)
        .order_by("-created_at")
    )
