"""Views do app setores."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios.permissions import IsColaboradorOuSuperior, IsAdmin
from .models import SetorConfig
from .serializers import SetorConfigSerializer


@api_view(['GET'])
@permission_classes([IsColaboradorOuSuperior])
def minha_bu_config(request):
    """
    GET /api/setor-config/minha-bu/
    Retorna configuração de campos do setor do usuário logado.
    Usado pelo frontend para renderizar formulário dinâmico ao concluir bloco.
    """
    user = request.user
    if not user.bu:
        return Response({'detail': 'Usuário sem BU.'}, status=status.HTTP_404_NOT_FOUND)

    config, created = SetorConfig.objects.get_or_create(
        bu=user.bu,
        defaults=SetorConfig.get_defaults_para_setor(user.bu.setor)
    )
    return Response(SetorConfigSerializer(config).data)


class SetorConfigView(APIView):
    """
    GET/PUT /api/setor-config/{bu_id}/
    Admin pode visualizar e atualizar campos obrigatórios da BU.
    """
    permission_classes = [IsAdmin]

    def get(self, request, bu_id):
        try:
            config = SetorConfig.objects.get(bu_id=bu_id)
        except SetorConfig.DoesNotExist:
            return Response({'detail': 'Config não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SetorConfigSerializer(config).data)

    def put(self, request, bu_id):
        try:
            config = SetorConfig.objects.get(bu_id=bu_id)
        except SetorConfig.DoesNotExist:
            return Response({'detail': 'Config não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SetorConfigSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
