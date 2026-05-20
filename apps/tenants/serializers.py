"""Serializers do app tenants."""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_tenants.utils import get_tenant_model

from .models import Tenant


class TenantConfigSerializer(serializers.ModelSerializer):
    """Retorna configurações públicas do tenant (cor, logo, nome)."""

    class Meta:
        model = Tenant
        fields = ['nome', 'cor_primaria', 'logo_url']


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT customizado — adiciona schema_name e perfil do usuário no payload.
    Token gerado para AcadiPrev é rejeitado ao tentar usar no endpoint Carvalho.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Injeta schema do tenant no payload
        from django.db import connection
        token['schema_name'] = connection.tenant.schema_name
        token['tenant_nome'] = connection.tenant.nome
        token['perfil'] = user.perfil
        token['nome'] = user.nome
        token['bu_id'] = str(user.bu_id) if user.bu_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Verifica que o usuário pertence ao schema atual
        from django.db import connection
        if not self.user.ativo:
            raise serializers.ValidationError('Usuário inativo.')
        return data
