"""
URL configuration for the grabsomore application.

Defines URL routes for authentication, registration,
password reset functionality, and role-based dashboards.
"""

from django.urls import path
from . import views

app_name = 'grabsomore'

urlpatterns = [
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path('', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('welcome/', views.welcome, name='welcome'),
    path('alter_login/', views.login_user, name='alterlogin'),
    path(
        'request-password-reset/',
        views.send_password_reset,
        name='request_password_reset',
    ),
    path(
        'reset/<str:token>/',
        views.reset_user_password,
        name='password_reset_form',
    ),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('vendor-dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
]
