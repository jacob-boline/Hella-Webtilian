# hr_access/admin.py

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from hr_access.forms import CustomUserChangeForm, CustomUserCreationForm

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ["email", "username", 'role', "is_superuser", "is_staff", 'is_active']
    list_filter = ['role', 'is_superuser', 'is_staff', 'is_active']

    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password'),
        }),
        ('Role & Status', {
            'fields': ('role', 'is_active'),
        }),
        ('Permissions (role based)', {
            'fields': ('is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {
            'fields': ('last_login',),
        }),
    )

    add_fieldsets = (  # BaseUserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    readonly_fields = ('is_staff', 'is_superuser', 'groups', 'last_login')
    search_fields = ['email', 'username']
    ordering = ['email']
    filter_horizontal = []

    def save_model(self, request, obj, form, change):

        UserModel = self.model

        if change:
            old = UserModel.objects.get(pk=obj.pk)

            demoting_from_admin = (
                old.role == UserModel.Role.GLOBAL_ADMIN and
                obj.role != UserModel.Role.GLOBAL_ADMIN
            )

            if demoting_from_admin:
                has_other_admin = UserModel.objects.exclude(pk=obj.pk).filter(
                    role=UserModel.Role.GLOBAL_ADMIN,
                    is_active=True,
                ).exists()

                if not has_other_admin:
                    messages.error(
                        request,
                        "You cannot demote the last Global Admin. "
                        "Create another Global Admin first."
                    )
                    return  # Skip saving

        super().save_model(request, obj, form, change)
