# hr_access/views/account_get_orders.py

from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hr_core.utils.email import normalize_email
from hr_shop.models import Customer, Order
from utils.http import hx_login_required

PER_PAGE = 20

@hx_login_required
def _orders_queryset_for_user(user):
    """
    Return a queryset of account_get_orders visible to this authenticated user.

    Visibility rule:
    - Orders tied to any Customer rows related to the user OR matching email
    - Orders that match the user's email directly
    """
    email = normalize_email(user.email or "")

    customer_ids = (
        Customer.objects
        .filter(Q(user=user) | Q(email__iexact=email))
        .values_list("id", flat=True)
    )

    return (
        Order.objects
        .filter(Q(customer_id__in=customer_ids) | Q(email__iexact=email))
        .order_by("-created_at")
        .distinct()
    )

@hx_login_required
def _paginate(qs, *, page: int, per: int):
    """
    Offset pagination with the "n+1 trick".

    Returns: (rows, has_more)
    """
    page = max(int(page or 1), 1)
    start = (page - 1) * per
    rows = list(qs[start:start + per + 1])
    has_more = len(rows) > per
    return rows[:per], has_more


@hx_login_required
def orders(request):
    """
    First page of account_get_orders, rendered into a modal partial.
    """
    qs = _orders_queryset_for_user(request.user)

    rows, has_more = _paginate(qs, page=1, per=PER_PAGE)

    ctx = {
        "account_get_orders": rows,
        "has_more": has_more,
        "page": 1
    }
    return render(request, "hr_access/orders/_orders_modal.html", ctx)


@hx_login_required
def orders_page(request, n: int):
    """
    Subsequent pages of account_get_orders.
    """
    qs = _orders_queryset_for_user(request.user)

    page = max(int(n or 1), 1)
    rows, has_more = _paginate(qs, page=page, per=PER_PAGE)

    ctx = {
        "account_get_orders": rows,
        "has_more": has_more,
        "page": page
    }
    return render(request, "hr_access/orders/_orders_modal.html", ctx)


@hx_login_required
@require_GET
def order_detail_modal(request, order_id: int):
    """
    Detailed modal for a single order, with items + variant/product prefetched.
    """
    qs = _orders_queryset_for_user(request.user).prefetch_related(
        "items",
        "items__variant",
        "items__variant__product"
    ).select_related(
        "customer",
        "shipping_address"
    )

    order = get_object_or_404(qs, pk=order_id)

    return render(request, "hr_access/orders/_order_detail_modal.html", {"order": order})
