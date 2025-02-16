from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ["email", "username", "is_admin", "is_staff"]
    list_filter = ['is_admin']
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ()}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ()})
    )
    search_fields = ["email", "usernamne"]
    ordering = ['email']
    filter_horizontal = []
