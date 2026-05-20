"""
Views do app tarefas — Kanban completo.
Implementa todos os endpoints da seção 4.3 da documentação técnica.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.permissions import IsColaboradorOuSuperior, IsLiderOuSuperior
from .models import Tarefa
from .serializers import TarefaSerializer, MoverTarefaSerializer, ReordenarTarefasSerializer


class TarefaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo do Kanban de tarefas.
    Colaborador gerencia as próprias; líder gerencia o time da BU.
    """
    serializer_class = TarefaSerializer
    permission_classes = [IsColaboradorOuSuperior]

    def get_queryset(self):
        user = self.request.user
        qs = Tarefa.objects.filter(deleted_at__isnull=True).select_related(
            'criado_por', 'atribuido_a', 'bu', 'bloco'
        )
        if user.perfil == 'colaborador':
            qs = qs.filter(atribuido_a=user)
        elif user.perfil == 'lider':
            qs = qs.filter(bu=user.bu)

        # Filtros opcionais
        status_f = self.request.query_params.get('status')
        prioridade_f = self.request.query_params.get('prioridade')
        prazo_f = self.request.query_params.get('prazo')
        if status_f:
            qs = qs.filter(status=status_f)
        if prioridade_f:
            qs = qs.filter(prioridade=prioridade_f)
        if prazo_f:
            qs = qs.filter(prazo=prazo_f)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        atribuido_a = serializer.validated_data.get('atribuido_a_id') or user
        bu = user.bu
        tarefa = serializer.save(
            criado_por=user,
            atribuido_a_id=atribuido_a if isinstance(atribuido_a, str) else user.id,
            bu=bu,
        )
        # Notifica se atribuída a outro
        if tarefa.atribuido_a and tarefa.atribuido_a != user:
            self._notificar_atribuicao(tarefa)

    def destroy(self, request, *args, **kwargs):
        """Soft delete — não remove do banco."""
        tarefa = self.get_object()
        tarefa.deleted_at = timezone.now()
        tarefa.save(update_fields=['deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'])
    def mover(self, request, pk=None):
        """PATCH /api/tarefas/{id}/mover/ — Move entre colunas do Kanban."""
        tarefa = self.get_object()
        serializer = MoverTarefaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        novo_status = serializer.validated_data['status']
        if novo_status == 'concluido' and tarefa.status != 'concluido':
            tarefa.concluido_em = timezone.now()

        tarefa.status = novo_status
        tarefa.ordem_kanban = serializer.validated_data['ordem_kanban']
        tarefa.save(update_fields=['status', 'ordem_kanban', 'concluido_em'])

        # Emite evento WebSocket para o time
        self._emit_kanban_update(tarefa)
        return Response(TarefaSerializer(tarefa).data)

    @action(detail=False, methods=['patch'])
    def reordenar(self, request):
        """
        PATCH /api/tarefas/reordenar/
        Reordena múltiplas tarefas em batch — executado em transação única.
        """
        serializer = ReordenarTarefasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tarefas_data = serializer.validated_data['tarefas']
        ids = [str(t['id']) for t in tarefas_data]
        tarefas_map = {
            str(t.id): t
            for t in Tarefa.objects.filter(id__in=ids, deleted_at__isnull=True)
        }

        with transaction.atomic():
            for item in tarefas_data:
                tarefa = tarefas_map.get(str(item['id']))
                if not tarefa:
                    continue
                tarefa.status = item['status']
                tarefa.ordem_kanban = item['ordem_kanban']
                if item['status'] == 'concluido' and tarefa.concluido_em is None:
                    tarefa.concluido_em = timezone.now()
                tarefa.save(update_fields=['status', 'ordem_kanban', 'concluido_em'])

        return Response({'reordenadas': len(tarefas_data)})

    @action(detail=True, methods=['patch'])
    def vincular_bloco(self, request, pk=None):
        """PATCH /api/tarefas/{id}/vincular-bloco/ — Vincula tarefa a um bloco."""
        tarefa = self.get_object()
        bloco_id = request.data.get('bloco_id')
        if not bloco_id:
            return Response({'detail': 'bloco_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        from apps.agendas.models import BlocoHorario
        try:
            bloco = BlocoHorario.objects.get(pk=bloco_id)
        except BlocoHorario.DoesNotExist:
            return Response({'detail': 'Bloco não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        tarefa.bloco = bloco
        tarefa.save(update_fields=['bloco'])
        return Response(TarefaSerializer(tarefa).data)

    @action(detail=True, methods=['patch'])
    def desvincular(self, request, pk=None):
        """PATCH /api/tarefas/{id}/desvincular/ — Remove vínculo com bloco."""
        tarefa = self.get_object()
        tarefa.bloco = None
        tarefa.save(update_fields=['bloco'])
        return Response(TarefaSerializer(tarefa).data)

    @action(detail=False, methods=['get'], url_path=r'bu/(?P<bu_id>[0-9a-f-]+)',
            permission_classes=[IsLiderOuSuperior])
    def por_bu(self, request, bu_id=None):
        """GET /api/tarefas/bu/{bu_id}/ — Tarefas do time (visão do líder)."""
        qs = Tarefa.objects.filter(bu_id=bu_id, deleted_at__isnull=True).select_related(
            'criado_por', 'atribuido_a', 'bloco'
        )
        return Response(TarefaSerializer(qs, many=True).data)

    @action(detail=False, methods=['post'], url_path='atribuir',
            permission_classes=[IsLiderOuSuperior])
    def atribuir(self, request):
        """POST /api/tarefas/atribuir/ — Líder cria e atribui tarefa ao colaborador."""
        serializer = TarefaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tarefa = serializer.save(
            criado_por=request.user,
            bu=request.user.bu,
        )
        self._notificar_atribuicao(tarefa)
        return Response(TarefaSerializer(tarefa).data, status=status.HTTP_201_CREATED)

    def _notificar_atribuicao(self, tarefa: Tarefa):
        try:
            from apps.notificacoes.models import Notificacao
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from django.db import connection

            schema = connection.tenant.schema_name
            usuario = tarefa.atribuido_a
            Notificacao.objects.create(
                usuario=usuario,
                tipo='tarefa_atribuida',
                titulo='Nova tarefa atribuída',
                mensagem=tarefa.titulo,
                link='/kanban',
            )
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'user_{schema}_{usuario.id}',
                {
                    'type': 'notificacao_event',
                    'tipo': 'tarefa_atribuida',
                    'titulo': 'Nova tarefa atribuída',
                    'mensagem': tarefa.titulo,
                }
            )
        except Exception:
            pass

    def _emit_kanban_update(self, tarefa: Tarefa):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from django.db import connection

            if not tarefa.bu:
                return
            schema = connection.tenant.schema_name
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'bu_{schema}_{tarefa.bu_id}',
                {
                    'type': 'kanban_atualizado',
                    'evento': 'kanban.atualizado',
                    'tarefa_id': str(tarefa.id),
                    'novo_status': tarefa.status,
                }
            )
        except Exception:
            pass
