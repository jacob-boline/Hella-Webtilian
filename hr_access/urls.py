# hr_access/urls.py

from django.contrib.auth.views import (
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import path

from hr_access import views
from hr_shop.views import orders


app_name = 'hr_access'

urlpatterns = [

    # Panels / sidebar
    path('sidebar/load/', views.determine_sidebar_access_panel, name='determine_sidebar_access_panel'),
    path('sidebar/load/user-panel/', views.get_user_sidebar_panel, name='get_user_sidebar_panel'),

    # Auth (public login/logout/signup)
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('login/success/', views.login_success, name='login_success'),
    path('logout/', views.user_logout, name='logout'),
    path('logout/redirect', views.logout_redirect, name='logout_redirect'),

    # Password change (for logged-in users)
    path('password/change/', views.password_change, name='password_change'),
    path('password/change/done/', PasswordChangeDoneView.as_view(template_name="hr_access/registration/password_change_done.html"),name='password_change_done'),

    # Password reset
    path('password/reset/', PasswordResetView.as_view(template_name='hr_access/registration/_password_reset_form.html'), name='password_reset'),
    path('password/reset/done/', PasswordResetDoneView.as_view(template_name='hr_access/registration/_password_reset_done.html'), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='hr_access/registration/_password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset/complete/', PasswordResetCompleteView.as_view(template_name='hr_access/registration/_password_reset_complete.html'), name='password_reset_complete'),

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
    path('account/claim/start/', views.claim_start, name='claim_start'),
    path('account/claim/verify/', views.claim_verify, name='claim_verify'),
    path('account/claim/resend/', views.claim_resend, name='claim_resend'),
    path('account/claim/<int:user_id>/<slug:token>/', views.claim_account, name='claim_account'),

    path("orders/page/<int:n>/", orders.orders_page, name="orders_page"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/", orders.order_detail_modal, name="order_detail_modal"),

    # path("account/claim/<slug:uidb64>/<slug:token>/", views.claim_account, name="claim_account"),
    # path("account/claim/resend/", views.claim_resend, name="claim_resend"),  # POST (email)
    path('manage/superuser/remove/<int:user_id>/', views.perform_superuser_removal, name='perform_superuser_removal'),
    path('manage/superuser/confirm-removal/<int:user_id>/', views.get_message_confirm_superuser_removal, name='confirm_superuser_removal'),
    path('manage/staff/add/', views.add_staff, name='add_staff'),
]
