"""Serializers do app tarefas."""
from rest_framework import serializers
from apps.usuarios.serializers import UsuarioResumoSerializer
from .models import Tarefa


class TarefaSerializer(serializers.ModelSerializer):
    criado_por = UsuarioResumoSerializer(read_only=True)
    atribuido_a = UsuarioResumoSerializer(read_only=True)
    atribuido_a_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    bloco_detalhe = serializers.SerializerMethodField()
    prazo_vencido = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tarefa
        fields = [
            'id', 'titulo', 'descricao', 'status', 'prioridade',
            'criado_por', 'atribuido_a', 'atribuido_a_id',
            'bu', 'prazo', 'prazo_vencido',
            'bloco', 'bloco_detalhe',
            'ordem_kanban',
            'created_at', 'updated_at', 'concluido_em',
        ]
        read_only_fields = ['id', 'criado_por', 'created_at', 'updated_at', 'concluido_em']

    def get_bloco_detalhe(self, obj):
        if obj.bloco:
            return {
                'id': str(obj.bloco.id),
                'horario_inicio': obj.bloco.horario_inicio.strftime('%H:%M'),
                'atividade': obj.bloco.atividade,
            }
        return None

    def update(self, instance, validated_data):
        atribuido_a_id = validated_data.pop('atribuido_a_id', ...)
        if atribuido_a_id is not ...:
            from apps.usuarios.models import Usuario
            if atribuido_a_id:
                instance.atribuido_a = Usuario.objects.get(id=atribuido_a_id)
            else:
                instance.atribuido_a = None
        return super().update(instance, validated_data)


class MoverTarefaSerializer(serializers.Serializer):
    """Payload para mover tarefa entre colunas do Kanban."""
    status = serializers.ChoiceField(choices=['a_fazer', 'em_andamento', 'concluido'])
    ordem_kanban = serializers.IntegerField(min_value=0)


class ReordenarTarefasSerializer(serializers.Serializer):
    """Payload para reordenação em batch (drag-and-drop)."""

    class TarefaOrdemSerializer(serializers.Serializer):
        id = serializers.UUIDField()
        status = serializers.ChoiceField(choices=['a_fazer', 'em_andamento', 'concluido'])
        ordem_kanban = serializers.IntegerField(min_value=0)

    tarefas = TarefaOrdemSerializer(many=True)
