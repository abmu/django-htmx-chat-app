from django.urls import path, re_path
from allauth.account import views as allauth_views
from . import views

urlpatterns = [
    path('login/', allauth_views.LoginView.as_view(template_name='account/login.html', extra_context={'title': 'Login'}), name='account_login'),
    path('logout/', allauth_views.LogoutView.as_view(), name='account_logout'),
    path('inactive/', allauth_views.AccountInactiveView.as_view(), name='account_inactive'),
    path('signup/', allauth_views.SignupView.as_view(), name='account_signup'),
    path('reauthenticate/', allauth_views.ReauthenticateView.as_view(), name='account_reauthenticate'),
    path('email/', allauth_views.EmailView.as_view(), name='account_email'),
    path('confirm-email/', allauth_views.EmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    re_path(r'^confirm-email/(?P<key>[-:\w]+)/$', allauth_views.ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('password-change/', allauth_views.PasswordChangeView.as_view(), name='account_change_password'),
    path('password-reset/', allauth_views.PasswordResetView.as_view(), name='account_reset_password'),
    path('password-reset/done/', allauth_views.PasswordResetDoneView.as_view(), name='account_reset_password_done'),
    re_path(r'^password-reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$', allauth_views.PasswordResetFromKeyView.as_view(), name='account_reset_password_from_key'),
    path('password-reset/complete/', allauth_views.PasswordResetFromKeyDoneView.as_view(), name='account_reset_password_from_key_done'),
    path('friends/', views.manage_friends, name='manage_friends'),
    path('friends/all/', views.friends_list, name='friends_list'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('friends/incoming/', views.incoming_requests, name='incoming_requests'),
    path('friends/incoming/<int:user_id>/', views.handle_incoming_request, name='handle_incoming_request'),
    path('friends/outgoing/', views.outgoing_requests, name='outgoing_requests'),
    path('friends/outgoing/<int:user_id>/', views.cancel_outgoing_request, name='cancel_outgoing_request'),
    path('friends/add/', views.add_friend, name='add_friend')
]