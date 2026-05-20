"""
Testes de isolamento multi-tenant.
Verifica que dados de um schema não são acessíveis pelo outro.
"""
import pytest
from django_tenants.utils import schema_context


@pytest.mark.django_db
def test_usuario_isolado_por_schema(tenant_acadiprev, tenant_carvalho):
    """Usuário criado no schema AcadiPrev não aparece no schema Carvalho."""
    from apps.usuarios.models import Usuario

    with schema_context(tenant_acadiprev.schema_name):
        Usuario.objects.create_user(
            email='exclusivo@acadiprev.test',
            nome='Usuário Exclusivo',
            password='senha123',
        )
        assert Usuario.objects.filter(email='exclusivo@acadiprev.test').exists()

    with schema_context(tenant_carvalho.schema_name):
        # Não deve existir no schema Carvalho
        assert not Usuario.objects.filter(email='exclusivo@acadiprev.test').exists()


@pytest.mark.django_db
def test_agenda_isolada_por_schema(tenant_acadiprev, tenant_carvalho, colaborador):
    """Agendas do schema AcadiPrev não aparecem no schema Carvalho."""
    from apps.agendas.models import Agenda
    from django.utils import timezone

    with schema_context(tenant_acadiprev.schema_name):
        Agenda.objects.create(
            usuario=colaborador,
            data=timezone.localdate(),
        )
        assert Agenda.objects.filter(usuario=colaborador).count() == 1

    with schema_context(tenant_carvalho.schema_name):
        # Schema Carvalho deve ter 0 agendas
        assert Agenda.objects.all().count() == 0


@pytest.mark.django_db
def test_tarefa_isolada_por_schema(tenant_acadiprev, tenant_carvalho, colaborador):
    """Tarefas do schema AcadiPrev não aparecem no schema Carvalho."""
    from apps.tarefas.models import Tarefa

    with schema_context(tenant_acadiprev.schema_name):
        Tarefa.objects.create(
            titulo='Tarefa exclusiva AcadiPrev',
            criado_por=colaborador,
            atribuido_a=colaborador,
        )

    with schema_context(tenant_carvalho.schema_name):
        assert Tarefa.objects.filter(titulo='Tarefa exclusiva AcadiPrev').count() == 0
