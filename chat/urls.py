from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='chat_home'),
    path('<uuid:uuid>/', views.direct_message, name='direct_message'),
]