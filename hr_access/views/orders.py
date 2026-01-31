# hr_access/views/orders.py

from __future__ import annotations

import logging

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from hr_common.utils.htmx_responses import hx_login_required
from hr_common.utils.http.htmx import hx_trigger
from hr_common.utils.http.messages import show_message
from hr_common.utils.unified_logging import log_event
from hr_shop.models import Order, OrderItem

logger = logging.getLogger(__name__)


@hx_login_required
@require_GET
def account_get_orders(request):
    email = request.user.email

    base_qs = (
        Order.objects.filter(user=request.user)
        .select_related("shipping_address", "customer")
        .prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("variant", "variant__product")))
        .order_by("-created_at")
    )

    order_list = list(base_qs[:21])

    ctx = {
        "orders": order_list[:20],
        "has_more": len(order_list) > 20,
        "unclaimed_count": (Order.objects.filter(user__isnull=True, email__iexact=email).count() if email else 0)
    }

    log_event(logger, logging.INFO, "access.orders.list_rendered", order_count=len(ctx["orders"]), has_more=ctx["has_more"])
    return render(request, "hr_access/orders/_orders_modal_body.html", ctx)


@hx_login_required
@require_GET
def account_get_order_receipt(request, order_id: int):
    order = get_object_or_404(Order.objects.select_related("customer", "shipping_address"), id=order_id, user=request.user)

    items = order.items.select_related("variant", "variant__product").all()
    is_guest = not (request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id)

    log_event(logger, logging.INFO, "access.orders.receipt_rendered", order_id=order.id)
    return render(request, "hr_shop/checkout/_order_receipt_modal.html", {
        "order": order,
        "items": items,
        "customer": order.customer,
        "address": order.shipping_address,
        "is_guest": is_guest}
    )


@hx_login_required
@require_GET
def account_get_unclaimed_orders(request):
    email = request.user.email

    if not email:
        log_event(logger, logging.WARNING, "access.orders.unclaimed.missing_email")
        return hx_trigger({"showMessage": show_message("No email address is associated with your account.")}, status=400)

    unclaimed_orders = (
        Order.objects
        .filter(user__isnull=True, email__iexact=email)
        .order_by("-created_at")
        [:50]
    )
    log_event(logger, logging.INFO, "access.orders.unclaimed_rendered", unclaimed_count=len(unclaimed_orders))
    return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
        "email": email,
        "unclaimed_orders": unclaimed_orders,
        "error": None
    })


@hx_login_required
@require_POST
def account_submit_claim_unclaimed_orders(request):
    email = request.user.email
    if not email:
        log_event(logger, logging.WARNING, "access.orders.claim.missing_email")
        return hx_trigger({"showMessage": show_message("No email address is associated with your account.")}, status=400)

    raw_ids = request.POST.getlist("order_ids")
    target_ids = [int(x) for x in raw_ids if str(x).isdigit()]

    if not target_ids:
        log_event(logger, logging.WARNING, "access.orders.claim.missing_selection")
        return hx_trigger({"showMessage": show_message("You must select one or more orders in order to claim.")}, status=400)

    with transaction.atomic():
        qs = Order.objects.select_for_update().filter(id__in=target_ids, user__isnull=True, email__iexact=email)
        claimed_ids = list(qs.values_list("id", flat=True))
        claimed_count = qs.update(user=request.user)

    log_event(logger, logging.INFO, "access.orders.claim.completed", claimed_count=claimed_count)
    return hx_trigger({
        "unclaimedOrdersClaimed": {
            "ids": claimed_ids,
            "count": claimed_count
        }
    }, status=204)
