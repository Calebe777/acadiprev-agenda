"""WebSocket consumers do app agendas."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class BUConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para o dashboard do líder.
    Room: bu_{schema}_{bu_id}
    Recebe eventos: checkin, bloco_iniciado, bloco_concluido, desvio, alerta_atraso, checkout.
    """

    async def connect(self):
        user = self.scope.get('user')
        tenant = self.scope.get('tenant')

        # Apenas líderes e admins conectam ao canal de BU
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        perfil = await self._get_perfil(user)
        if perfil not in ('lider', 'admin', 'rh', 'diretoria'):
            await self.close(code=4003)
            return

        bu_id = self.scope['url_route']['kwargs']['bu_id']
        schema = tenant.schema_name if tenant else 'public'
        self.room = f'bu_{schema}_{bu_id}'

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

        await self.send(json.dumps({
            'tipo': 'conexao_estabelecida',
            'room': self.room,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room'):
            await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data):
        """Líder pode enviar ping ou comandos de redistribuição via WS."""
        try:
            data = json.loads(text_data)
            if data.get('tipo') == 'ping':
                await self.send(json.dumps({'tipo': 'pong'}))
        except Exception:
            pass

    # ---- Event handlers (disparados por group_send) ----

    async def agenda_event(self, event):
        """Repassa qualquer evento de agenda para o cliente."""
        await self.send(json.dumps(event))

    async def lider_alerta(self, event):
        """Repassa alertas do Celery (atraso, tarefa vencida)."""
        await self.send(json.dumps(event))

    async def kanban_atualizado(self, event):
        """Atualização no kanban da BU."""
        await self.send(json.dumps(event))

    @database_sync_to_async
    def _get_perfil(self, user):
        return user.perfil
