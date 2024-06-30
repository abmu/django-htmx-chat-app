"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from allauth.account import views as allauth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', allauth_views.LoginView.as_view(), name='account_login'),
    path('logout/', allauth_views.LogoutView.as_view(), name='account_logout'),
    path('inactive/', allauth_views.AccountInactiveView.as_view(), name='account_inactive'),
    path('signup/', allauth_views.SignupView.as_view(), name='account_signup'),
    path('reauthenticate/', allauth_views.ReauthenticateView.as_view(), name='account_reauthenticate'),
    path('email/', allauth_views.EmailView.as_view(), name='account_email'),
    path('confirm-email/', allauth_views.EmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    re_path(r'^confirm-email/(?P<key>[-:\w]+)/$', allauth_views.ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('password-change/', allauth_views.PasswordChangeView.as_view(), name='account_change_password'),
    path('password-set/', allauth_views.PasswordSetView.as_view(), name='account_set_password'),
    path('password-reset/', allauth_views.PasswordResetView.as_view(), name='account_reset_password'),
    path('password-reset/done/', allauth_views.PasswordResetDoneView.as_view(), name='account_reset_password_done'),
    re_path(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$', allauth_views.PasswordResetFromKeyView.as_view(), name="account_reset_password_from_key"),
    path('password-reset/complete/', allauth_views.PasswordResetFromKeyDoneView.as_view(), name='account_reset_password_from_key_done'),
    path('', include('chat.urls')),
]
