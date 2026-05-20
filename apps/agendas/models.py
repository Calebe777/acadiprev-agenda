"""
App: agendas — TENANT APP
Models: Agenda, BlocoHorario, RegistroAtividade
"""
import uuid
from django.db import models
from django.utils import timezone


class Agenda(models.Model):
    """
    Agenda diária do colaborador — única por usuário/data (unique_together).
    Ciclo: rascunho → ativo (check-in) → encerrado (check-out) → aprovado (líder)
    """
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('ativo', 'Ativo'),
        ('encerrado', 'Encerrado'),
        ('aprovado', 'Aprovado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='agendas')
    data = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    meta_dia = models.TextField(blank=True)
    check_in_at = models.DateTimeField(null=True, blank=True)
    check_out_at = models.DateTimeField(null=True, blank=True)
    resumo_final = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agendas'
        unique_together = [('usuario', 'data')]
        indexes = [
            models.Index(fields=['usuario', 'data']),
            models.Index(fields=['data']),
            models.Index(fields=['status']),
        ]
        ordering = ['-data']

    def __str__(self):
        return f'Agenda {self.usuario.nome} — {self.data}'

    @property
    def is_somente_leitura(self):
        """Após checkout, colaborador não pode editar."""
        return self.status in ('encerrado', 'aprovado')


class BlocoHorario(models.Model):
    """
    Unidade mínima da agenda — atividade planejada em um horário.
    Tipo 'acumulativo' é exclusivo para Recepção (modo de atendimentos).
    """
    TIPO_CHOICES = [
        ('trabalho', 'Trabalho'),
        ('intervalo', 'Intervalo'),
        ('reuniao', 'Reunião'),
        ('treinamento', 'Treinamento'),
        ('checkin', 'Check-in'),
        ('checkout', 'Check-out'),
        ('acumulativo', 'Acumulativo'),  # Recepção
    ]
    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('integral', 'Integral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE, related_name='blocos')
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField(null=True, blank=True)
    atividade = models.CharField(max_length=200)
    foco_entrega = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='trabalho')
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, blank=True)
    ordem = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blocos_horario'
        ordering = ['ordem', 'horario_inicio']

    def __str__(self):
        return f'{self.horario_inicio} — {self.atividade}'

    @property
    def duracao_minutos(self):
        if self.horario_fim:
            from datetime import datetime, date
            inicio = datetime.combine(date.today(), self.horario_inicio)
            fim = datetime.combine(date.today(), self.horario_fim)
            return int((fim - inicio).total_seconds() / 60)
        return None


class RegistroAtividade(models.Model):
    """
    Registro de execução de um bloco — preenchido pelo colaborador ao concluir.
    Campos variam por setor (SetorConfig). Dados específicos em campos_setor (JSONB).
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em andamento'),
        ('concluido', 'Concluído'),
        ('parcial', 'Parcial'),
        ('nao_realizado', 'Não realizado'),
        ('desviado', 'Desviado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bloco = models.OneToOneField(BlocoHorario, on_delete=models.CASCADE, related_name='registro')
    iniciado_em = models.DateTimeField(null=True, blank=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    # Campos base (todos os setores)
    tipo_atividade = models.CharField(max_length=50, blank=True)
    descricao = models.TextField(blank=True)       # obrigatório ao concluir
    motivo_parcial = models.TextField(blank=True)  # obrigatório se parcial/não realizado
    percentual_meta = models.SmallIntegerField(null=True, blank=True)

    # Campos extras por setor (JSONB genérico)
    campos_setor = models.JSONField(default=dict, blank=True)

    # Evidência (obrigatória para Marketing e Administrativo)
    evidencia_url = models.URLField(blank=True)
    evidencia_arquivo = models.CharField(max_length=500, blank=True)  # path no S3

    # Privacidade — dados jurídicos restritos
    confidencial = models.BooleanField(default=False)

    # Modo acumulativo — Recepção
    qtd_atendimentos = models.SmallIntegerField(null=True, blank=True)
    ocorrencias = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'registros_atividade'

    def __str__(self):
        return f'Registro {self.bloco} — {self.status}'
