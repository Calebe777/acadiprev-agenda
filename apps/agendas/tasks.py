"""
Tasks Celery do app agendas.
Todas as tasks usam schema_context para isolamento multi-tenant.
"""
from celery import shared_task
from django_tenants.utils import schema_context
from django.utils import timezone


@shared_task(name='apps.agendas.tasks.verificar_atrasos')
def verificar_atrasos(schema_name: str):
    """
    Verifica blocos com mais de 15 minutos sem início e emite alerta WebSocket para o líder.
    Executado a cada 5 minutos via Celery Beat.
    """
    with schema_context(schema_name):
        from .models import BlocoHorario, RegistroAtividade
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from datetime import datetime, timedelta

        agora = timezone.now()
        limite = (agora - timedelta(minutes=15)).time()
        data_hoje = timezone.localdate()

        # Blocos que deveriam ter iniciado mas ainda estão pendentes
        blocos_atrasados = BlocoHorario.objects.filter(
            agenda__data=data_hoje,
            agenda__status='ativo',
            horario_inicio__lte=limite,
            registro__status='pendente',
        ).select_related('agenda__usuario__bu')

        layer = get_channel_layer()

        for bloco in blocos_atrasados:
            bu = bloco.agenda.usuario.bu
            if not bu:
                continue
            room = f'bu_{schema_name}_{bu.id}'
            try:
                async_to_sync(layer.group_send)(room, {
                    'type': 'lider_alerta',
                    'evento': 'lider.alerta_atraso',
                    'bloco_id': str(bloco.id),
                    'atividade': bloco.atividade,
                    'horario': bloco.horario_inicio.strftime('%H:%M'),
                    'usuario_id': str(bloco.agenda.usuario.id),
                    'usuario_nome': bloco.agenda.usuario.nome,
                    'minutos_atraso': int(
                        (agora.time().hour * 60 + agora.time().minute) -
                        (bloco.horario_inicio.hour * 60 + bloco.horario_inicio.minute)
                    ),
                })
            except Exception:
                pass

        return {'schema': schema_name, 'blocos_atrasados': blocos_atrasados.count()}


@shared_task(name='apps.agendas.tasks.notificar_inicio_bloco')
def notificar_inicio_bloco(schema_name: str):
    """
    Notifica colaboradores 5 minutos antes do início de cada bloco.
    Executado a cada 1 minuto.
    """
    with schema_context(schema_name):
        from .models import BlocoHorario
        from apps.notificacoes.models import Notificacao
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from datetime import timedelta

        agora = timezone.now()
        em_5_min = (agora + timedelta(minutes=5)).time()
        data_hoje = timezone.localdate()

        blocos = BlocoHorario.objects.filter(
            agenda__data=data_hoje,
            agenda__status='ativo',
            horario_inicio__hour=em_5_min.hour,
            horario_inicio__minute=em_5_min.minute,
            registro__status='pendente',
        ).select_related('agenda__usuario')

        layer = get_channel_layer()

        for bloco in blocos:
            usuario = bloco.agenda.usuario
            # Cria notificação persistente
            Notificacao.objects.create(
                usuario=usuario,
                tipo='bloco_inicio',
                titulo='Bloco em 5 minutos',
                mensagem=f'"{bloco.atividade}" começa às {bloco.horario_inicio.strftime("%H:%M")}',
                link=f'/agenda/{bloco.agenda.data}',
            )
            # Envia via WebSocket
            room = f'user_{schema_name}_{usuario.id}'
            try:
                async_to_sync(layer.group_send)(room, {
                    'type': 'notificacao_event',
                    'tipo': 'bloco_inicio',
                    'titulo': 'Bloco em 5 minutos',
                    'mensagem': f'"{bloco.atividade}" começa às {bloco.horario_inicio.strftime("%H:%M")}',
                })
            except Exception:
                pass


@shared_task(name='apps.agendas.tasks.criar_agendas_diarias')
def criar_agendas_diarias(schema_name: str):
    """
    Cria agendas do dia a partir do template padrão de cada BU.
    Executado às 07h45. Respeita feriados e afastamentos.
    """
    with schema_context(schema_name):
        from apps.usuarios.models import Usuario, BusinessUnit
        from apps.feriados.models import Feriado, AfastamentoColaborador
        from apps.templates_agenda.models import TemplateAgenda
        from .models import Agenda, BlocoHorario, RegistroAtividade

        data_hoje = timezone.localdate()

        # Verifica feriado
        if Feriado.objects.filter(data=data_hoje).exists():
            return {'schema': schema_name, 'motivo': 'feriado', 'agendas_criadas': 0}

        colaboradores = Usuario.objects.filter(
            ativo=True, perfil='colaborador', bu__isnull=False
        ).select_related('bu')

        criadas = 0
        for colaborador in colaboradores:
            # Verifica afastamento
            if AfastamentoColaborador.objects.filter(
                usuario=colaborador,
                data_inicio__lte=data_hoje,
                data_fim__gte=data_hoje,
            ).exists():
                continue

            # Evita duplicata
            if Agenda.objects.filter(usuario=colaborador, data=data_hoje).exists():
                continue

            # Cria agenda
            agenda = Agenda.objects.create(
                usuario=colaborador,
                data=data_hoje,
                status='rascunho',
            )

            # Aplica template padrão da BU se existir
            try:
                template = TemplateAgenda.objects.get(bu=colaborador.bu, ativo=True, padrao=True)
                for bloco_template in template.blocos.all().order_by('ordem'):
                    bloco = BlocoHorario.objects.create(
                        agenda=agenda,
                        horario_inicio=bloco_template.horario_inicio,
                        horario_fim=bloco_template.horario_fim,
                        atividade=bloco_template.atividade,
                        foco_entrega=bloco_template.foco_entrega,
                        tipo=bloco_template.tipo,
                        ordem=bloco_template.ordem,
                    )
                    RegistroAtividade.objects.create(bloco=bloco)
            except Exception:
                pass

            criadas += 1

        return {'schema': schema_name, 'agendas_criadas': criadas}
