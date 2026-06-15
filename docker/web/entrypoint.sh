#!/usr/bin/env bash
# =============================================================================
#  Entrypoint del contenedor web / celery
#  - Espera a PostgreSQL
#  - (solo web) aplica migraciones y recolecta estáticos
#  - Ejecuta el comando recibido (gunicorn / celery)
# =============================================================================
set -euo pipefail

# --- Esperar a que PostgreSQL acepte conexiones ---
echo "[entrypoint] Esperando a PostgreSQL en ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-blog}" >/dev/null 2>&1; do
    sleep 1
done
echo "[entrypoint] PostgreSQL disponible."

# --- Tareas de arranque solo para el proceso web ---
# RUN_MIGRATIONS=1 se establece en el servicio web del compose.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "[entrypoint] Aplicando migraciones..."
    python manage.py migrate --noinput

    echo "[entrypoint] Ajustando el Site (hostname desde WAGTAIL_BASE_URL)..."
    python manage.py setup_site || true

    echo "[entrypoint] Compilando traducciones (i18n)..."
    python manage.py compilemessages 2>/dev/null || true

    echo "[entrypoint] Recolectando estáticos..."
    python manage.py collectstatic --noinput --clear

    # Bootstrap opcional de superusuario (si las env vars están presentes)
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        echo "[entrypoint] Asegurando superusuario..."
        python manage.py createsuperuser --noinput || true
    fi
fi

echo "[entrypoint] Iniciando: $*"
exec "$@"
