"""URLs do app justificativas."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JustificativaViewSet

router = DefaultRouter()
router.register('justificativas', JustificativaViewSet, basename='justificativa')

urlpatterns = [
    path('', include(router.urls)),
]
