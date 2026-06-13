"""
chat/routing.py — WebSocket URL routing (BOSQICH 0.7 skeleti).
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/chat/(?P<visitor_id>[0-9a-f-]+)/$',
        consumers.ChatConsumer.as_asgi(),
        name='ws_chat',
    ),
    re_path(
        r'ws/support/$',
        consumers.SupportConsumer.as_asgi(),
        name='ws_support',
    ),
]
