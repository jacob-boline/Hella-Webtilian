# hr_common/views.py

import logging

from django.shortcuts import render
from django.utils import timezone

from hr_about.models import CarouselSlide, PullQuote
from hr_common.utils.unified_logging import log_event
from hr_live.models import Show
from hr_shop.models import Product

logger = logging.getLogger(__name__)


def index(request):
    today = timezone.localdate()
    products = Product.objects.prefetch_related('variants').order_by('name')
    slides = CarouselSlide.objects.filter(is_active=True).order_by('order', 'id')
    quotes = PullQuote.objects.filter(is_active=True).order_by("order", "id")
    shows = Show.objects.filter(status='published', date__gte=today).select_related('venue').prefetch_related('lineup').order_by('date', 'time', 'id')[:5]
    modal = (request.GET.get('modal') or '').strip()
    log_event(
        logger,
        logging.INFO,
        "site.index.rendered",
        products_count=products.count(),
        slides_count=slides.count(),
        quotes_count=quotes.count(),
        shows_count=shows.count(),
        has_modal=bool(modal)
    )
    return render(request, "hr_site/templates/hr_common/index.html", {
        'products': products,
        'slides': slides,
        'quotes': quotes,
        'shows': shows,
        'landing_modal': modal
    })


def display_message_box_modal(request, *args, **kwargs):
    """
    Generic HTMX-friendly message box for the modal.

    Accepts:
      - title: str
      - message: str
      - level: 'info' | 'success' | 'warning' | 'error'
      - confirm_url: optional URL for the primary action
      - confirm_method: 'post' or 'get' (default: 'post')
      - confirm_label: button text (default: 'OK')
      - cancel_url: optional URL for a secondary action
      - cancel_label: button text (default: 'Cancel')
    Values can come from kwargs OR query parameters.
    """

    def _get(name, default=None):
        return kwargs.get(name) or request.GET.get(name) or default

    context = {
        'title':          _get('title', 'Notice'),
        'message':        _get('message', ''),
        'level':          _get('level', 'info'),
        "confirm_url":    _get("confirm_url"),
        "confirm_method": _get("confirm_method", "post").lower(),
        "confirm_label":  _get("confirm_label", "OK"),
        "cancel_url":     _get("cancel_url"),
        "cancel_label":   _get("cancel_label", "Cancel")
    }
    log_event(
        logger,
        logging.INFO,
        "site.message_box.rendered",
        level=context["level"],
        has_confirm=bool(context["confirm_url"]),
        has_cancel=bool(context["cancel_url"])
    )

    return render(request, "hr_site/templates/hr_common/display_message_box_modal.html", context)
