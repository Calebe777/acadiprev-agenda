"""App: justificativas — Fluxo de aprovação por bloco."""
import uuid
from django.db import models


class Justificativa(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bloco = models.ForeignKey(
        'agendas.BlocoHorario', on_delete=models.CASCADE, related_name='justificativas'
    )
    colaborador = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.CASCADE, related_name='justificativas'
    )
    texto = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    # Resposta do líder
    aprovado_por = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='justificativas_avaliadas'
    )
    comentario_lider = models.TextField(blank=True)
    avaliado_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'justificativas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Justificativa {self.colaborador.nome} — {self.status}'
