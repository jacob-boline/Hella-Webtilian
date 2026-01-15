# hr_access/views/account_get_orders.py

from __future__ import annotations

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django.db import transaction

from hr_core.utils.email import normalize_email
from hr_shop.models import Order, OrderItem
from utils.http import hx_login_required


@hx_login_required
@require_GET
def account_get_orders(request):
    email = request.user.email

    base_qs = (
        Order.objects
        .filter(user=request.user)
        .select_related("shipping_address", "customer")
        .prefetch_related(
            Prefetch(
                "items",
                queryset=OrderItem.objects.select_related("variant", "variant__product")
            )
        )
        .order_by("-created_at")
    )

    order_list = list(base_qs[:21])

    ctx = {
        "orders": order_list[:20],
        "has_more": len(order_list) > 20,
        "unclaimed_count": (
            Order.objects.filter(user__isnull=True, email__iexact=email).count()
            if email else 0
        )
    }

    return render(request, "hr_access/orders/_orders_modal_body.html", ctx)


@hx_login_required
@require_GET
def account_get_order_receipt(request, order_id: int):
    order = get_object_or_404(
        Order.objects.select_related("customer", "shipping_address"),
        id=order_id,
        user=request.user
    )

    items = order.items.select_related("variant", "variant__product").all()
    is_guest = not (request.user.is_authenticated and getattr(order, "user_id", None) == request.user.id)

    return render(request, "hr_shop/checkout/_order_receipt_modal.html", {
        "order": order,
        "items": items,
        "customer": order.customer,
        "address": order.shipping_address,
        "is_guest": is_guest
    })


@hx_login_required
@require_GET
def account_get_unclaimed_orders(request):
    email = request.user.email

    if not email:
        return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
            "email": "",
            "account_get_orders": [],
            "error": "No email address is associated with your account."
        }, status=400)

    unclaimed_orders = (
        Order.objects
        .filter(user__isnull=True, email__iexact=email)
        .order_by("-created_at")[:50]
    )

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
        return render(request, 'hr_access/orders/_unclaimed_orders_modal.html', {
            'email': '',
            'unclaimed_orders': [],
            'error': 'No email address is associated with your account.',
            'claimed_count': 0
        }, status=400)

    raw_ids = request.POST.getlist("order_ids")
    order_ids = [int(x) for x in raw_ids if str(x).isdigit()]

    if not order_ids:
        unclaimed_orders = (
            Order.objects
            .filter(user__isnull=True, email__iexact=email)
            .order_by("-created_at")[:50]
        )
        return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
            "email": email,
            "unclaimed_orders": unclaimed_orders,
            "error": "Select at least one order to claim.",
            "claimed_count": 0
        })

    with transaction.atomic():
        qs = (
            Order.objects
            .select_for_update()
            .filter(id__in=order_ids, user__isnull=True, email__iexact=email)
        )
        claimed_count = qs.update(user=request.user)

    remaining = (
        Order.objects
        .filter(user__isnull=True, email__iexact=email)
        .order_by("-created_at")[:50]
    )

    return render(request, "hr_access/orders/_unclaimed_orders_modal.html", {
        "email": email,
        "unclaimed_orders": remaining,
        "error": None,
        "claimed_count": claimed_count
    })
