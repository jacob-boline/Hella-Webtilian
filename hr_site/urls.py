# hr_site/urls.py

"""top level url registration for application"""

from django.urls import path
from hr_site import views

urlpatterns = [
    path("", views.index, name="index")
]
