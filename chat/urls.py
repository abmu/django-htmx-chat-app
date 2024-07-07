from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='chat_home'),
    path('@<str:username>/', views.direct_message, name='direct_message'),
]