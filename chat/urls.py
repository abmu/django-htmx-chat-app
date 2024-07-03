from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='chat_home'),
    path('@<str:username>/', views.direct_message, name='chat_direct_message'),
    path('add/', views.add_user, name='chat_add_user')
]