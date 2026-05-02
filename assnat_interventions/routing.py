# assnat_interventions/routing.py
from django.urls import re_path
from requetes.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]