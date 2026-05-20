"""App: feriados — Feriado e AfastamentoColaborador."""
import uuid
from django.db import models


class Feriado(models.Model):
    TIPO_CHOICES = [
        ('nacional', 'Nacional'),
        ('estadual', 'Estadual'),
        ('tenant', 'Empresa'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.DateField(unique=True)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    class Meta:
        db_table = 'feriados'
        ordering = ['data']

    def __str__(self):
        return f'{self.nome} ({self.data})'


class AfastamentoColaborador(models.Model):
    TIPO_CHOICES = [
        ('ferias', 'Férias'),
        ('folga', 'Folga'),
        ('licenca', 'Licença'),
        ('outro', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='afastamentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    observacao = models.TextField(blank=True)
    aprovado_por = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='afastamentos_aprovados'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'afastamentos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.usuario.nome} — {self.get_tipo_display()} ({self.data_inicio} a {self.data_fim})'
