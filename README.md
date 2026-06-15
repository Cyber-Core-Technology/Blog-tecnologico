# Blog Tecnológico

CMS propio para publicar contenido de tecnología (programación, ciberseguridad,
DevOps). Construido sobre **Django 5.2 + Wagtail 7.4**, contenedorizado con Docker,
con foco en **seguridad**, **rendimiento** y **estética**.

> Reemplazo a medida de WordPress/Blogger: sin tracking de terceros, control total
> del contenido y del stack.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| CMS / Framework | Wagtail 7.4 sobre Django 5.2 (Python 3.12) |
| Base de datos | PostgreSQL 16 |
| Cache / sesiones / broker | Redis 7 |
| Tareas async | Celery (worker + beat) |
| App server | Gunicorn |
| Estáticos | WhiteNoise (comprimidos, con manifest) |
| Media | AWS S3 (django-storages + boto3) |
| Frontend | Templates + Tailwind CSS v4 + HTMX + Alpine.js |
| Resaltado de código | Pygments (server-side, sin JS) |
| Búsqueda | PostgreSQL Full-Text Search (Wagtail) |
| 2FA admin | wagtail-2fa (TOTP) |
| Anti-fuerza bruta | django-axes |
| CSP / headers | django-csp + cabeceras de seguridad de Django |

---

## Arquitectura

```
Nginx Proxy Manager (red: proxy-network)
        │  proxy + SSL
        ▼
      web  ──────────────►  Gunicorn / Django / Wagtail
        │                         (sin puertos publicados)
        │  red privada: blog_internal
        ├── postgres   (aislado, solo blog_internal)
        ├── redis      (aislado, solo blog_internal)
        ├── celery_worker
        └── celery_beat
```

- **Nginx Proxy Manager** (externo) termina TLS y enruta a `web:8000` por la red
  `proxy-network`. Este proyecto **no expone puertos al host** en producción.
- `postgres` y `redis` viven **solo** en `blog_internal`: ni NPM ni el host pueden
  alcanzarlos.

---

## Puesta en marcha

### 1. Requisitos
- Docker + Docker Compose v2
- La red externa `proxy-network` debe existir (la crea Nginx Proxy Manager). Si no:
  ```bash
  docker network create proxy-network
  ```

### 2. Configuración
```bash
cp .env.example .env
# Edita .env: genera DJANGO_SECRET_KEY, pon credenciales de Postgres/Redis,
# claves de AWS S3 y SMTP, y tu dominio en DJANGO_ALLOWED_HOSTS.
```
Genera la clave secreta:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Producción (VPS + Nginx Proxy Manager) — dominio `blog.cyco.tech`

En el `.env` de producción, lo esencial:
```ini
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=...            # python -c "import secrets; print(secrets.token_urlsafe(64))"
DJANGO_ALLOWED_HOSTS=blog.cyco.tech
DJANGO_CSRF_TRUSTED_ORIGINS=https://blog.cyco.tech
WAGTAIL_BASE_URL=https://blog.cyco.tech
DJANGO_SECURE_HSTS_SECONDS=0     # súbelo a 31536000 cuando el HTTPS sea estable
# + Postgres/Redis/AWS S3/SMTP/DEEPL_API_KEY
```

Despliega (usa **solo** el compose de producción; ignora el override de dev):
```bash
docker compose -f docker-compose.yml up -d --build
docker compose -f docker-compose.yml exec web python manage.py createsuperuser
```
El arranque aplica migraciones, fija el hostname del Site (`setup_site` desde
`WAGTAIL_BASE_URL`), compila traducciones y recolecta estáticos automáticamente.

**Nginx Proxy Manager** (en la misma red `proxy-network`): crea un *Proxy Host*:
- Domain Names: `blog.cyco.tech`
- Scheme: `http` · Forward Hostname: `blog_web` · Forward Port: `8000`
- ✅ Block Common Exploits · ✅ Websockets Support
- Pestaña **SSL**: pide un certificado Let's Encrypt y activa **Force SSL** + **HTTP/2**.

> NPM ya envía `X-Forwarded-Proto`, así que Django detecta HTTPS correctamente
> (`SECURE_PROXY_SSL_HEADER`). No se publica ningún puerto al host.

Traducir el contenido (idiomas iniciales en/fr/pt; crea los locales si faltan):
```bash
docker compose -f docker-compose.yml exec web python manage.py translate_content --locales en fr pt
```

### 4. Desarrollo (local)
El `docker-compose.override.yml` se aplica automáticamente: monta el código,
usa `runserver`, settings de dev y publica `127.0.0.1:8000`.
```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
# CSS en modo watch (requiere Node en el host):
make css-watch
```
Abre http://127.0.0.1:8000 (público) y http://127.0.0.1:8000/admin/ (Wagtail).

