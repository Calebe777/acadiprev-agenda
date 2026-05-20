"""URLs do app notificacoes."""
from django.urls import path
from .views import listar_notificacoes, marcar_lida, marcar_todas_lidas

urlpatterns = [
    path('notificacoes/', listar_notificacoes, name='notificacoes-list'),
    path('notificacoes/<uuid:pk>/lida/', marcar_lida, name='notificacao-lida'),
    path('notificacoes/marcar-todas-lidas/', marcar_todas_lidas, name='notificacoes-todas-lidas'),
]
