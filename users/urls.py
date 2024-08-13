from django.urls import path, re_path
from django.contrib.auth.decorators import login_not_required
from allauth.account import views as allauth_views
from . import views

urlpatterns = [
    path('login/', login_not_required(allauth_views.LoginView.as_view(template_name='account/login.html', extra_context={'title': 'Login'})), name='account_login'),
    path('logout/', login_not_required(allauth_views.LogoutView.as_view(extra_context={'title': 'Logout'})), name='account_logout'),
    path('inactive/', login_not_required(allauth_views.AccountInactiveView.as_view(extra_context={'title': 'Account inactive'})), name='account_inactive'),
    path('signup/', login_not_required(allauth_views.SignupView.as_view(extra_context={'title': 'Signup'})), name='account_signup'),
    path('reauthenticate/', allauth_views.ReauthenticateView.as_view(extra_context={'title': 'Reauthenticate'}), name='account_reauthenticate'),
    path('confirm-email/', login_not_required(allauth_views.EmailVerificationSentView.as_view(extra_context={'title': 'Email verification sent'})), name='account_email_verification_sent'),
    re_path(r'^confirm-email/(?P<key>[-:\w]+)/$', login_not_required(allauth_views.ConfirmEmailView.as_view(extra_context={'title': 'Confirm email address'})), name='account_confirm_email'),
    path('password-reset/', login_not_required(allauth_views.PasswordResetView.as_view(extra_context={'title': 'Request password reset'})), name='account_reset_password'),
    path('password-reset/done/', login_not_required(allauth_views.PasswordResetDoneView.as_view(extra_context={'title': 'Password reset sent'})), name='account_reset_password_done'),
    re_path(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$', login_not_required(allauth_views.PasswordResetFromKeyView.as_view(extra_context={'title': 'Reset password'})), name='account_reset_password_from_key'),
    path('password-reset/complete/', login_not_required(allauth_views.PasswordResetFromKeyDoneView.as_view(extra_context={'title': 'Password reset complete'})), name='account_reset_password_from_key_done'),
    path('friends/', views.manage_friends, name='manage_friends'),
    path('friends/all/', views.friends_list, name='friends_list'),
    path('friends/remove/<str:username>/', views.remove_friend, name='remove_friend'),
    path('friends/incoming/', views.incoming_requests, name='incoming_requests'),
    path('friends/incoming/<str:username>/', views.handle_incoming_request, name='handle_incoming_request'),
    path('friends/outgoing/', views.outgoing_requests, name='outgoing_requests'),
    path('friends/outgoing/<str:username>/', views.cancel_outgoing_request, name='cancel_outgoing_request'),
    path('friends/add/', views.add_friend, name='add_friend'),
    path('settings/', views.settings, name='settings'),
    path('settings/email/', allauth_views.EmailView.as_view(extra_context={'title': 'Change email address'}), name='account_email'),
    path('settings/password/', allauth_views.PasswordChangeView.as_view(extra_context={'title': 'Change password'}), name='account_change_password'),
    path('settings/delete/', views.delete_account, name='delete_account')
]