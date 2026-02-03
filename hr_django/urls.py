# hr_django/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("about/", include("hr_about.urls")),
    path("user/", include("hr_access.urls")),
    path("bulletin/", include("hr_bulletin.urls")),
    path("live/", include("hr_live.urls")),
    path("payment/", include("hr_payment.urls")),
    path("shop/", include("hr_shop.urls")),
    path("", include("hr_common.urls")),
    path("admin/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path(".well-known/appspecific/com.chrome.devtools.json", lambda r: JsonResponse({}, status=204),)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
