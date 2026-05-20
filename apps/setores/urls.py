"""URLs do app setores."""
from django.urls import path
from .views import minha_bu_config, SetorConfigView

urlpatterns = [
    path('setor-config/minha-bu/', minha_bu_config, name='setor-config-minha-bu'),
    path('setor-config/<uuid:bu_id>/', SetorConfigView.as_view(), name='setor-config-detail'),
]
