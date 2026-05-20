"""URLs do app usuarios."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessUnitViewSet, UsuarioViewSet

router = DefaultRouter()
router.register('bus', BusinessUnitViewSet, basename='business-unit')
router.register('usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = [
    path('', include(router.urls)),
]
