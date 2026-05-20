"""Serializers do app agendas."""
from rest_framework import serializers
from django.utils import timezone

from apps.usuarios.serializers import UsuarioResumoSerializer
from .models import Agenda, BlocoHorario, RegistroAtividade


class RegistroAtividadeSerializer(serializers.ModelSerializer):
    """
    Serializer com filtragem de campos confidenciais para o setor Jurídico.
    Colaboradores externos ao setor jurídico não veem campos_setor nem descricao
    quando confidencial=True.
    """

    class Meta:
        model = RegistroAtividade
        fields = [
            'id', 'status', 'tipo_atividade', 'descricao', 'motivo_parcial',
            'percentual_meta', 'campos_setor', 'evidencia_url', 'evidencia_arquivo',
            'confidencial', 'qtd_atendimentos', 'ocorrencias',
            'iniciado_em', 'finalizado_em', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request else None

        if instance.confidencial and user and user.is_authenticated:
            e_lider_juridico = (
                user.perfil in ('lider', 'admin') and
                user.bu and user.bu.setor == 'juridico'
            )
            if not e_lider_juridico and user.perfil != 'admin':
                data.pop('campos_setor', None)
                data['descricao'] = '— conteúdo restrito —'

        return data


class BlocoHorarioSerializer(serializers.ModelSerializer):
    registro = RegistroAtividadeSerializer(read_only=True)
    duracao_minutos = serializers.IntegerField(read_only=True)
    tarefas_count = serializers.SerializerMethodField()

    class Meta:
        model = BlocoHorario
        fields = [
            'id', 'horario_inicio', 'horario_fim', 'atividade', 'foco_entrega',
            'tipo', 'turno', 'ordem', 'duracao_minutos',
            'registro', 'tarefas_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tarefas_count(self, obj):
        return obj.tarefas.filter(deleted_at__isnull=True).count() if hasattr(obj, 'tarefas') else 0

    def validate(self, attrs):
        """Valida que blocos não se sobrepõem na mesma agenda."""
        agenda = self.context.get('agenda') or (self.instance.agenda if self.instance else None)
        if not agenda:
            return attrs

        inicio = attrs.get('horario_inicio', getattr(self.instance, 'horario_inicio', None))
        fim = attrs.get('horario_fim', getattr(self.instance, 'horario_fim', None))

        if not inicio or not fim:
            return attrs

        conflitos = BlocoHorario.objects.filter(
            agenda=agenda,
            horario_inicio__lt=fim,
            horario_fim__gt=inicio,
        )
        if self.instance:
            conflitos = conflitos.exclude(pk=self.instance.pk)

        if conflitos.exists():
            raise serializers.ValidationError(
                'Horário conflita com outro bloco já existente na agenda.'
            )
        return attrs


class AgendaSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumoSerializer(read_only=True)
    blocos = BlocoHorarioSerializer(many=True, read_only=True)
    blocos_count = serializers.IntegerField(source='blocos.count', read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()

    class Meta:
        model = Agenda
        fields = [
            'id', 'usuario', 'data', 'status', 'meta_dia',
            'check_in_at', 'check_out_at', 'resumo_final',
            'blocos', 'blocos_count', 'percentual_conclusao',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'usuario', 'created_at', 'updated_at']

    def get_percentual_conclusao(self, obj):
        blocos = obj.blocos.all()
        total = blocos.count()
        if not total:
            return 0
        concluidos = sum(
            1 for b in blocos
            if hasattr(b, 'registro') and b.registro.status == 'concluido'
        )
        return round((concluidos / total) * 100)


class AgendaResumoSerializer(serializers.ModelSerializer):
    """Versão leve para listagem da BU pelo líder."""
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()
    blocos_pendentes = serializers.SerializerMethodField()

    class Meta:
        model = Agenda
        fields = [
            'id', 'usuario', 'usuario_nome', 'data', 'status',
            'check_in_at', 'check_out_at',
            'percentual_conclusao', 'blocos_pendentes',
        ]

    def get_percentual_conclusao(self, obj):
        blocos = obj.blocos.all()
        total = blocos.count()
        if not total:
            return 0
        concluidos = sum(
            1 for b in blocos
            if hasattr(b, 'registro') and b.registro.status == 'concluido'
        )
        return round((concluidos / total) * 100)

    def get_blocos_pendentes(self, obj):
        return obj.blocos.filter(registro__status='pendente').count()
