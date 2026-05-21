# Deploy na VPS (Ubuntu 22.04 / 24.04) — Agenda Hora a Hora

Este guia coloca o app rodando em produção em uma VPS Ubuntu, em HTTP, numa
porta configurável (default `8090` — você pode trocar pra qualquer porta livre).

> Tudo é rodado dentro de Docker — não precisa instalar Python, Node ou
> Postgres na VPS. O único pré-requisito é Docker + Docker Compose.

---

## 0. O que você vai usar

Arquivos novos criados especificamente pra produção:

| Arquivo                              | Função                                          |
|--------------------------------------|-------------------------------------------------|
| `docker-compose.prod.yml`            | Stack completa (db, redis, minio, api, celery, nginx) |
| `nginx/Dockerfile.prod`              | Build do frontend + nginx                       |
| `nginx/nginx.prod.conf`              | Config do nginx (SPA + proxy `/api` e `/ws`)    |
| `scripts/entrypoint.sh`              | Boot do container `api` (migra, gera chaves JWT)|
| `scripts/gen-secrets.sh`             | Gera SECRET_KEY/senhas fortes                   |
| `.env.production.example`            | Template do `.env`                              |

O `production.py` foi ajustado pra HTTPS ser configurável (`USE_HTTPS=False`
no `.env` desativa redirects/cookies seguros — necessário para acesso HTTP
por IP).

---

## 1. Instalar Docker na VPS (uma única vez)

Conecte na VPS por SSH e rode:

```bash
# Atualiza
sudo apt update && sudo apt -y upgrade

# Instala Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Reentre na sessão para ganhar permissão no grupo docker
exit
```

Reconecte e teste:

```bash
docker version
docker compose version
```

---

## 2. Enviar o código para a VPS

Escolha **uma** das opções:

**Opção A — Git (recomendado se o repo já está no GitHub/GitLab):**

```bash
cd ~
git clone <URL_DO_SEU_REPO> acadiprev-agenda
cd acadiprev-agenda
```

**Opção B — rsync do seu computador:**

```bash
# No SEU computador (não na VPS), dentro da pasta do projeto:
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '__pycache__' \
      --exclude '.git' --exclude 'frontend/dist' \
      ./ usuario@SEU_IP_DA_VPS:~/acadiprev-agenda/
```

Depois entre na VPS:

```bash
ssh usuario@SEU_IP_DA_VPS
cd ~/acadiprev-agenda
```

---

## 3. Gerar segredos e criar o `.env`

```bash
cp .env.production.example .env
bash scripts/gen-secrets.sh
```

O `gen-secrets.sh` imprime três linhas (`SECRET_KEY`, `DB_PASSWORD`,
`AWS_SECRET_ACCESS_KEY`). Copie-as e cole no `.env`, substituindo os
placeholders.

Edite o `.env` (com `nano .env`) e ajuste:

- `HTTP_PORT=8090` (ou outra porta livre — confira com `ss -tlnp`)
- `ALLOWED_HOSTS=SEU_IP_DA_VPS,localhost,127.0.0.1`
- `CSRF_TRUSTED_ORIGINS=http://SEU_IP_DA_VPS:8090`
- `CORS_ALLOWED_ORIGINS=http://SEU_IP_DA_VPS:8090`

Se for usar e-mail (recuperação de senha, etc.), preencha os campos `EMAIL_*`.

---

## 4. Liberar a porta no firewall

```bash
# UFW (padrão Ubuntu)
sudo ufw allow 8090/tcp     # use a mesma porta de HTTP_PORT
sudo ufw status
```

Se a VPS é AWS/GCP/Oracle/Hetzner, libere também no **Security Group / Firewall
do painel**, não só no UFW.

---

## 5. Subir tudo

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

O primeiro build demora alguns minutos (instala Python deps, builda o
frontend Vite, baixa imagens base). Os próximos boots são instantâneos.

Acompanhe os logs até estabilizar:

```bash
docker compose -f docker-compose.prod.yml logs -f api nginx
```

Você deve ver:
- `[entrypoint] Postgres respondeu...`
- `[entrypoint] migrate_schemas --shared...`
- `Starting server at tcp:port=8000:interface=0.0.0.0` (Daphne)
- nginx pronto.

`Ctrl+C` pra sair dos logs (não derruba os containers).

