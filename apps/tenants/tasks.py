"""Task Celery para limpar tokens JWT expirados."""
from celery import shared_task
from django_tenants.utils import schema_context


@shared_task(name='apps.tenants.tasks.limpar_tokens_expirados')
def limpar_tokens_expirados(schema_name: str):
    """Remove refresh tokens vencidos da blacklist — executado às 03h00."""
    with schema_context(schema_name):
        from django.utils import timezone
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

        # Remove tokens vencidos
        expired = OutstandingToken.objects.filter(expires_at__lt=timezone.now())
        BlacklistedToken.objects.filter(token__in=expired).delete()
        count = expired.delete()[0]

        return {'schema': schema_name, 'tokens_removidos': count}
