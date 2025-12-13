# hr_access/urls.py

from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView, PasswordChangeDoneView
from django.urls import path, reverse_lazy

from hr_access import views
from hr_access.views import (
    HRPasswordResetView,
    HRPasswordResetDoneView,
    HRPasswordResetConfirmView,
    HRPasswordResetCompleteView
)

app_name = 'hr_access'

urlpatterns = [

    # Panels / sidebar
    path('access_panel', views.access_panel, name='access_panel'),
    path('access/sidebar/', views.sidebar_access, name='sidebar_access'),
    path('user_panel', views.user_panel, name='user_panel'),

    # Auth (public login/logout/signup)
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('login/success/', views.login_success, name='login_success'),
    path('logout/', views.user_logout, name='logout'),
    path('logout/redirect', views.logout_redirect, name='logout_redirect'),

    # Password change (for logged-in users)
    path('password/change/', views.password_change, name='password_change'),
    path('password/change/done/', PasswordChangeDoneView.as_view(template_name="hr_access/password_change_done.html"),name='password_change_done'),

    # Password reset
    path('password/reset/', HRPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', HRPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', HRPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', HRPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # # Password reset
    # path(
    #     'password_reset/', auth_views.PasswordResetView.as_view(
    #          template_name='hr_access/_password_reset_form.html',
    #          subject_template_name='hr_access/password_reset_subject.txt',
    #          email_template_name='hr_access/password_reset_email.html',
    #          success_url=reverse_lazy('hr_access:password_reset_done')),
    #     name='password_reset'),
    # path(
    #     'password_reset/done/',
    #     auth_views.PasswordResetDoneView.as_view(
    #         template_name='hr_access/_password_reset_done.html'),
    #     name='password_reset_done'),
    # path(
    #     "reset/<uidb64>/<token>/",
    #     auth_views.PasswordResetConfirmView.as_view(
    #         template_name="hr_access/_password_reset_confirm.html",
    #         success_url=reverse_lazy("hr_access:password_reset_complete")),
    #     name="password_reset_confirm",),
    # path(
    #     "reset/done/",
    #     auth_views.PasswordResetCompleteView.as_view(
    #         template_name="hr_access/_password_reset_complete.html"),
    #     name="password_reset_complete",
    # ),

    # Orders (modal vs full page handled inside view)
    path('orders/', views.orders, name='orders'),

    path('account/claim/modal/', views.claim_modal, name='claim_modal'),
    path('account/claim/verify/', views.claim_verify, name='claim_verify'),
    path('account/claim/resend/', views.claim_resend, name='claim_resend'),
    path('account/claim/<int:user_id>/<slug:token>/', views.claim_account, name='claim_account'),

    # path("account/claim/<slug:uidb64>/<slug:token>/", views.claim_account, name="claim_account"),
    # path("account/claim/resend/", views.claim_resend, name="claim_resend"),  # POST (email)

    path('add_staff/', views.add_staff, name='add_staff'),
]