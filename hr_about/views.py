# hr_about/views.py


from django.shortcuts import render
from hr_about.models import CarouselSlide, PullQuote


def get_carousel_partial(request):
    slides = CarouselSlide.objects.filter(is_active=True).order_by('order', 'id')
    return render(request, 'hr_about/_about_carousel.html', {'slides': slides})


def get_quotes_partial(request):
    quotes = PullQuote.objects.filter(is_active=True).order_by("order", "id")
    return render(request, "hr_about/_about_quotes.html", {"quotes": quotes})
