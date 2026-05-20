"""
WebSocket URL routing — Agenda Hora a Hora.
"""
from django.urls import re_path
from apps.agendas.consumers import BUConsumer
from apps.notificacoes.consumers import UserConsumer

websocket_urlpatterns = [
    # Canal da Business Unit — dashboard líder em tempo real
    re_path(r'^ws/bu/(?P<bu_id>[0-9a-f-]+)/$', BUConsumer.as_asgi()),

    # Canal pessoal do usuário — notificações in-app
    re_path(r'^ws/user/$', UserConsumer.as_asgi()),
]
