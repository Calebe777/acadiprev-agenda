"""
App: tarefas — TENANT APP
Model: Tarefa (Backlog + Kanban)
"""
import uuid
from django.db import models


class Tarefa(models.Model):
    """
    Tarefa do backlog pessoal — pode existir livremente ou vinculada a um bloco da agenda.
    Suporta Kanban com 3 colunas: a_fazer, em_andamento, concluido.
    Soft delete via deleted_at.
    """
    STATUS_CHOICES = [
        ('a_fazer', 'A fazer'),
        ('em_andamento', 'Em andamento'),
        ('concluido', 'Concluído'),
    ]
    PRIORIDADE_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Média'),
        ('baixa', 'Baixa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='a_fazer')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')

    # Dono e atribuição
    criado_por = models.ForeignKey(
        'usuarios.Usuario', on_delete=models.CASCADE, related_name='tarefas_criadas'
    )
    atribuido_a = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tarefas_atribuidas'
    )
    bu = models.ForeignKey(
        'usuarios.BusinessUnit', null=True, blank=True, on_delete=models.SET_NULL
    )

    # Prazo
    prazo = models.DateField(null=True, blank=True)

    # Vínculo com bloco da agenda (opcional)
    bloco = models.ForeignKey(
        'agendas.BlocoHorario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tarefas'
    )

    # Posição na coluna Kanban
    ordem_kanban = models.SmallIntegerField(default=0)

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    concluido_em = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete

    class Meta:
        db_table = 'tarefas'
        ordering = ['ordem_kanban', '-created_at']
        indexes = [
            models.Index(fields=['atribuido_a', 'status']),
            models.Index(fields=['bu', 'status']),
            models.Index(fields=['prazo']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return self.titulo

    @property
    def prazo_vencido(self):
        if self.prazo and self.status in ('a_fazer', 'em_andamento'):
            from django.utils import timezone
            return self.prazo < timezone.localdate()
        return False
