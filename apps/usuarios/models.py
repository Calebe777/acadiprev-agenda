"""
App: usuarios — TENANT APP
Models: BusinessUnit, Usuario (custom AbstractBaseUser)
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UsuarioManager


class BusinessUnit(models.Model):
    """
    Unidade de negócio (BU) — agrupa colaboradores por setor.
    Cada BU tem um líder e pertence a um setor específico.
    """
    SETOR_CHOICES = [
        ('comercial', 'Comercial'),
        ('marketing', 'Marketing'),
        ('juridico', 'Jurídico'),
        ('administrativo', 'Administrativo'),
        ('recepcao', 'Recepção'),
        ('outro', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    lider = models.ForeignKey(
        'Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='bu_liderada'
    )
    setor = models.CharField(max_length=30, choices=SETOR_CHOICES)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_units'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_setor_display()})'


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Usuário customizado — identificado por email, com perfil e BU.
    Suporta soft delete via deleted_at.
    """
    PERFIL_CHOICES = [
        ('colaborador', 'Colaborador'),
        ('lider', 'Líder'),
        ('rh', 'RH'),
        ('diretoria', 'Diretoria'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='colaborador')
    bu = models.ForeignKey(
        BusinessUnit, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='membros'
    )
    ativo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuarios'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.email})'

    def soft_delete(self):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.ativo = False
        self.save(update_fields=['deleted_at', 'ativo'])

    @property
    def is_active(self):
        return self.ativo and self.deleted_at is None
