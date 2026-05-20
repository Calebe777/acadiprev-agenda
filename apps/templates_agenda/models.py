"""App: templates_agenda — TemplateAgenda e TemplateBlocos por BU."""
import uuid
from django.db import models


class TemplateAgenda(models.Model):
    """Template de agenda reutilizável por BU — usado pelo Celery para criar agendas diárias."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bu = models.ForeignKey('usuarios.BusinessUnit', on_delete=models.CASCADE, related_name='templates')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    padrao = models.BooleanField(default=False)  # Template padrão da BU
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates_agenda'

    def __str__(self):
        return f'{self.nome} — {self.bu.nome}'

    def save(self, *args, **kwargs):
        # Garante somente um template padrão por BU
        if self.padrao:
            TemplateAgenda.objects.filter(bu=self.bu, padrao=True).exclude(pk=self.pk).update(padrao=False)
        super().save(*args, **kwargs)


class TemplateBlocos(models.Model):
    """Bloco de horário pertencente a um template de agenda."""
    TIPO_CHOICES = [
        ('trabalho', 'Trabalho'), ('intervalo', 'Intervalo'),
        ('reuniao', 'Reunião'), ('treinamento', 'Treinamento'),
        ('checkin', 'Check-in'), ('checkout', 'Check-out'),
        ('acumulativo', 'Acumulativo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(TemplateAgenda, on_delete=models.CASCADE, related_name='blocos')
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField(null=True, blank=True)
    atividade = models.CharField(max_length=200)
    foco_entrega = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='trabalho')
    ordem = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'template_blocos'
        ordering = ['ordem', 'horario_inicio']

    def __str__(self):
        return f'{self.horario_inicio} — {self.atividade}'
