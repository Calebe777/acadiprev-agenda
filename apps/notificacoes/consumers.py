"""WebSocket consumer pessoal do usuário — notificações in-app."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class UserConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para notificações pessoais do usuário.
    Room: user_{schema}_{user_id}
    """

    async def connect(self):
        user = self.scope.get('user')
        tenant = self.scope.get('tenant')

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        schema = tenant.schema_name if tenant else 'public'
        self.room = f'user_{schema}_{user.id}'

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

        # Envia notificações não lidas ao conectar
        nao_lidas = await self._get_nao_lidas(user)
        if nao_lidas:
            await self.send(json.dumps({
                'tipo': 'notificacoes_pendentes',
                'notificacoes': nao_lidas,
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room'):
            await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('tipo') == 'marcar_lida':
                await self._marcar_lida(data.get('id'))
        except Exception:
            pass

    async def notificacao_event(self, event):
        """Repassa nova notificação para o cliente."""
        await self.send(json.dumps({
            'tipo': 'nova_notificacao',
            **event,
        }))

    @database_sync_to_async
    def _get_nao_lidas(self, user):
        from apps.notificacoes.models import Notificacao
        notifs = Notificacao.objects.filter(usuario=user, lida=False).order_by('-created_at')[:10]
        return [
            {'id': str(n.id), 'tipo': n.tipo, 'titulo': n.titulo, 'mensagem': n.mensagem, 'link': n.link}
            for n in notifs
        ]

    @database_sync_to_async
    def _marcar_lida(self, notificacao_id):
        from apps.notificacoes.models import Notificacao
        if notificacao_id:
            Notificacao.objects.filter(id=notificacao_id).update(lida=True)
