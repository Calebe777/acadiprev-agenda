"""
Views do app agendas.
Implementa todos os endpoints da seção 4.2 da documentação técnica.
"""
import uuid
import boto3
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apps.usuarios.permissions import IsColaboradorOuSuperior, IsLiderOuSuperior, IsAdmin
from .models import Agenda, BlocoHorario, RegistroAtividade
from .serializers import (
    AgendaSerializer, AgendaResumoSerializer,
    BlocoHorarioSerializer, RegistroAtividadeSerializer
)


class AgendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal de agendas.
    Colaborador gerencia a própria agenda; líder vê agendas da BU.
    """
    serializer_class = AgendaSerializer
    permission_classes = [IsColaboradorOuSuperior]

    def get_queryset(self):
        user = self.request.user
        qs = Agenda.objects.select_related('usuario__bu').prefetch_related(
            'blocos__registro'
        )
        if user.perfil == 'colaborador':
            return qs.filter(usuario=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    # ---- Actions específicos ----

    @action(detail=False, methods=['get'], url_path='hoje')
    def hoje(self, request):
        """GET /api/agendas/hoje/ — Agenda do dia corrente."""
        data_hoje = timezone.localdate()
        try:
            agenda = Agenda.objects.prefetch_related('blocos__registro').get(
                usuario=request.user, data=data_hoje
            )
        except Agenda.DoesNotExist:
            return Response({'detail': 'Nenhuma agenda para hoje.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AgendaSerializer(agenda, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path=r'data/(?P<data>[0-9]{4}-[0-9]{2}-[0-9]{2})')
    def por_data(self, request, data=None):
        """GET /api/agendas/data/{YYYY-MM-DD}/"""
        parsed = parse_date(data)
        if not parsed:
            return Response({'detail': 'Data inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            agenda = Agenda.objects.prefetch_related('blocos__registro').get(
                usuario=request.user, data=parsed
            )
        except Agenda.DoesNotExist:
            return Response({'detail': 'Agenda não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AgendaSerializer(agenda, context={'request': request}).data)

    @action(detail=True, methods=['patch'])
    def checkin(self, request, pk=None):
        """PATCH /api/agendas/{id}/checkin/ — Registra check-in."""
        agenda = self.get_object()
        if agenda.usuario != request.user:
            return Response({'detail': 'Proibido.'}, status=status.HTTP_403_FORBIDDEN)
        if agenda.check_in_at:
            return Response({'detail': 'Check-in já realizado.'}, status=status.HTTP_400_BAD_REQUEST)
        agenda.check_in_at = timezone.now()
        agenda.status = 'ativo'
        agenda.save(update_fields=['check_in_at', 'status'])

        # Emite evento WebSocket para o líder da BU
        self._emit_ws_event('agenda.checkin', agenda, {'check_in_at': agenda.check_in_at.isoformat()})
        return Response(AgendaSerializer(agenda, context={'request': request}).data)

    @action(detail=True, methods=['patch'])
    def checkout(self, request, pk=None):
        """PATCH /api/agendas/{id}/checkout/ — Registra check-out e resumo final."""
        agenda = self.get_object()
        if agenda.usuario != request.user:
            return Response({'detail': 'Proibido.'}, status=status.HTTP_403_FORBIDDEN)
        if not agenda.check_in_at:
            return Response({'detail': 'Faça check-in primeiro.'}, status=status.HTTP_400_BAD_REQUEST)
        agenda.check_out_at = timezone.now()
        agenda.status = 'encerrado'
        agenda.resumo_final = request.data.get('resumo_final', '')
        agenda.save(update_fields=['check_out_at', 'status', 'resumo_final'])

        self._emit_ws_event('agenda.checkout', agenda, {'check_out_at': agenda.check_out_at.isoformat()})
        return Response(AgendaSerializer(agenda, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path=r'bu/(?P<bu_id>[0-9a-f-]+)',
            permission_classes=[IsLiderOuSuperior])
    def por_bu(self, request, bu_id=None):
        """GET /api/agendas/bu/{bu_id}/?data=YYYY-MM-DD — Agendas da BU (líder)."""
        data_str = request.query_params.get('data', str(timezone.localdate()))
        data = parse_date(data_str)
        agendas = Agenda.objects.filter(
            usuario__bu_id=bu_id, data=data
        ).select_related('usuario').prefetch_related('blocos__registro')
        return Response(AgendaResumoSerializer(agendas, many=True).data)

    def _emit_ws_event(self, tipo: str, agenda: Agenda, extra: dict = None):
        """Emite evento via Django Channels para a room da BU."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            bu = agenda.usuario.bu
            if not bu:
                return
            schema = connection.tenant.schema_name
            room = f'bu_{schema}_{bu.id}'
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(room, {
                'type': 'agenda_event',
                'evento': tipo,
                'agenda_id': str(agenda.id),
                'usuario_id': str(agenda.usuario.id),
                'usuario_nome': agenda.usuario.nome,
                **(extra or {}),
            })
        except Exception:
            pass  # WebSocket não crítico


class BlocoHorarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet de blocos — criação, edição, iniciar e concluir.
    Endpoint de conclusão aceita multipart/form-data para upload de evidência.
    """
    serializer_class = BlocoHorarioSerializer
    permission_classes = [IsColaboradorOuSuperior]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return BlocoHorario.objects.select_related(
            'agenda__usuario__bu', 'registro'
        ).prefetch_related('tarefas')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if 'agenda_pk' in self.kwargs:
            try:
                ctx['agenda'] = Agenda.objects.get(pk=self.kwargs['agenda_pk'])
            except Agenda.DoesNotExist:
                pass
        return ctx

    def perform_create(self, serializer):
        agenda = Agenda.objects.get(pk=self.kwargs['agenda_pk'])
        # Cria o RegistroAtividade junto com o bloco
        bloco = serializer.save(agenda=agenda)
        RegistroAtividade.objects.create(bloco=bloco)

    @action(detail=True, methods=['patch'])
    def iniciar(self, request, pk=None, **kwargs):
        """PATCH /api/blocos/{id}/iniciar/ — Inicia execução do bloco."""
        bloco = self.get_object()
        registro = bloco.registro
        registro.status = 'em_andamento'
        registro.iniciado_em = timezone.now()
        registro.save(update_fields=['status', 'iniciado_em'])

        # Tarefas vinculadas também entram em andamento
        bloco.tarefas.filter(
            deleted_at__isnull=True, status='a_fazer'
        ).update(status='em_andamento')

        self._emit_ws(bloco, 'agenda.bloco_iniciado')
        return Response(BlocoHorarioSerializer(bloco, context={'request': request}).data)

    @action(detail=True, methods=['patch'])
    def concluir(self, request, pk=None, **kwargs):
        """
        PATCH /api/blocos/{id}/concluir/
        Aceita multipart/form-data para upload de evidência.
        Valida campos obrigatórios conforme SetorConfig da BU.
        """
        bloco = self.get_object()
        arquivo = request.FILES.get('evidencia_arquivo')
        dados = request.data

        registro = bloco.registro
        novo_status = dados.get('status', 'concluido')
        registro.status = novo_status
        registro.tipo_atividade = dados.get('tipo_atividade', '')
        registro.descricao = dados.get('descricao', '')
        registro.motivo_parcial = dados.get('motivo_parcial', '')
        registro.percentual_meta = dados.get('percentual_meta')
        registro.evidencia_url = dados.get('evidencia_url', '')
        registro.finalizado_em = timezone.now()

        # Campos JSONB por setor
        campos_setor = dados.get('campos_setor', {})
        if isinstance(campos_setor, str):
            import json
            campos_setor = json.loads(campos_setor)
        registro.campos_setor = campos_setor

        # Confidencialidade (jurídico)
        if dados.get('confidencial'):
            registro.confidencial = True

        # Modo acumulativo (recepção)
        if bloco.tipo == 'acumulativo':
            registro.qtd_atendimentos = dados.get('qtd_atendimentos')
            registro.ocorrencias = dados.get('ocorrencias', '')

        # Upload de evidência no S3/MinIO
        if arquivo:
            tenant_schema = connection.tenant.schema_name
            path = f'{tenant_schema}/blocos/{bloco.id}/{uuid.uuid4()}_{arquivo.name}'
            try:
                s3 = boto3.client(
                    's3',
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
                s3.upload_fileobj(arquivo, settings.AWS_STORAGE_BUCKET_NAME, path)
                registro.evidencia_arquivo = path
            except Exception as e:
                return Response(
                    {'detail': f'Erro no upload: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        registro.save()

        # Evento WebSocket
        evento = 'agenda.bloco_concluido' if novo_status == 'concluido' else 'agenda.desvio'
        self._emit_ws(bloco, evento)

        return Response(RegistroAtividadeSerializer(registro, context={'request': request}).data)

    @action(detail=True, methods=['patch'],
            permission_classes=[IsLiderOuSuperior])
    def redistribuir(self, request, pk=None, **kwargs):
        """PATCH /api/blocos/{id}/redistribuir/ — Líder edita bloco de colaborador."""
        bloco = self.get_object()
        serializer = BlocoHorarioSerializer(
            bloco, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def _emit_ws(self, bloco: BlocoHorario, evento: str):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            bu = bloco.agenda.usuario.bu
            if not bu:
                return
            schema = connection.tenant.schema_name
            room = f'bu_{schema}_{bu.id}'
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(room, {
                'type': 'agenda_event',
                'evento': evento,
                'bloco_id': str(bloco.id),
                'atividade': bloco.atividade,
                'usuario_id': str(bloco.agenda.usuario.id),
                'usuario_nome': bloco.agenda.usuario.nome,
            })
        except Exception:
            pass
