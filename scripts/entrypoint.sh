#!/usr/bin/env sh
# ============================================================
# scripts/entrypoint.sh — Boot do container api em produção.
# 1. Espera o Postgres responder
# 2. Garante que existam as chaves JWT (RSA)
# 3. Roda collectstatic (idempotente)
# 4. Aplica migrações: shared (django-tenants) + tenants
# 5. Inicia o Daphne (ASGI)
# ============================================================
set -e

echo "[entrypoint] DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"

# ---- 1. Aguarda o Postgres ----
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
echo "[entrypoint] Aguardando Postgres em ${DB_HOST}:${DB_PORT}..."
for i in $(seq 1 60); do
    if nc -z "${DB_HOST}" "${DB_PORT}"; then
        echo "[entrypoint] Postgres respondeu (tentativa ${i})."
        break
    fi
    sleep 1
done

# ---- 2. Chaves JWT ----
KEYS_DIR="${KEYS_DIR:-/app/keys}"
mkdir -p "${KEYS_DIR}"
if [ ! -f "${KEYS_DIR}/private.pem" ]; then
    echo "[entrypoint] Gerando par de chaves RSA em ${KEYS_DIR}..."
    openssl genrsa -out "${KEYS_DIR}/private.pem" 2048 2>/dev/null \
        || python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
with open('${KEYS_DIR}/private.pem','wb') as f:
    f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
open('${KEYS_DIR}/public.pem','wb').write(pub)
"
    if [ ! -f "${KEYS_DIR}/public.pem" ]; then
        openssl rsa -in "${KEYS_DIR}/private.pem" -pubout -out "${KEYS_DIR}/public.pem" 2>/dev/null || true
    fi
    chmod 600 "${KEYS_DIR}/private.pem" || true
fi

# ---- 3. Static ----
echo "[entrypoint] collectstatic..."
python manage.py collectstatic --noinput || true

# ---- 4. Migrações (django-tenants) ----
echo "[entrypoint] migrate_schemas --shared..."
python manage.py migrate_schemas --shared --noinput || python manage.py migrate --noinput

echo "[entrypoint] migrate_schemas (tenants)..."
python manage.py migrate_schemas --noinput || true

# ---- 5. Daphne ----
echo "[entrypoint] Iniciando Daphne em 0.0.0.0:8000"
exec daphne -b 0.0.0.0 -p 8000 acadiprev.asgi:application