> En dev, el CSS compilado (`src/static/css/app.css`) debe existir en el host porque
> el volumen monta `./src` sobre `/app`. Genera con `make css`, o cópialo de la imagen:
> `docker cp $(docker create blog-tecnologico-web:latest):/app/static/css/app.css src/static/css/app.css`

---

## Comandos útiles (`make`)

```
make up              # levanta los servicios
make down            # los detiene
make logs s=web      # sigue logs de un servicio
make migrate         # aplica migraciones
make makemigrations  # genera migraciones
make superuser       # crea superusuario
make collectstatic   # recolecta estáticos
make css             # compila Tailwind (host)
make css-watch       # Tailwind en watch
make check           # django check --deploy
make shell           # shell de Django
```

---

## Modelo de contenido (Wagtail)

- **HomePage** — portada con hero + últimos artículos.
- **BlogIndexPage** — listado con paginación, filtro por categoría/tag y búsqueda FTS.
- **ArticlePage** — artículo con `StreamField`: encabezados, párrafos enriquecidos,
  **bloques de código** (resaltado Pygments), callouts, imágenes, citas y embeds.
  Calcula tiempo de lectura automáticamente.
- **Snippets**: `Category`, `Author`, `Comment` (moderación), `Subscriber` (newsletter),
  y `SiteSettings` (redes sociales, pie).

### Apps propias
- `apps.core` — HomePage, páginas genéricas, bloques de StreamField, ajustes de sitio.
- `apps.blog` — artículos, índice, categorías, autores, feed RSS.
- `apps.comments` — comentarios propios con moderación, honeypot y rate-limit (HTMX).
- `apps.newsletter` — suscripción double opt-in y envíos con Celery.
- `apps.accounts` — espacio para extensiones de cuenta (2FA lo gestiona wagtail-2fa).

---

## Multilenguaje (i18n)

**Interfaz (UI):** Django i18n con 12 idiomas (es por defecto + en, fr, it, pt, de,
zh-hans, ja, ru, ko, ar, nl). Cadenas en `src/locale/<lang>/LC_MESSAGES/`; el
entrypoint corre `compilemessages`. Árabe en RTL automático.

**Contenido (artículos):** `wagtail-localize` + **DeepL**. Cada idioma se sirve en su
URL (es en la raíz, el resto con prefijo: `/en/...`, `/fr/...`). El selector del header
solo muestra los idiomas a los que la página actual está traducida (sin 404s).

### Configurar DeepL
1. Crea una clave gratis en https://www.deepl.com/pro-api (las free terminan en `:fx`).
2. Ponla en `.env`: `DEEPL_API_KEY=tu-clave:fx`
3. Reinicia: `docker compose up -d`

### Traducir
- **Todo el sitio (CLI):**
  ```bash
  docker compose exec web python manage.py translate_content --locales en fr pt
  ```
  Es idempotente: vuelve a ejecutarlo al publicar artículos nuevos (solo traduce lo que
  falte). Sin `DEEPL_API_KEY` crea la estructura para traducir a mano.
- **Por artículo (admin):** abre el artículo → botón **Translate** → elige idiomas →
  **Translate with DeepL** → revisa y publica.

### Añadir un idioma nuevo
1. Crea el `Locale` en el admin de Wagtail (o por shell).
2. Tradúcelo con `translate_content` o desde el admin. Aparecerá solo en el selector.

> Nota: los snippets (categorías/autores) aún se comparten entre idiomas; el cuerpo,
> título y extracto de cada artículo sí se traducen.

---

## Seguridad

- **2FA TOTP obligatorio** en el admin de Wagtail (`WAGTAIL_2FA_REQUIRED = True`).
- **django-axes**: bloqueo tras 5 intentos fallidos (IP + usuario).
- **Argon2** como hasher de contraseñas; longitud mínima 12.
- **Cabeceras**: HSTS (configurable), `X-Frame-Options: DENY`, nosniff, referrer-policy,
  cookies `Secure`/`HttpOnly`, CSP (`django-csp`).
- **TLS** delegado a NPM; Django confía en `X-Forwarded-Proto`.
- **Sin tracking de terceros**: fuentes y JS (HTMX/Alpine) self-hosted.
- Postgres y Redis **aislados** en red interna, con contraseña; Redis con `--requirepass`.

> Tras confirmar que el HTTPS es estable, sube `DJANGO_SECURE_HSTS_SECONDS` a `31536000`.

---

## Notas

- **Fuentes**: el CSS referencia *Inter* y *JetBrains Mono*; añade los `@font-face`
  self-hosted en `tailwind/src/input.css` (o se usa la fuente del sistema como fallback).
- **Migraciones de apps propias**: ya incluidas en `src/apps/*/migrations/`.
- El `.env` real **no** se versiona; solo `.env.example`.
