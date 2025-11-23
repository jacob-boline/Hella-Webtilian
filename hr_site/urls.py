# hr_site/urls.py

"""top level url registration for application"""

from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # HTMX partials
    path("about/partial/carousel", views.about_carousel_partial, name="about_carousel_partial"),
    path("about/partial/quotes", views.about_quotes_partial, name="about_quotes_partial"),

    # JSON API
    path("api/about/carousel", views.api_about_carousel, name="api_about_carousel"),
    path("api/about/quotes", views.api_about_quotes, name="api_about_quotes"),

    path("__reload__/", include("django_browser_reload.urls")),
]
