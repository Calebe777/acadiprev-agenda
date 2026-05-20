"""
Permissões customizadas por perfil de usuário.
Usadas como permission_classes nos ViewSets.
"""
from rest_framework.permissions import BasePermission


class IsColaboradorOuSuperior(BasePermission):
    """Qualquer perfil autenticado e ativo."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.ativo
            and request.user.perfil in ('colaborador', 'lider', 'rh', 'diretoria', 'admin')
        )


class IsLiderOuSuperior(BasePermission):
    """Líder, RH, Diretoria ou Admin."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.ativo
            and request.user.perfil in ('lider', 'rh', 'diretoria', 'admin')
        )


class IsRHOuSuperior(BasePermission):
    """RH, Diretoria ou Admin."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.ativo
            and request.user.perfil in ('rh', 'diretoria', 'admin')
        )


class IsDiretoriaOuAdmin(BasePermission):
    """Diretoria ou Admin."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.ativo
            and request.user.perfil in ('diretoria', 'admin')
        )


class IsAdmin(BasePermission):
    """Apenas Admin do tenant."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.ativo
            and request.user.perfil == 'admin'
        )


class IsLiderDaBU(BasePermission):
    """
    Líder pode acessar apenas dados da própria BU.
    Admin pode acessar qualquer BU.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.perfil == 'admin':
            return True
        if request.user.perfil == 'lider':
            # obj pode ser Agenda, Tarefa, etc. — todos têm usuario.bu
            target_bu = getattr(obj, 'bu', None) or getattr(getattr(obj, 'usuario', None), 'bu', None)
            return target_bu == request.user.bu
        return False
