"""Serializers do app notificacoes."""
from rest_framework import serializers
from .models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'titulo', 'mensagem', 'lida', 'link', 'created_at']
        read_only_fields = ['id', 'tipo', 'titulo', 'mensagem', 'link', 'created_at']
