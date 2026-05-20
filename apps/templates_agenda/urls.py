"""Views e URLs para templates de agenda."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, serializers
from apps.usuarios.permissions import IsLiderOuSuperior
from .models import TemplateAgenda, TemplateBlocos


class TemplateBlocosSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateBlocos
        fields = ['id', 'horario_inicio', 'horario_fim', 'atividade', 'foco_entrega', 'tipo', 'ordem']


class TemplateAgendaSerializer(serializers.ModelSerializer):
    blocos = TemplateBlocosSerializer(many=True, read_only=True)
    bu_nome = serializers.CharField(source='bu.nome', read_only=True)

    class Meta:
        model = TemplateAgenda
        fields = ['id', 'bu', 'bu_nome', 'nome', 'descricao', 'ativo', 'padrao', 'blocos', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TemplateAgendaViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateAgendaSerializer
    permission_classes = [IsLiderOuSuperior]

    def get_queryset(self):
        user = self.request.user
        qs = TemplateAgenda.objects.prefetch_related('blocos')
        if user.perfil == 'lider':
            qs = qs.filter(bu=user.bu)
        return qs


router = DefaultRouter()
router.register('templates', TemplateAgendaViewSet, basename='template-agenda')

urlpatterns = [path('admin/', include(router.urls))]
