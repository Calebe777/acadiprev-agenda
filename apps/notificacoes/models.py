"""App: notificacoes — Notificação in-app."""
import uuid
from django.db import models


class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('bloco_inicio', 'Início de bloco em breve'),
        ('tarefa_vencida', 'Tarefa com prazo vencido'),
        ('tarefa_atribuida', 'Nova tarefa atribuída'),
        ('justificativa_avaliada', 'Justificativa avaliada'),
        ('alerta_lider', 'Alerta do líder'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.CASCADE, related_name='notificacoes'
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)  # rota frontend
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacoes'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['usuario', 'lida'])]

    def __str__(self):
        return f'{self.titulo} → {self.usuario.nome}'
