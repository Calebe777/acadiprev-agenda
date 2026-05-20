"""
Conftest para testes multi-tenant.
Cria schemas de teste para AcadiPrev e Carvalho.
"""
import pytest
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.usuarios.models import BusinessUnit, Usuario


@pytest.fixture(scope='session')
def django_db_setup():
    """Setup do banco de dados para testes multi-tenant."""
    pass


@pytest.fixture
def tenant_acadiprev(db):
    """Fixture: tenant AcadiPrev com schema isolado."""
    tenant, _ = Tenant.objects.get_or_create(
        schema_name='test_acadiprev',
        defaults={'nome': 'AcadiPrev Teste', 'cor_primaria': '#1B3A6B'}
    )
    Domain.objects.get_or_create(domain='acadiprev.test', defaults={'tenant': tenant, 'is_primary': True})
    return tenant


@pytest.fixture
def tenant_carvalho(db):
    """Fixture: tenant Carvalho com schema isolado."""
    tenant, _ = Tenant.objects.get_or_create(
        schema_name='test_carvalho',
        defaults={'nome': 'Carvalho Teste', 'cor_primaria': '#7C3D1A'}
    )
    Domain.objects.get_or_create(domain='carvalho.test', defaults={'tenant': tenant, 'is_primary': True})
    return tenant


@pytest.fixture
def bu_comercial(tenant_acadiprev):
    """Fixture: BU Comercial no schema AcadiPrev."""
    with schema_context(tenant_acadiprev.schema_name):
        bu, _ = BusinessUnit.objects.get_or_create(
            codigo='COM-001',
            defaults={'nome': 'Comercial', 'setor': 'comercial'}
        )
        return bu


@pytest.fixture
def colaborador(bu_comercial, tenant_acadiprev):
    """Fixture: colaborador no schema AcadiPrev."""
    with schema_context(tenant_acadiprev.schema_name):
        user = Usuario.objects.create_user(
            email='colaborador@acadiprev.test',
            nome='Grasi Nunes',
            password='senha123',
            perfil='colaborador',
            bu=bu_comercial,
        )
        return user


@pytest.fixture
def lider(bu_comercial, tenant_acadiprev):
    """Fixture: líder no schema AcadiPrev."""
    with schema_context(tenant_acadiprev.schema_name):
        user = Usuario.objects.create_user(
            email='lider@acadiprev.test',
            nome='João Líder',
            password='senha123',
            perfil='lider',
            bu=bu_comercial,
        )
        return user
