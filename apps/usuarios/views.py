"""Views do app usuarios — CRUD de BUs e Usuários via /api/admin/."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.permissions import IsAdmin, IsLiderOuSuperior
from .models import BusinessUnit, Usuario
from .serializers import (
    BusinessUnitSerializer, UsuarioSerializer, UsuarioCreateSerializer
)


class BusinessUnitViewSet(viewsets.ModelViewSet):
    """
    GET/POST /api/admin/bus/
    GET/PUT/DELETE /api/admin/bus/{id}/
    Permissão: Admin
    """
    queryset = BusinessUnit.objects.select_related('lider').all()
    serializer_class = BusinessUnitSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')
        return qs

    @action(detail=True, methods=['get'])
    def membros(self, request, pk=None):
        """GET /api/admin/bus/{id}/membros/ — lista colaboradores da BU."""
        bu = self.get_object()
        users = bu.membros.filter(ativo=True).order_by('nome')
        serializer = UsuarioSerializer(users, many=True)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    GET/POST /api/admin/usuarios/
    GET/PUT/PATCH/DELETE /api/admin/usuarios/{id}/
    Permissão: Admin
    """
    queryset = Usuario.objects.select_related('bu').all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        return UsuarioSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        perfil = self.request.query_params.get('perfil')
        bu = self.request.query_params.get('bu')
        if perfil:
            qs = qs.filter(perfil=perfil)
        if bu:
            qs = qs.filter(bu_id=bu)
        return qs

    def destroy(self, request, *args, **kwargs):
        """Soft delete — não remove do banco."""
        usuario = self.get_object()
        usuario.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """GET /api/admin/usuarios/me/ — dados do usuário logado."""
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
