"""Views do app tenants."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection

from .models import Tenant
from .serializers import TenantConfigSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def tenant_config(request):
    """
    GET /api/tenant/config/
    Retorna nome, cor primária e logo do tenant atual (público — sem autenticação).
    Usado pelo frontend para aplicar o tema antes do login.
    """
    tenant = connection.tenant
    serializer = TenantConfigSerializer(tenant)
    return Response(serializer.data)
