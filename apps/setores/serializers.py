"""Serializers do app setores."""
from rest_framework import serializers
from .models import SetorConfig


class SetorConfigSerializer(serializers.ModelSerializer):
    bu_nome = serializers.CharField(source='bu.nome', read_only=True)
    bu_setor = serializers.CharField(source='bu.setor', read_only=True)

    class Meta:
        model = SetorConfig
        fields = [
            'id', 'bu', 'bu_nome', 'bu_setor',
            'tipos_atividade',
            'requer_cliente', 'requer_resultado',
            'requer_campanha', 'requer_evidencia',
            'requer_num_processo', 'requer_obs_confidencial',
            'requer_referencia_doc',
            'modo_acumulativo', 'requer_qtd_atendimentos',
            'visibilidade_restrita',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
