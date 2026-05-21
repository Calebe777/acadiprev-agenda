#!/usr/bin/env bash
# ============================================================
# scripts/gen-secrets.sh
# Gera valores seguros para preencher o .env de produção.
# Uso (na VPS, na raiz do projeto):
#   bash scripts/gen-secrets.sh
# ============================================================
set -e

rand() {
    # 50 caracteres alfanuméricos urlsafe
    python3 -c "import secrets;print(secrets.token_urlsafe(38))" 2>/dev/null \
        || openssl rand -base64 48 | tr -d '\n=+/' | cut -c1-50
}

SECRET_KEY=$(rand)
DB_PASSWORD=$(rand)
MINIO_SECRET=$(rand)

cat <<EOF

# ============================================================
# Cole as linhas abaixo no seu .env (substituindo os placeholders)
# ============================================================

SECRET_KEY=${SECRET_KEY}
DB_PASSWORD=${DB_PASSWORD}
AWS_SECRET_ACCESS_KEY=${MINIO_SECRET}

EOF
