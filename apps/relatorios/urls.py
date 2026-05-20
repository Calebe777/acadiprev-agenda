"""URLs do app relatorios."""
from django.urls import path
from .views import (
    meu_desempenho, frequencia, desempenho_bu, executivo,
    exportar_relatorio, status_exportacao
)

urlpatterns = [
    path('relatorios/meu-desempenho/', meu_desempenho, name='relatorio-desempenho'),
    path('relatorios/frequencia/', frequencia, name='relatorio-frequencia'),
    path('relatorios/bu/', desempenho_bu, name='relatorio-bu'),
    path('relatorios/executivo/', executivo, name='relatorio-executivo'),
    path('relatorios/exportar/', exportar_relatorio, name='relatorio-exportar'),
    path('relatorios/exportar/<str:task_id>/', status_exportacao, name='relatorio-exportar-status'),
]
