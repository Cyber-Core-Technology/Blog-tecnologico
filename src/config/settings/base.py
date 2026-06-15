"""
Settings base — compartidos entre desarrollo y producción.

Los valores sensibles y dependientes del entorno se leen con django-environ.
NO pongas secretos aquí; usa el archivo .env.
"""
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

# -----------------------------------------------------------------------------
# Rutas
# -----------------------------------------------------------------------------
# BASE_DIR apunta a /app (donde vive manage.py dentro del contenedor).
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR / "config"

# -----------------------------------------------------------------------------
# Entorno
# -----------------------------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# En contenedor las variables vienen del env_file; en local lee .env si existe.
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

WAGTAIL_BASE_URL = env("WAGTAIL_BASE_URL", default="http://localhost:8000")

# -----------------------------------------------------------------------------
# Aplicaciones
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Apps propias
    "apps.core",
    "apps.blog",
    "apps.comments",
    "apps.newsletter",
    "apps.accounts",

    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.sitemaps",
    "wagtail.contrib.settings",
    "wagtail.contrib.styleguide",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    # Traducción de contenido (wagtail-localize). `.locales` reemplaza a wagtail.locales.
    "wagtail_localize",
    "wagtail_localize.locales",
    "modelcluster",
    "taggit",

    # 2FA del admin de Wagtail (wagtail-2fa sobre django-otp)
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "wagtail_2fa",

    # Seguridad / utilidades
    "axes",
    "django_celery_beat",

    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise justo después de SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # i18n: detecta el idioma activo (cookie/sesión/Accept-Language).
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # OTP debe ir después de AuthenticationMiddleware.
    "django_otp.middleware.OTPMiddleware",
    # wagtail-2fa: fuerza la verificación TOTP de usuarios staff en el admin.
    "wagtail_2fa.middleware.VerifyUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Content-Security-Policy.
    "csp.middleware.CSPMiddleware",
    # django-axes debe ser el ÚLTIMO para envolver la autenticación.
    "axes.middleware.AxesMiddleware",
    # Redirects de Wagtail.
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.core.context_processors.language_options",
                "apps.core.context_processors.nav_urls",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# -----------------------------------------------------------------------------
# Base de datos (PostgreSQL)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="blog"),
        "USER": env("POSTGRES_USER", default="blog"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="blog"),
        "HOST": env("POSTGRES_HOST", default="postgres"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"connect_timeout": 10},
    }
}

# -----------------------------------------------------------------------------
# Cache / sesiones / Celery (Redis)
# -----------------------------------------------------------------------------
REDIS_PASSWORD = env("REDIS_PASSWORD", default="")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@redis:6379"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Celery
CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/2"
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "America/Mexico_City"
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# -----------------------------------------------------------------------------
# Autenticación
# -----------------------------------------------------------------------------
# Orden importante: axes primero, luego el backend por defecto.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Argon2 como hasher principal.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Login del admin de Wagtail (wagtail-2fa intercepta la verificación TOTP).
LOGIN_URL = "wagtailadmin_login"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/"

# wagtail-2fa: obliga a todos los usuarios staff a configurar y usar 2FA.
WAGTAIL_2FA_REQUIRED = True

# -----------------------------------------------------------------------------
# django-axes (bloqueo por fuerza bruta)
# -----------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # horas
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ADMIN = True
AXES_LOCKOUT_TEMPLATE = "account/lockout.html"

# -----------------------------------------------------------------------------
# Internacionalización
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "es"  # idioma principal por defecto

# Idiomas disponibles en el selector (nombres nativos).
LANGUAGES = [
    ("es", _("Español")),
    ("en", _("English")),
    ("fr", _("Français")),
    ("it", _("Italiano")),
    ("pt", _("Português")),
    ("de", _("Deutsch")),
    ("zh-hans", _("中文")),
    ("ja", _("日本語")),
    ("ru", _("Русский")),
    ("ko", _("한국어")),
    ("ar", _("العربية")),
    ("nl", _("Nederlands")),
]

# Carpeta con las traducciones (.po/.mo).
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Archivos estáticos (WhiteNoise) y media (S3 en producción)
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# El media (default storage) se sobreescribe en producción para usar S3.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# -----------------------------------------------------------------------------
# Email (sobrescrito por entorno)
# -----------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# -----------------------------------------------------------------------------
# Content Security Policy (django-csp 3.x)
# -----------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Alpine/HTMX inline; afinar con nonces si se desea
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'self'", "https://www.youtube-nocookie.com")
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
# El admin de Wagtail necesita CSP más laxa (eval/inline de su JS). Va detrás
# de login + 2FA, así que se excluye del CSP estricto del sitio público.
CSP_EXCLUDE_URL_PREFIXES = ("/admin", "/django-admin")

# -----------------------------------------------------------------------------
# Wagtail
# -----------------------------------------------------------------------------
WAGTAIL_SITE_NAME = "CyCoTech Blog"
WAGTAILADMIN_BASE_URL = WAGTAIL_BASE_URL

# --- i18n de contenido (wagtail-localize) ---
WAGTAIL_I18N_ENABLED = True
# Idiomas a los que se puede traducir el contenido (mismos que la UI).
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Traductor automático: DeepL. La key se pone en .env (DEEPL_API_KEY).
# Las keys gratuitas terminan en ":fx" (usan el endpoint api-free).
WAGTAILLOCALIZE_MACHINE_TRANSLATOR = {
    "CLASS": "wagtail_localize.machine_translators.deepl.DeepLTranslator",
    "OPTIONS": {
        "AUTH_KEY": env("DEEPL_API_KEY", default=""),
    },
}
WAGTAILDOCS_EXTENSIONS = ["csv", "docx", "key", "odt", "pdf", "pptx", "rtf", "txt", "xlsx", "zip"]

# Búsqueda con PostgreSQL Full-Text Search.
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# -----------------------------------------------------------------------------
# Varios
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tamaño máximo de subida en memoria (10 MB) — evita DoS por uploads.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000
