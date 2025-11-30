from django.shortcuts import render
from django.utils import timezone

from hr_live.models import Show
from hr_shop.models import Product
from hr_about.models import CarouselSlide, PullQuote


def index(request):
    today = timezone.localdate()
    products = Product.objects.prefetch_related('variants').order_by('name')
    slides = CarouselSlide.objects.filter(is_active=True).order_by('order', 'id')
    quotes = PullQuote.objects.filter(is_active=True).order_by("order", "id")
    shows = Show.objects.filter(status='published', date__gte=today).select_related('venue').prefetch_related('lineup').order_by('date', 'time', 'id')[:5]
    return render(request, "hr_site/index.html", {
        'products': products,
        'slides': slides,
        'quotes': quotes,
        'shows': shows,
    })


def display_message_box_modal(request, *args, **kwargs):
    """
    Generic HTMX-friendly message box for the modal.

    Accepts:
      - title: str
      - message: str
      - level: 'info' | 'success' | 'warning' | 'error'
      - confirm_url: optional URL for the primary action
      - confirm_method: 'post' or 'get' (default: 'post')
      - confirm_label: button text (default: 'OK')
      - cancel_url: optional URL for a secondary action
      - cancel_label: button text (default: 'Cancel')
    Values can come from kwargs OR query parameters.
    """

    def _get(name, default=None):
        return kwargs.get(name) or request.GET.get(name) or default

    context = {
        'title':        _get('title', 'Notice'),
        'message':      _get('message', ''),
        'level':        _get('level', 'info'),
        "confirm_url":    _get("confirm_url"),
        "confirm_method": _get("confirm_method", "post").lower(),
        "confirm_label":  _get("confirm_label", "OK"),
        "cancel_url":     _get("cancel_url"),
        "cancel_label":   _get("cancel_label", "Cancel"),
    }

    return render(request, "hr_site/display_message_box_modal.html", context)

    # ------------------------------------------------------------------
    # # Confirmation when removing superuser / global admin privileges
    # # ------------------------------------------------------------------
    # def save_modal(self, request, obj, form, change):
    #     """
    #     Add a confirmation step when:
    #     - a superuser is being demoted (is_superuser -> False), or
    #     - a Global Admin (role=GLOBAL_ADMIN) is being changed to a non-admin role.
    #
    #     If the confirmation flag is present in POST, we proceed.
    #     """
    #
    #     if change:
    #         old = User.objects.get(pk=obj.pk)
    #
    #         removing_superuser = old.is_superuser and not obj.is_superuser
    #         removing_global_role = (old.role == User.Role.GLOBAL_ADMIN and obj.role != User.Role.GLOBAL_ADMIN)
    #
    #         if (removing_superuser or removing_global_role) and 'confirm_superuser_removal' not in request.POST:
    #             # TODO don't allow the last superuser to be removed
    #             if removing_superuser:
    #                 other_supers_exist = User.objects.filter(is_superuser=True).exclude(pk=obj.pk).exists()
    #                 if not other_supers_exist:
    #                     messages.error(request, 'Superuser is on Starks in Winterfell vibes.')
    #                     return render(
    #                         request,
    #                         "admin/auth/user/change_form.html",
    #                         {
    #                             "title":                 "Change user",
    #                             "original":              old,
    #                             "object":                old,
    #                             "is_popup":              False,
    #                             "save_as":               self.save_as,
    #                             "opts":                  self.model._meta,
    #                             "app_label":             self.model._meta.app_label,
    #                             "has_view_permission":   self.has_view_permission(request, old),
    #                             "has_change_permission": self.has_change_permission(request, old),
    #                             "has_delete_permission": self.has_delete_permission(request, old),
    #                             "has_add_permission":    self.has_add_permission(request),
    #                             "adminform":             self.get_form(request, obj=obj)(instance=obj),
    #                         },
    #                     )
    #
    #             # Show confirmation page
    #             context = {
    #                 "title":                "Confirm removal of global admin privileges",
    #                 "object":               old,
    #                 "original":             old,
    #                 "opts":                 self.model._meta,
    #                 "app_label":            self.model._meta.app_label,
    #                 "action_url":           request.path,
    #                 "removing_superuser":   removing_superuser,
    #                 "removing_global_role": removing_global_role,
    #             }
    #             return render(request, "hr_access/confirm_superuser_removal.html", context)
    #
    #     super().save_model(request, obj, form, change)
