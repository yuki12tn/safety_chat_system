from django.urls import path
from . import views

urlpatterns = [
    path('', views.connect_view, name='connect'),
    path('chat/', views.chat_view, name='chat'),
    path('send_message/', views.send_message, name='send_message'),
    path('get_messages/', views.get_messages, name='get_messages'),
    path('get_client_info/', views.get_client_info, name='get_client_info'), 
    path('get_peer_info/', views.get_peer_info, name='get_peer_info'),
    path('disconnect/', views.disconnect, name='disconnect'),
]