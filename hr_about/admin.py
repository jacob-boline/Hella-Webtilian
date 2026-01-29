# hr_about/admin.py

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from hr_about.models import CarouselSlide, PullQuote


@admin.register(CarouselSlide)
class CarouselSlideAdmin(ModelAdmin):
    list_display = ("id", "title", "caption", "order", "is_active", "created_at", "updated_at")
    list_editable = (
        "title",
        "caption",
        "order",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "caption")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "id")


@admin.register(PullQuote)
class PullQuoteAdmin(ModelAdmin):
    list_display = ("id", "attribution", "text", "order", "is_active", "created_at", "updated_at")
    list_editable = (
        "attribution",
        "text",
        "order",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("text", "attribution")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "id")
