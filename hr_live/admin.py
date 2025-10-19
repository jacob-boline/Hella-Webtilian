from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import Act, Booker, Show, Venue, Address, Musician


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_editable = ("street_address", "city", "subdivision", "postal_code", "country")
    list_filter = ("city", "subdivision", "postal_code", "country")
    list_display = ("id", "street_address", "city", "subdivision", "postal_code", "country")
    list_display_links = ("id",)


@admin.register(Act)
class ActAdmin(ModelAdmin):
    list_display = ("name", "website")
    list_editable = ("website",)
    list_filter = ("name",)


@admin.register(Booker)
class BookerAdmin(ModelAdmin):
    list_display = ("id", "first_name","last_name", "nickname", "phone_number", "email")
    list_editable = ("first_name", "last_name", "nickname", "phone_number", "email")
    list_display_links = ("id",)


@admin.register(Venue)
class VenueAdmin(ModelAdmin):
    list_display = ("name", "website", "phone_number", "email", "note")
    list_editable = ("website", "phone_number", "email", "note")



@admin.register(Show)
class ShowAdmin(ModelAdmin):
    list_display = ("id", "venue", "date", "time", "image")
    list_editable = ("venue", "date", "time", "image")
    list_display_links = ("id",)
    readonly_fields = ("created_by",)

    def save_model(self, request, obj, form, change):
        if obj.id is None:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Musician)
class MusicianAdmin(ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'phone_number', 'email')
    list_editale = ('first_name', 'last_name', 'phone', 'email')
    list_display_links = ('id',)