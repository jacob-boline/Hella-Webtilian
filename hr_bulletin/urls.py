# hr_bulletin/urls.py

from django.urls import path
from hr_bulletin import views


app_name = "hr_bulletin"

urlpatterns = [
    path("",             views.bulletin_list,         name="bulletin_list"),
    path("list/",        views.bulletin_list_partial, name="bulletin_list_partial"),
    path("<slug:slug>/", views.bulletin_detail,       name="bulletin_detail"),

    # # Admin-only CRUD
    # path("admin/bulletin/new",                 views.admin_bulletin_new,     name="admin_new"),
    # path("admin/bulletin/<slug:slug>/edit",    views.admin_bulletin_edit,    name="admin_edit"),
    # path("admin/bulletin/<slug:slug>/publish", views.admin_bulletin_publish, name="admin_publish"),
    # path("admin/bulletin/<slug:slug>/delete",  views.admin_bulletin_delete,  name="admin_delete"),
]
