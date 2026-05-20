"""
Task Celery para geração assíncrona de relatórios.
Usa WeasyPrint para PDF e openpyxl para Excel.
Faz upload do arquivo no S3/MinIO e retorna presigned URL de 1h.
"""
import uuid
import io
from celery import shared_task
from django_tenants.utils import schema_context
from django.conf import settings


@shared_task(name='apps.relatorios.tasks.gerar_relatorio_exportacao', bind=True)
def gerar_relatorio_exportacao(self, schema_name: str, tipo: str, formato: str, params: dict):
    """
    Gera PDF ou Excel do relatório especificado e faz upload no S3.
    Retorna presigned URL com validade de 1h.
    """
    with schema_context(schema_name):
        dados = _query_relatorio(tipo, params, schema_name)

        if formato == 'pdf':
            conteudo = _gerar_pdf(dados, tipo)
            ext = 'pdf'
            content_type = 'application/pdf'
        else:
            conteudo = _gerar_excel(dados, tipo)
            ext = 'xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        path = f'{schema_name}/relatorios/{tipo}_{uuid.uuid4()}.{ext}'

        import boto3
        s3 = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=path,
            Body=conteudo,
            ContentType=content_type,
        )

        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': path},
            ExpiresIn=settings.AWS_PRESIGNED_URL_EXPIRY,
        )

        return url


def _query_relatorio(tipo: str, params: dict, schema_name: str) -> dict:
    """Executa a query de dados conforme o tipo de relatório."""
    from apps.agendas.models import Agenda
    from apps.usuarios.models import Usuario
    from django.utils import timezone

    data_inicio = params.get('periodo_inicio') or str(timezone.localdate().replace(day=1))
    data_fim = params.get('periodo_fim') or str(timezone.localdate())
    bu_id = params.get('bu_id')

    if tipo == 'frequencia':
        usuarios = Usuario.objects.filter(ativo=True, perfil='colaborador')
        if bu_id:
            usuarios = usuarios.filter(bu_id=bu_id)
        rows = []
        for u in usuarios:
            agendas = Agenda.objects.filter(usuario=u, data__range=(data_inicio, data_fim))
            rows.append({
                'nome': u.nome, 'email': u.email,
                'dias': agendas.filter(check_in_at__isnull=False).count(),
                'total': agendas.count(),
            })
        return {'tipo': tipo, 'periodo': {'inicio': data_inicio, 'fim': data_fim}, 'linhas': rows}

    return {'tipo': tipo, 'periodo': {'inicio': data_inicio, 'fim': data_fim}, 'linhas': []}


def _gerar_pdf(dados: dict, tipo: str) -> bytes:
    """Gera PDF usando WeasyPrint a partir de HTML."""
    try:
        from weasyprint import HTML
        html = _render_html(dados, tipo)
        return HTML(string=html).write_pdf()
    except ImportError:
        # Fallback simples se WeasyPrint não estiver disponível
        return f"Relatório {tipo}\n{dados}".encode()


def _gerar_excel(dados: dict, tipo: str) -> bytes:
    """Gera Excel usando openpyxl."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = tipo.capitalize()

    linhas = dados.get('linhas', [])
    if linhas:
        # Cabeçalho
        headers = list(linhas[0].keys())
        ws.append(headers)
        for linha in linhas:
            ws.append([linha.get(h, '') for h in headers])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _render_html(dados: dict, tipo: str) -> str:
    """Gera HTML simples para WeasyPrint."""
    linhas_html = ''
    for linha in dados.get('linhas', []):
        cells = ''.join(f'<td style="padding:8px;border:1px solid #ddd">{v}</td>' for v in linha.values())
        linhas_html += f'<tr>{cells}</tr>'

    headers = ''
    if dados.get('linhas'):
        headers = ''.join(
            f'<th style="padding:8px;background:#1B3A6B;color:white">{k}</th>'
            for k in dados['linhas'][0].keys()
        )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #1B3A6B; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Relatório: {tipo.capitalize()}</h1>
        <p>Período: {dados['periodo']['inicio']} a {dados['periodo']['fim']}</p>
        <table>
            <thead><tr>{headers}</tr></thead>
            <tbody>{linhas_html}</tbody>
        </table>
    </body>
    </html>
    """
