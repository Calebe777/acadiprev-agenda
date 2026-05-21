FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Argumentos de build (escolhem dev vs produção sem precisar de outro Dockerfile)
ARG REQUIREMENTS=development
ARG DJANGO_SETTINGS_MODULE=acadiprev.settings.development
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

WORKDIR /app

# System deps (libpq + weasyprint + cairo/pango + utilitários úteis no boot)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/${REQUIREMENTS}.txt

COPY . .

# Torna o entrypoint executável se existir (não falha se não houver)
RUN chmod +x /app/scripts/entrypoint.sh 2>/dev/null || true

# Collect static usando o settings escolhido no build
# (SECRET_KEY dummy para o collectstatic não falhar em build time)
RUN SECRET_KEY=build-time-dummy ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "acadiprev.asgi:application"]
