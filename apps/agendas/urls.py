"""URLs do app agendas."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import AgendaViewSet, BlocoHorarioViewSet

router = DefaultRouter()
router.register('agendas', AgendaViewSet, basename='agenda')

# Blocos aninhados sob agendas: /api/agendas/{agenda_pk}/blocos/
agenda_router = nested_routers.NestedDefaultRouter(router, 'agendas', lookup='agenda')
agenda_router.register('blocos', BlocoHorarioViewSet, basename='agenda-bloco')

# Blocos também acessíveis diretamente: /api/blocos/{id}/
blocos_router = DefaultRouter()
blocos_router.register('blocos', BlocoHorarioViewSet, basename='bloco')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(agenda_router.urls)),
    path('', include(blocos_router.urls)),
]
