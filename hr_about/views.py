# hr_about/views.py


import logging

from django.shortcuts import render

from hr_about.models import CarouselSlide, PullQuote
from hr_common.utils.unified_logging import log_event

logger = logging.getLogger(__name__)


def get_carousel_partial(request):
    slides = CarouselSlide.objects.filter(is_active=True).order_by("order", "id")
    log_event(logger, logging.INFO, "about.carousel.rendered", count=slides.count(),)
    return render(request, "hr_about/_about_carousel.html", {"slides": slides})


def get_quotes_partial(request):
    quotes = PullQuote.objects.filter(is_active=True).order_by("order", "id")
    log_event(logger, logging.INFO, "about.quotes.rendered", count=quotes.count(),)
    return render(request, "hr_about/_about_quotes.html", {"quotes": quotes})
