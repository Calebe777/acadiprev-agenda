"""
App: tenants — SHARED APP
Gerencia os tenants (empresas) e domínios no schema público.
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """Representa uma empresa (AcadiPrev, Carvalho) com schema isolado."""
    nome = models.CharField(max_length=100)
    cor_primaria = models.CharField(max_length=7, default='#1B3A6B')
    logo_url = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    # django-tenants: cria schema automaticamente ao salvar
    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        db_table = 'tenants'

    def __str__(self):
        return self.nome


class Domain(DomainMixin):
    """Mapeia domínios/subdomínios para tenants."""

    class Meta:
        db_table = 'domains'

    def __str__(self):
        return self.domain
