"""URLs e views para feriados e afastamentos."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, serializers
from apps.usuarios.permissions import IsAdmin, IsRHOuSuperior
from .models import Feriado, AfastamentoColaborador


class FeriadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feriado
        fields = ['id', 'data', 'nome', 'tipo']


class AfastamentoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)

    class Meta:
        model = AfastamentoColaborador
        fields = ['id', 'usuario', 'usuario_nome', 'tipo', 'data_inicio', 'data_fim', 'observacao', 'aprovado_por', 'created_at']
        read_only_fields = ['id', 'created_at']


class FeriadoViewSet(viewsets.ModelViewSet):
    queryset = Feriado.objects.all()
    serializer_class = FeriadoSerializer
    permission_classes = [IsAdmin]


class AfastamentoViewSet(viewsets.ModelViewSet):
    serializer_class = AfastamentoSerializer
    permission_classes = [IsRHOuSuperior]

    def get_queryset(self):
        qs = AfastamentoColaborador.objects.select_related('usuario', 'aprovado_por')
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        return qs


router = DefaultRouter()
router.register('feriados', FeriadoViewSet, basename='feriado')
router.register('afastamentos', AfastamentoViewSet, basename='afastamento')

urlpatterns = [path('admin/', include(router.urls))]