---

## 6. Criar tenant inicial + superuser

O app é multi-tenant (django-tenants). Você precisa criar pelo menos o tenant
público antes de logar.

```bash
# Cria o schema "public" (tenant raiz) se ainda não existir
docker compose -f docker-compose.prod.yml exec api \
    python manage.py shell -c "
from apps.tenants.models import Tenant, Domain
t, _ = Tenant.objects.get_or_create(schema_name='public', defaults={'name':'Public'})
Domain.objects.get_or_create(domain='localhost', tenant=t, defaults={'is_primary':True})
print('OK')
"

# Cria o superuser
docker compose -f docker-compose.prod.yml exec api \
    python manage.py createsuperuser
```

> Observação: dependendo de como o `apps/tenants/models.py` foi modelado, os
> campos exatos podem ser diferentes. Se o `get_or_create` reclamar de algum
> campo obrigatório (ex.: `paid_until`, `on_trial`), abra
> `apps/tenants/models.py` e ajuste os defaults acima conforme o modelo.

---

## 7. Acessar o app

Abra no navegador:

- App: `http://SEU_IP_DA_VPS:8090/`
- Admin: `http://SEU_IP_DA_VPS:8090/admin/`
- API: `http://SEU_IP_DA_VPS:8090/api/`

---

## 8. Operação do dia a dia

```bash
# Ver status
docker compose -f docker-compose.prod.yml ps

# Logs (tudo)
docker compose -f docker-compose.prod.yml logs -f --tail=100

# Reiniciar só a API depois de mudar código
docker compose -f docker-compose.prod.yml up -d --build api celery_worker celery_beat

# Aplicar migrações manualmente
docker compose -f docker-compose.prod.yml exec api python manage.py migrate_schemas --shared
docker compose -f docker-compose.prod.yml exec api python manage.py migrate_schemas

# Shell Django
docker compose -f docker-compose.prod.yml exec api python manage.py shell

# Derrubar (mantém volumes/dados)
docker compose -f docker-compose.prod.yml down

# Derrubar + APAGAR dados (cuidado!)
docker compose -f docker-compose.prod.yml down -v
```

---

## 9. Backup do Postgres

```bash
# Backup
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dumpall -U "$(grep ^DB_USER .env | cut -d= -f2)" \
    > backup_$(date +%F).sql

# Restaurar
cat backup_2026-05-21.sql | docker compose -f docker-compose.prod.yml exec -T db \
    psql -U "$(grep ^DB_USER .env | cut -d= -f2)"
```

Coloque isso num cron diário (`crontab -e`) e mande o `.sql` pra um S3/storage
fora da VPS.

---

## 10. Quando tiver domínio + HTTPS

Quando quiser ligar HTTPS de verdade:

1. Aponte o DNS A do domínio para o IP da VPS.
2. Coloque um Caddy/Traefik/nginx na frente (porta 443) com Let's Encrypt
   fazendo proxy pra `http://127.0.0.1:8090`.
3. No `.env`, mude:
   - `USE_HTTPS=True`
   - `ALLOWED_HOSTS=seudominio.com,SEU_IP_DA_VPS`
   - `CSRF_TRUSTED_ORIGINS=https://seudominio.com`
   - `CORS_ALLOWED_ORIGINS=https://seudominio.com`
4. `docker compose -f docker-compose.prod.yml restart api`

---

## Troubleshooting rápido

| Sintoma                                          | O que checar                                                                    |
|--------------------------------------------------|---------------------------------------------------------------------------------|
| `DisallowedHost` ao abrir o IP                   | Adicione o IP em `ALLOWED_HOSTS` e `docker compose restart api`                 |
| Admin loga e cai pra tela em branco              | Falta o tenant `public` (passo 6) ou `CSRF_TRUSTED_ORIGINS` errado              |
| 502/504 no nginx                                 | `docker compose logs api` — provavelmente erro de migração ou env faltando      |
| `connection refused` ao Postgres                 | Espere 10s e tente — healthcheck do db demora no primeiro boot                  |
| Frontend pede `/api` errado                      | Confira `VITE_API_BASE_URL` no build do frontend (variável usada pelo Vite)     |
| Porta `8090` ocupada                             | Mude `HTTP_PORT` no `.env` e libere a nova porta no UFW                         |
