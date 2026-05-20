"""URLs do tenant config."""
from django.urls import path
from .views import tenant_config

urlpatterns = [
    path('config/', tenant_config, name='tenant-config'),
]
