# =============================================================================
#  Imagen de la aplicación (Django + Wagtail)
#  Multi-stage:
#    1) tailwind  -> compila el CSS con Node
#    2) builder   -> compila wheels de Python
#    3) runtime   -> imagen final slim, sin toolchains, usuario no-root
# =============================================================================

# --- Stage 1: compilar Tailwind CSS -----------------------------------------
FROM node:22-slim AS tailwind
WORKDIR /tw
COPY tailwind/package.json ./
RUN npm install
COPY tailwind/ ./
COPY src/templates/ /src/templates/
COPY src/apps/ /src/apps/
RUN npm run build

# --- Stage 2: compilar dependencias de Python -------------------------------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /wheels
COPY requirements/ requirements/
ARG REQ_FILE=requirements/production.txt
RUN pip wheel --wheel-dir /wheels -r ${REQ_FILE}

# --- Stage 3: imagen final --------------------------------------------------
FROM python:3.12-slim AS runtime

# Variables de entorno de Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# Dependencias de runtime:
#  - libpq5: psycopg
#  - postgresql-client: pg_isready
#  - gettext: compilación de traducciones (compilemessages)
RUN apt-get update && apt-get install --no-install-recommends -y \
        libpq5 \
        postgresql-client \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Usuario no-root
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

# Instalar dependencias desde los wheels precompilados
COPY --from=builder /wheels /wheels
COPY requirements/ /tmp/requirements/
ARG REQ_FILE=requirements/production.txt
RUN pip install --no-index --find-links=/wheels -r /tmp/${REQ_FILE} \
    && rm -rf /wheels /tmp/requirements

WORKDIR /app

# Código de la aplicación
COPY --chown=appuser:appuser src/ /app/

# CSS compilado desde el stage de Tailwind
COPY --from=tailwind --chown=appuser:appuser /src/static/css/app.css /app/static/css/app.css

# Entrypoint
COPY --chown=appuser:appuser docker/web/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Directorios escribibles por appuser (collectstatic / media local).
# /app lo crea WORKDIR como root, por eso hay que dar propiedad a appuser:
# sin esto, collectstatic falla con PermissionError en producción.
RUN mkdir -p /app/staticfiles /app/mediafiles \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
