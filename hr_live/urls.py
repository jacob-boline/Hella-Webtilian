# hr_live/urls.py

from django.urls import path

from hr_live import views

app_name = "hr_live"

urlpatterns = [
    path("", views.live_upcoming_list, name="upcoming"),
    path("past/", views.live_past_list, name="past"),
    # path("shows/<int:year>/<int:month>/<int:day>/<slug:venue_slug>/", views.show_details, name="show_details"),
]
