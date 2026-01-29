# hr_common/urls.py

"""top level url registration for application"""

from django.urls import path

from hr_common import views

urlpatterns = [path("", views.index, name="index")]
