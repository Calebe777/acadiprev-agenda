"""Serializers do app usuarios."""
from rest_framework import serializers
from .models import BusinessUnit, Usuario


class BusinessUnitSerializer(serializers.ModelSerializer):
    lider_nome = serializers.CharField(source='lider.nome', read_only=True)
    membros_count = serializers.SerializerMethodField()

    class Meta:
        model = BusinessUnit
        fields = [
            'id', 'nome', 'codigo', 'setor', 'ativo',
            'lider', 'lider_nome', 'membros_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_membros_count(self, obj):
        return obj.membros.filter(ativo=True).count()


class UsuarioResumoSerializer(serializers.ModelSerializer):
    """Serializer leve para uso em relacionamentos (atribuido_a, lider, etc.)."""
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'perfil']


class UsuarioSerializer(serializers.ModelSerializer):
    bu_nome = serializers.CharField(source='bu.nome', read_only=True)
    bu_setor = serializers.CharField(source='bu.setor', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'nome', 'email', 'perfil', 'ativo',
            'bu', 'bu_nome', 'bu_setor',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UsuarioCreateSerializer(UsuarioSerializer):
    """Serializer para criação de usuário com senha obrigatória."""
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta(UsuarioSerializer.Meta):
        fields = UsuarioSerializer.Meta.fields + ['password']
