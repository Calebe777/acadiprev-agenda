"""Task Celery para verificar tarefas vencidas."""
from celery import shared_task
from django_tenants.utils import schema_context
from django.utils import timezone


@shared_task(name='apps.tarefas.tasks.verificar_tarefas_vencidas')
def verificar_tarefas_vencidas(schema_name: str):
    """
    Verifica tarefas com prazo vencido e gera alertas WebSocket + notificações in-app.
    Executado diariamente às 08h00.
    """
    with schema_context(schema_name):
        from .models import Tarefa
        from apps.notificacoes.models import Notificacao
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        hoje = timezone.localdate()
        tarefas_vencidas = Tarefa.objects.filter(
            prazo__lt=hoje,
            status__in=['a_fazer', 'em_andamento'],
            deleted_at__isnull=True,
        ).select_related('atribuido_a__bu', 'criado_por')

        layer = get_channel_layer()
        notificadas = 0

        for tarefa in tarefas_vencidas:
            usuario = tarefa.atribuido_a or tarefa.criado_por
            if not usuario:
                continue

            # Cria notificação persistente
            Notificacao.objects.get_or_create(
                usuario=usuario,
                tipo='tarefa_vencida',
                titulo='Tarefa com prazo vencido',
                mensagem=tarefa.titulo,
                defaults={'link': '/kanban', 'lida': False},
            )

            # WebSocket pessoal do usuário
            try:
                async_to_sync(layer.group_send)(
                    f'user_{schema_name}_{usuario.id}',
                    {
                        'type': 'notificacao_event',
                        'tipo': 'tarefa_vencida',
                        'titulo': 'Tarefa vencida',
                        'mensagem': tarefa.titulo,
                        'tarefa_id': str(tarefa.id),
                    }
                )
            except Exception:
                pass

            # Alerta para o líder da BU
            bu = usuario.bu
            if bu:
                try:
                    async_to_sync(layer.group_send)(
                        f'bu_{schema_name}_{bu.id}',
                        {
                            'type': 'lider_alerta',
                            'evento': 'lider.alerta_tarefa_vencida',
                            'tarefa_id': str(tarefa.id),
                            'titulo': tarefa.titulo,
                            'usuario_nome': usuario.nome,
                            'prazo': str(tarefa.prazo),
                        }
                    )
                except Exception:
                    pass

            notificadas += 1

        return {'schema': schema_name, 'tarefas_vencidas': notificadas}
