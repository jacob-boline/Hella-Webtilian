from django.urls import path
from . import views

urlpatterns = [
    path("test", views.index, name="index"),
    path("test2", views.test2, name="test2"),
    path("burn-test", views.burn_test, name="burn-test"),
    path("parallax-test", views.parallax_test, name="par"),
    path("pt2", views.pt2, name="pt2"),
    path("pt3", views.pt3, name="pt3"),
]
