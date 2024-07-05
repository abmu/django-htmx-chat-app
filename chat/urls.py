from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='chat_home'),
    path('@<str:username>/', views.direct_message, name='chat_direct_message'),
    path('add/', views.add_user, name='chat_add_user'),
    path('request/incoming/<int:user_id>/', views.handle_incoming_request, name='chat_handle_incoming_request'),
    path('request/outgoing/<int:user_id>/', views.handle_outgoing_request, name='chat_handle_outgoing_request')
]