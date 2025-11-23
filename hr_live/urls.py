# hr_live/urls.py

from django.urls import path
from hr_live import views

app_name = 'hr_live'

urlpatterns = [
    path('', views.live_upcoming_list, name='upcoming'),
    path('past/', views.live_past_list, name='past'),

    #------------------------------------------------------------------------#
    #                            BELOW IS POST MVP                           #
    #------------------------------------------------------------------------#

    # # HTMX
    # path("partial/list/", views.live_upcoming_partial, name="upcoming_partial"),
    # path("partial/past/", views.live_past_partial, name="past_partial"),
    #
    # # Detail SSR + partial
    # path("<slug:slug>/", views.live_detail, name="detail"),
    # path("partial/<slug:slug>/card/", views.live_detail_card_partial, name="detail_card"),
    #
    # # JSON APIs
    # path("api/shows/", views.api_live_shows_list, name="api_shows"),
    # path("api/shows/<slug:slug>/", views.api_live_show_detail, name="api_show_detail"),
    #
    # # Calendar export
    # path("calendar.ics", views.live_calendar_ics, name="calendar_ics"),

]