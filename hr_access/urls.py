# hr_access/urls.py

from django.contrib.auth.views import (
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import path

from hr_access.views import orders, admin, auth, account
from hr_shop.views.orders import order_detail_modal, orders_page

app_name = 'hr_access'

urlpatterns = [

    # Panels / sidebar
    path('sidebar/load/', auth.account_get_sidebar_panel, name='account_get_sidebar_panel'),
    path('sidebar/load/user-panel/', auth.account_get_user_panel, name='account_get_user_panel'),

    # Auth (public login/logout/account_signup)
    path('account_signup/', account.account_signup, name='account_signup'),
    path('login/', auth.auth_login, name='auth_login'),
    # path('login/success/', views.login_success, name='login_success'),
    path('logout/', auth.auth_logout, name='auth_logout'),
    # path('logout/redirect', views.logout_redirect, name='logout_redirect'),

    # Password change (for logged-in users)
    path('password/change/', account.account_change_password, name='account_change_password'),
    path('password/change/done/', PasswordChangeDoneView.as_view(template_name="hr_access/registration/_password_change_done.html"),name='password_change_done'),

    # Password reset
    path('password/reset/', PasswordResetView.as_view(template_name='hr_access/registration/templates/hr_access/password_reset/_password_reset_form.html'), name='password_reset'),
    path('password/reset/done/', PasswordResetDoneView.as_view(template_name='hr_access/registration/templates/hr_access/password_reset/_password_reset_done.html'), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='hr_access/registration/templates/hr_access/password_reset/_password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset/complete/', PasswordResetCompleteView.as_view(template_name='hr_access/registration/templates/hr_access/password_reset/_password_reset_complete.html'), name='password_reset_complete'),

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
    path('account_get_orders/', orders.account_get_orders, name='account_get_orders'),
    path('account_get_orders/unclaimed/', orders.account_get_unclaimed_orders, name='account_get_unclaimed_orders'),
    path('account_get_orders/claim/', orders.account_submit_claim_unclaimed_orders, name='account_submit_claim_unclaimed_orders'),

    path("account_get_orders/page/<int:n>/", orders_page, name="orders_page"),
    path("account_get_orders/", orders.account_get_orders, name="account_get_orders"),
    path("account_get_orders/<int:order_id>/", order_detail_modal, name="order_detail_modal"),
    path("account_get_orders/<int:order_id>/receipt/", orders.account_get_order_receipt, name="account_get_order_receipt"),

    # path("account/claim/<slug:uidb64>/<slug:token>/", views.claim_account, name="claim_account"),
    # path("account/claim/resend/", views.claim_resend, name="claim_resend"),  # POST (email)
    path('manage/superuser/remove/<int:user_id>/', admin.admin_demote_superuser, name='admin_demote_superuser'),
    path('manage/superuser/confirm-removal/<int:user_id>/', admin.admin_confirm_privilege_demotion, name='admin_confirm_privilege_demotion'),
    path('manage/staff/add/', admin.admin_create_site_admin, name='admin_create_site_admin'),

    # Post-purchase account (guest checkout -> account create/claim flow)
    path('post-purchase/<int:order_id>/', account.account_get_post_purchase_create_account, name='account_get_post_purchase_create_account'),
    path('post-purchase/<int:order_id>/create/', account.account_submit_post_purchase_create_account, name='account_submit_post_purchase_create_account'),
    # path('post-purchase/<int:order_id>/done/', views.post_purchase_account_done, name='post_purchase_account_done'),
    path('post-purchase/<int:order_id>/claim-account_get_orders/', account.account_submit_post_purchase_claim_orders, name='account_submit_post_purchase_claim_orders'),

]
