"""
ASGI config — Django Channels multi-tenant.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acadiprev.settings.development')

# Inicializa Django antes de importar consumers/routing
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from acadiprev.routing import websocket_urlpatterns
from acadiprev.middleware import JWTAuthMiddlewareStack, TenantChannelsMiddleware

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TenantChannelsMiddleware(
            JWTAuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
