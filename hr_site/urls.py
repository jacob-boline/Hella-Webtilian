# hr_site/urls.py

"""top level url registration for application"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
]
