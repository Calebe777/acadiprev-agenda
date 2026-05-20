"""
Celery app — Agenda Hora a Hora.
Todas as tasks usam schema_context(schema_name) para isolamento multi-tenant.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acadiprev.settings.development')

app = Celery('acadiprev')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Registra tarefas periódicas para cada tenant ativo.
    Em produção, use django-celery-beat para gerenciar via admin.
    """
    from django_tenants.utils import get_tenant_model
    TenantModel = get_tenant_model()

    try:
        tenants = TenantModel.objects.exclude(schema_name='public')
        for tenant in tenants:
            schema = tenant.schema_name

            # Verificar atrasos de blocos — a cada 5 minutos
            sender.add_periodic_task(
                300.0,
                verificar_atrasos_task.s(schema),
                name=f'verificar_atrasos_{schema}',
            )

            # Notificar início de bloco — a cada 1 minuto
            sender.add_periodic_task(
                60.0,
                notificar_inicio_bloco_task.s(schema),
                name=f'notificar_inicio_bloco_{schema}',
            )

            # Criar agendas diárias — 07h45 todo dia útil
            sender.add_periodic_task(
                crontab(hour=7, minute=45),
                criar_agendas_diarias_task.s(schema),
                name=f'criar_agendas_diarias_{schema}',
            )

            # Verificar tarefas vencidas — 08h00 todo dia
            sender.add_periodic_task(
                crontab(hour=8, minute=0),
                verificar_tarefas_vencidas_task.s(schema),
                name=f'verificar_tarefas_vencidas_{schema}',
            )

            # Limpar tokens expirados — 03h00 todo dia
            sender.add_periodic_task(
                crontab(hour=3, minute=0),
                limpar_tokens_expirados_task.s(schema),
                name=f'limpar_tokens_{schema}',
            )
    except Exception:
        pass  # Tabela pode não existir ainda (primeira migração)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Importações lazy para evitar circular imports
@app.task(name='apps.agendas.tasks.verificar_atrasos')
def verificar_atrasos_task(schema_name):
    from apps.agendas.tasks import verificar_atrasos
    verificar_atrasos(schema_name)


@app.task(name='apps.agendas.tasks.notificar_inicio_bloco')
def notificar_inicio_bloco_task(schema_name):
    from apps.agendas.tasks import notificar_inicio_bloco
    notificar_inicio_bloco(schema_name)


@app.task(name='apps.agendas.tasks.criar_agendas_diarias')
def criar_agendas_diarias_task(schema_name):
    from apps.agendas.tasks import criar_agendas_diarias
    criar_agendas_diarias(schema_name)


@app.task(name='apps.tarefas.tasks.verificar_tarefas_vencidas')
def verificar_tarefas_vencidas_task(schema_name):
    from apps.tarefas.tasks import verificar_tarefas_vencidas
    verificar_tarefas_vencidas(schema_name)


@app.task(name='apps.tenants.tasks.limpar_tokens_expirados')
def limpar_tokens_expirados_task(schema_name):
    from apps.tenants.tasks import limpar_tokens_expirados
    limpar_tokens_expirados(schema_name)
