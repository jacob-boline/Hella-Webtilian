from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from hr_shop.models import Order
from hr_core.utils import http


@login_required
def orders(request):
    qs = (Order.objects
          .filter(Q(email=request.user.email) | Q(user=request.user))
          .order_by('-created_at')
          .distinct())

    ctx = {
        "orders": qs[:20],
        "has_more": qs.count() > 20
    }

    template = "orders.html"

    if http.is_htmx(request):
        template = "_orders_modal.html"

    return render(request, f"account/{template}", ctx)


@login_required
def orders_page(request, n: int):
    per = 20
    start = (n-1)*per
    end = n*per

    qs = (Order.objects
          .filter(Q(email=request.user.email) | Q(user=request.user))
          .order_by('-created_at')
          .distinct())

    return render(request, "account/_orders_list_items.html", {
        "orders": qs[start:end],
        "has_more": qs.count() > end
    })


@login_required
def order_detail_modal(request, order_id: int):
    order = get_object_or_404(
        Order.objects.filter(Q(email=request.user.email) | Q(user=request.user)),
        pk=order_id
    )
    return render(request, "account/_order_detail_modal.html", {"order": order})
