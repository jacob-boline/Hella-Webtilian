from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView, PasswordChangeDoneView
from django.urls import path, reverse_lazy

from hr_access import views

app_name = 'hr_access'

urlpatterns = [

    path('access_panel', views.access_panel, name='access_panel'),
    path('access/sidebar/', views.sidebar_access, name='sidebar_access'),
    path('add_staff/', views.add_staff, name='add_staff'),

    path('login/', views.user_login, name='logoin'),
    path('login/success/', views.login_success, name='login_success'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/redirect', views.logout_redirect, name='logout_redirect'),

    path('password_change/', views.password_change, name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
             template_name='hr_access/password_reset_form.html',
             subject_template_name='hr_access/password_reset_subject.txt',
             email_template_name='hr_access/password_reset_email.html',
             success_url=reverse_lazy('hr_access:password_reset_done')
         ),  name='password_reset'),

    path('user_panel', views.user_panel, name='user_panel'),
]