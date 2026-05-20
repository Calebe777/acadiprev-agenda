"""Views e URLs do app notificacoes."""
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Notificacao
from .serializers import NotificacaoSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_notificacoes(request):
    """GET /api/notificacoes/ — Notificações do usuário logado."""
    apenas_nao_lidas = request.query_params.get('nao_lidas') == 'true'
    qs = Notificacao.objects.filter(usuario=request.user)
    if apenas_nao_lidas:
        qs = qs.filter(lida=False)
    return Response(NotificacaoSerializer(qs[:50], many=True).data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def marcar_lida(request, pk):
    """PATCH /api/notificacoes/{id}/lida/ — Marca notificação como lida."""
    try:
        n = Notificacao.objects.get(pk=pk, usuario=request.user)
        n.lida = True
        n.save(update_fields=['lida'])
        return Response(NotificacaoSerializer(n).data)
    except Notificacao.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_todas_lidas(request):
    """POST /api/notificacoes/marcar-todas-lidas/ — Marca todas como lidas."""
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return Response({'ok': True})
