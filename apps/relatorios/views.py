"""
App: relatorios — TENANT APP
Views de relatórios e task de exportação assíncrona (WeasyPrint + openpyxl).
"""
import uuid
import json
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.usuarios.permissions import (
    IsColaboradorOuSuperior, IsLiderOuSuperior,
    IsRHOuSuperior, IsDiretoriaOuAdmin
)


@api_view(['GET'])
@permission_classes([IsColaboradorOuSuperior])
def meu_desempenho(request):
    """
    GET /api/relatorios/meu-desempenho/?periodo=semana|mes
    Histórico pessoal: % blocos concluídos por semana/mês.
    """
    from apps.agendas.models import Agenda, BlocoHorario, RegistroAtividade
    from datetime import timedelta

    periodo = request.query_params.get('periodo', 'semana')
    hoje = timezone.localdate()

    if periodo == 'mes':
        inicio = hoje.replace(day=1)
    else:
        inicio = hoje - timedelta(days=7)

    agendas = Agenda.objects.filter(
        usuario=request.user, data__range=(inicio, hoje)
    ).prefetch_related('blocos__registro')

    total_blocos = 0
    concluidos = 0
    parciais = 0
    nao_realizados = 0
    por_dia = []
    checkins_pontuais = 0
    total_checkins = 0

    for agenda in agendas:
        dia_total = agenda.blocos.count()
        dia_concluidos = 0
        for bloco in agenda.blocos.all():
            if hasattr(bloco, 'registro'):
                s = bloco.registro.status
                total_blocos += 1
                if s == 'concluido':
                    concluidos += 1
                    dia_concluidos += 1
                elif s == 'parcial':
                    parciais += 1
                elif s == 'nao_realizado':
                    nao_realizados += 1

        # Verifica pontualidade do check-in
        if agenda.check_in_at:
            total_checkins += 1
            primeiro_bloco = agenda.blocos.order_by('horario_inicio').first()
            if primeiro_bloco and agenda.check_in_at.time() <= primeiro_bloco.horario_inicio:
                checkins_pontuais += 1

        por_dia.append({
            'data': str(agenda.data),
            'concluidos': dia_concluidos,
            'total': dia_total,
            'pct': round((dia_concluidos / dia_total * 100) if dia_total else 0),
        })

    return Response({
        'colaborador': {'id': str(request.user.id), 'nome': request.user.nome},
        'periodo': {'inicio': str(inicio), 'fim': str(hoje)},
        'resumo': {
            'total_blocos_planejados': total_blocos,
            'blocos_concluidos': concluidos,
            'blocos_parciais': parciais,
            'blocos_nao_realizados': nao_realizados,
            'percentual_conclusao': round((concluidos / total_blocos * 100) if total_blocos else 0),
            'media_checkin_pontual': round((checkins_pontuais / total_checkins * 100) if total_checkins else 0),
        },
        'por_dia': sorted(por_dia, key=lambda x: x['data']),
    })


@api_view(['GET'])
@permission_classes([IsRHOuSuperior])
def frequencia(request):
    """GET /api/relatorios/frequencia/ — Frequência e pontualidade por colaborador."""
    from apps.agendas.models import Agenda
    from apps.usuarios.models import Usuario

    data_inicio = request.query_params.get('data_inicio', str(timezone.localdate().replace(day=1)))
    data_fim = request.query_params.get('data_fim', str(timezone.localdate()))
    bu_id = request.query_params.get('bu_id')

    usuarios = Usuario.objects.filter(ativo=True, perfil='colaborador')
    if bu_id:
        usuarios = usuarios.filter(bu_id=bu_id)

    resultado = []
    for usuario in usuarios:
        agendas = Agenda.objects.filter(
            usuario=usuario, data__range=(data_inicio, data_fim)
        )
        resultado.append({
            'usuario': {'id': str(usuario.id), 'nome': usuario.nome, 'bu': usuario.bu.nome if usuario.bu else None},
            'dias_trabalhados': agendas.filter(check_in_at__isnull=False).count(),
            'dias_planejados': agendas.count(),
            'checkins_no_prazo': agendas.filter(check_in_at__isnull=False).count(),
        })

    return Response({'periodo': {'inicio': data_inicio, 'fim': data_fim}, 'colaboradores': resultado})


@api_view(['GET'])
@permission_classes([IsLiderOuSuperior])
def desempenho_bu(request):
    """GET /api/relatorios/bu/ — Comparativo de desempenho da BU."""
    from apps.agendas.models import Agenda
    from apps.usuarios.models import Usuario

    bu_id = request.query_params.get('bu_id') or (str(request.user.bu_id) if request.user.bu else None)
    data_inicio = request.query_params.get('data_inicio', str(timezone.localdate().replace(day=1)))
    data_fim = request.query_params.get('data_fim', str(timezone.localdate()))

    if not bu_id:
        return Response({'detail': 'bu_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

    usuarios = Usuario.objects.filter(bu_id=bu_id, ativo=True)
    resultado = []
    for usuario in usuarios:
        agendas = Agenda.objects.filter(
            usuario=usuario, data__range=(data_inicio, data_fim)
        ).prefetch_related('blocos__registro')
        total = concluidos = 0
        for agenda in agendas:
            for bloco in agenda.blocos.all():
                total += 1
                if hasattr(bloco, 'registro') and bloco.registro.status == 'concluido':
                    concluidos += 1
        resultado.append({
            'usuario': usuario.nome,
            'total_blocos': total,
            'concluidos': concluidos,
            'pct': round(concluidos / total * 100 if total else 0),
        })

    return Response({'bu_id': bu_id, 'periodo': {'inicio': data_inicio, 'fim': data_fim}, 'colaboradores': resultado})


@api_view(['GET'])
@permission_classes([IsDiretoriaOuAdmin])
def executivo(request):
    """GET /api/relatorios/executivo/ — Painel consolidado por setor e BU."""
    from apps.usuarios.models import BusinessUnit

    bus = BusinessUnit.objects.filter(ativo=True).prefetch_related('membros')
    resultado = []
    for bu in bus:
        total_membros = bu.membros.filter(ativo=True).count()
        resultado.append({'bu': bu.nome, 'setor': bu.setor, 'total_membros': total_membros})

    return Response({'setores': resultado, 'gerado_em': timezone.now().isoformat()})


@api_view(['POST'])
@permission_classes([IsRHOuSuperior])
def exportar_relatorio(request):
    """
    POST /api/relatorios/exportar/
    Inicia geração assíncrona de PDF ou Excel via Celery.
    Response 202: { task_id, status }
    """
    from .tasks import gerar_relatorio_exportacao

    tipo = request.data.get('tipo', 'frequencia')
    formato = request.data.get('formato', 'pdf')
    params = {
        'periodo_inicio': request.data.get('periodo_inicio'),
        'periodo_fim': request.data.get('periodo_fim'),
        'bu_id': request.data.get('bu_id'),
    }

    schema = connection.tenant.schema_name
    task = gerar_relatorio_exportacao.delay(schema, tipo, formato, params)

    return Response({'task_id': task.id, 'status': 'processando'}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsRHOuSuperior])
def status_exportacao(request, task_id):
    """
    GET /api/relatorios/exportar/{task_id}/
    Consulta status da exportação e retorna URL quando concluída.
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id)
    if result.ready():
        if result.successful():
            return Response({'status': 'concluido', 'url': result.result, 'expira_em': None})
        return Response({'status': 'erro', 'detalhe': str(result.result)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'status': 'processando'})
