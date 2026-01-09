# hr_access/urls.py

from django.contrib.auth.views import PasswordChangeDoneView
from django.urls import path

from hr_access.views import orders, admin, auth, account
from hr_access.views.password_reset import (
    AccountPasswordResetView,
    AccountPasswordResetDoneView,
    AccountPasswordResetConfirmView,
    AccountPasswordResetCompleteView,
)
from hr_shop.views.orders import order_detail_modal, orders_page

app_name = 'hr_access'

urlpatterns = [

    # Panels / sidebar
    path('sidebar/load/', auth.account_get_sidebar_panel, name='account_get_sidebar_panel'),
    path('sidebar/load/user-panel/', auth.account_get_user_panel, name='account_get_user_panel'),

    # Auth (public login/logout/account_signup)
    path('account_signup/', account.account_signup, name='account_signup'),
    path('account_signup/confirm/', account.account_signup_confirm, name="account_signup_confirm"),
    path('login/', auth.auth_login, name='auth_login'),
    path('logout/', auth.auth_logout, name='auth_logout'),

    # Password change
    path('account/settings/', account.account_settings, name='account_settings'),
    path('password/change/', account.account_change_password, name='account_change_password'),
    path('password/change/done/', PasswordChangeDoneView.as_view(template_name="hr_access/registration/_password_change_done.html"),name='password_change_done'),
    path('account/email/change/', account.account_change_email, name='account_change_email'),
    path('account/email/change/confirm/', account.account_change_email_confirm, name='account_change_email_confirm'),
    path('account/email/change/success/', account.account_email_change_success, name='account_email_change_success'),
    path('account/security/logout-all/confirm/', account.account_logout_all_confirm, name='account_logout_all_confirm'),
    path('account/security/logout-all/', account.account_logout_all_sessions, name='account_logout_all_sessions'),
    path('account/delete/confirm/', account.account_delete_confirm, name='account_delete_confirm'),
    path('account/delete/', account.account_delete_account, name='account_delete_account'),

    # Password reset
    path('password/reset/', AccountPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', AccountPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', AccountPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', AccountPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Orders (modal vs full page handled inside view)
    path('account_get_orders/', orders.account_get_orders, name='account_get_orders'),
    path('account_get_orders/unclaimed/', orders.account_get_unclaimed_orders, name='account_get_unclaimed_orders'),
    path('account_get_orders/claim/', orders.account_submit_claim_unclaimed_orders, name='account_submit_claim_unclaimed_orders'),
    path("account_get_orders/page/<int:n>/", orders_page, name="orders_page"),
    path("account_get_orders/<int:order_id>/", order_detail_modal, name="order_detail_modal"),
    path("account_get_orders/<int:order_id>/receipt/", orders.account_get_order_receipt, name="account_get_order_receipt"),

    path('manage/superuser/remove/<int:user_id>/', admin.admin_demote_superuser, name='admin_demote_superuser'),
    path('manage/superuser/confirm-removal/<int:user_id>/', admin.admin_confirm_privilege_demotion, name='admin_confirm_privilege_demotion'),
    path('manage/staff/add/', admin.admin_create_site_admin, name='admin_create_site_admin'),

    # Post-purchase account (guest checkout -> account create/claim flow)
    path('post-purchase/<int:order_id>/', account.account_get_post_purchase_create_account, name='account_get_post_purchase_create_account'),
    path('post-purchase/<int:order_id>/create/', account.account_submit_post_purchase_create_account, name='account_submit_post_purchase_create_account'),
    path('post-purchase/<int:order_id>/claim-account_get_orders/', account.account_submit_post_purchase_claim_orders, name='account_submit_post_purchase_claim_orders'),

]
