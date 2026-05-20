"""Serializers do app justificativas."""
from rest_framework import serializers
from apps.usuarios.serializers import UsuarioResumoSerializer
from apps.agendas.serializers import BlocoHorarioSerializer
from .models import Justificativa


class JustificativaSerializer(serializers.ModelSerializer):
    colaborador = UsuarioResumoSerializer(read_only=True)
    aprovado_por = UsuarioResumoSerializer(read_only=True)
    bloco_detalhe = BlocoHorarioSerializer(source='bloco', read_only=True)

    class Meta:
        model = Justificativa
        fields = [
            'id', 'bloco', 'bloco_detalhe', 'colaborador',
            'texto', 'status',
            'aprovado_por', 'comentario_lider', 'avaliado_em',
            'created_at',
        ]
        read_only_fields = ['id', 'colaborador', 'status', 'aprovado_por', 'avaliado_em', 'created_at']


class AvaliarJustificativaSerializer(serializers.Serializer):
    """Payload para aprovação ou rejeição pelo líder."""
    status = serializers.ChoiceField(choices=['aprovada', 'rejeitada'])
    comentario_lider = serializers.CharField(required=True, min_length=3)
