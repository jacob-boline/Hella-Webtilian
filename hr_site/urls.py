"""top level url registration for application"""

from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("test", views.index, name="index"),
    # path("test2", views.test2, name="test2"),
    # path("burn-test", views.burn_test, name="burn-test"),
    # path("parallax-test", views.parallax_test, name="par"),
    # path("pt2", views.pt2, name="pt2"),
    path("pt3", views.pt3, name="pt3"),
    path("pt4", views.pt4, name="pt4"),
    path("pt5", views.pt5, name="pt5"),
    path("pt6", views.pt6, name="pt6"),
    path("__reload__/", include("django_browser_reload.urls")),
]
