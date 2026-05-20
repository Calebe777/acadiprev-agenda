"""Views do app justificativas."""
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.permissions import IsColaboradorOuSuperior, IsLiderOuSuperior, IsRHOuSuperior
from .models import Justificativa
from .serializers import JustificativaSerializer, AvaliarJustificativaSerializer


class JustificativaViewSet(viewsets.ModelViewSet):
    serializer_class = JustificativaSerializer
    permission_classes = [IsColaboradorOuSuperior]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = Justificativa.objects.select_related(
            'colaborador__bu', 'aprovado_por', 'bloco__agenda'
        )
        if user.perfil == 'colaborador':
            return qs.filter(colaborador=user)
        if user.perfil == 'lider':
            return qs.filter(colaborador__bu=user.bu)
        return qs

    def perform_create(self, serializer):
        justificativa = serializer.save(colaborador=self.request.user)
        # Notifica líder via WebSocket
        self._notificar_lider(justificativa)

    @action(detail=False, methods=['get'], permission_classes=[IsLiderOuSuperior])
    def pendentes(self, request):
        """GET /api/justificativas/pendentes/ — Pendentes na BU do líder."""
        qs = Justificativa.objects.filter(
            status='pendente',
            colaborador__bu=request.user.bu,
        ).select_related('colaborador', 'bloco')
        return Response(JustificativaSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsRHOuSuperior])
    def historico(self, request):
        """GET /api/justificativas/historico/ — Histórico completo para RH."""
        qs = self.get_queryset()
        colaborador = request.query_params.get('colaborador')
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        if colaborador:
            qs = qs.filter(colaborador_id=colaborador)
        if data_inicio:
            qs = qs.filter(created_at__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(created_at__date__lte=data_fim)
        return Response(JustificativaSerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsLiderOuSuperior])
    def avaliar(self, request, pk=None):
        """PATCH /api/justificativas/{id}/avaliar/ — Aprova ou rejeita."""
        justificativa = self.get_object()
        if justificativa.status != 'pendente':
            return Response({'detail': 'Justificativa já avaliada.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AvaliarJustificativaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        justificativa.status = serializer.validated_data['status']
        justificativa.comentario_lider = serializer.validated_data['comentario_lider']
        justificativa.aprovado_por = request.user
        justificativa.avaliado_em = timezone.now()
        justificativa.save()

        # Notifica colaborador
        self._notificar_colaborador(justificativa)
        return Response(JustificativaSerializer(justificativa).data)

    def _notificar_lider(self, justificativa: Justificativa):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from django.db import connection

            bu = justificativa.colaborador.bu
            if not bu:
                return
            schema = connection.tenant.schema_name
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'bu_{schema}_{bu.id}',
                {
                    'type': 'agenda_event',
                    'evento': 'justificativa.nova',
                    'justificativa_id': str(justificativa.id),
                    'colaborador_nome': justificativa.colaborador.nome,
                }
            )
        except Exception:
            pass

    def _notificar_colaborador(self, justificativa: Justificativa):
        try:
            from apps.notificacoes.models import Notificacao
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            from django.db import connection

            schema = connection.tenant.schema_name
            status_label = 'aprovada' if justificativa.status == 'aprovada' else 'rejeitada'
            Notificacao.objects.create(
                usuario=justificativa.colaborador,
                tipo='justificativa_avaliada',
                titulo=f'Justificativa {status_label}',
                mensagem=justificativa.comentario_lider,
                link='/justificativas',
            )
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'user_{schema}_{justificativa.colaborador.id}',
                {
                    'type': 'notificacao_event',
                    'tipo': 'justificativa_avaliada',
                    'titulo': f'Justificativa {status_label}',
                    'mensagem': justificativa.comentario_lider,
                }
            )
        except Exception:
            pass
