"""Custom exception handler para retornar erros padronizados."""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'erro': True,
            'status_code': response.status_code,
            'detalhe': response.data,
        }

    return response
