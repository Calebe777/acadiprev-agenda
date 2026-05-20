"""
Middleware customizados — Agenda Hora a Hora.
- AuditMiddleware: registra IP e user-agent em requests autenticados
- JWTAuthMiddlewareStack: autenticação JWT para WebSocket consumers
- TenantChannelsMiddleware: injeta tenant no scope do WebSocket
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """Registra ações de usuários autenticados para auditoria."""

    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                logger.info(
                    'audit',
                    extra={
                        'user_id': str(request.user.id),
                        'method': request.method,
                        'path': request.path,
                        'status': response.status_code,
                        'ip': self._get_client_ip(request),
                    }
                )
        return response

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# ============================================================
# WebSocket Middlewares
# ============================================================

@database_sync_to_async
def get_user_from_token(token_key):
    """Valida JWT e retorna o usuário correspondente."""
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from apps.usuarios.models import Usuario

        token = AccessToken(token_key)
        user_id = token['user_id']
        return Usuario.objects.get(id=user_id, ativo=True)
    except Exception:
        return AnonymousUser()


@database_sync_to_async
def get_tenant_from_scope(scope):
    """Resolve o tenant a partir do host do WebSocket."""
    try:
        from django_tenants.utils import get_tenant_model
        from django_tenants.middleware.main import TenantMainMiddleware

        headers = dict(scope.get('headers', []))
        host = headers.get(b'host', b'localhost').decode('utf-8').split(':')[0]

        TenantModel = get_tenant_model()
        DomainModel = __import__('apps.tenants.models', fromlist=['Domain']).Domain

        domain = DomainModel.objects.get(domain=host)
        return domain.tenant
    except Exception:
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """Autentica conexões WebSocket via token JWT na query string."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)
        token_list = params.get('token', [])

        if token_list:
            scope['user'] = await get_user_from_token(token_list[0])
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))


class TenantChannelsMiddleware(BaseMiddleware):
    """Injeta o tenant no scope do WebSocket baseado no host."""

    async def __call__(self, scope, receive, send):
        scope['tenant'] = await get_tenant_from_scope(scope)
        return await super().__call__(scope, receive, send)
