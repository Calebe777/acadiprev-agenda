"""App: setores — SetorConfig por BU (campos dinâmicos)."""
import uuid
from django.db import models


class SetorConfig(models.Model):
    """
    Configuração de campos obrigatórios ao concluir um bloco, por BU.
    O frontend faz GET /api/setor-config/minha-bu/ para renderizar o formulário dinamicamente.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bu = models.OneToOneField(
        'usuarios.BusinessUnit', on_delete=models.CASCADE, related_name='setor_config'
    )
    # Opções do select "tipo_atividade" (array JSON)
    tipos_atividade = models.JSONField(default=list)

    # Flags por setor
    requer_cliente = models.BooleanField(default=False)           # Comercial
    requer_resultado = models.BooleanField(default=False)         # Comercial
    requer_campanha = models.BooleanField(default=False)          # Marketing
    requer_evidencia = models.BooleanField(default=False)         # Marketing, Administrativo
    requer_num_processo = models.BooleanField(default=False)      # Jurídico
    requer_obs_confidencial = models.BooleanField(default=False)  # Jurídico
    requer_referencia_doc = models.BooleanField(default=False)    # Administrativo
    modo_acumulativo = models.BooleanField(default=False)         # Recepção
    requer_qtd_atendimentos = models.BooleanField(default=False)  # Recepção
    visibilidade_restrita = models.BooleanField(default=False)    # Jurídico

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'setor_config'

    def __str__(self):
        return f'Config — {self.bu.nome}'

    @classmethod
    def get_defaults_para_setor(cls, setor: str) -> dict:
        """Retorna configuração padrão baseada no setor da BU."""
        defaults = {
            'comercial': {
                'tipos_atividade': ['Ligação', 'Visita', 'Reunião', 'Proposta', 'Follow-up'],
                'requer_cliente': True, 'requer_resultado': True,
            },
            'marketing': {
                'tipos_atividade': ['Arte', 'Texto', 'Post', 'Vídeo', 'Campanha'],
                'requer_campanha': True, 'requer_evidencia': True,
            },
            'juridico': {
                'tipos_atividade': ['Petição', 'Audiência', 'Reunião', 'Parecer'],
                'requer_num_processo': True, 'requer_obs_confidencial': True,
                'visibilidade_restrita': True,
            },
            'administrativo': {
                'tipos_atividade': ['Documento', 'Protocolo', 'Pagamento', 'Relatório'],
                'requer_referencia_doc': True, 'requer_evidencia': True,
            },
            'recepcao': {
                'tipos_atividade': [],
                'modo_acumulativo': True, 'requer_qtd_atendimentos': True,
            },
        }
        return defaults.get(setor, {'tipos_atividade': []})
