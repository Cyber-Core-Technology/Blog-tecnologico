"""
Settings de PRODUCCIÓN.

Endurece la seguridad, activa S3 para media y SMTP para email.
TLS lo termina Nginx Proxy Manager, por eso confiamos en la cabecera
X-Forwarded-Proto que NPM envía.
"""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# -----------------------------------------------------------------------------
# Seguridad HTTP — detrás de NPM (que termina TLS)
# -----------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

# El healthcheck del contenedor llega por HTTP a 127.0.0.1 (sin pasar por NPM).
# Permitimos ese host interno y eximimos /healthz/ de la redirección a HTTPS,
# para que el chequeo reciba 200 y el contenedor quede "healthy".
ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ["127.0.0.1", "localhost"]  # noqa: F405
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # necesario si HTMX necesita leer el token vía JS
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# HSTS — empieza en 0 y sube a 31536000 cuando el HTTPS sea estable.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# -----------------------------------------------------------------------------
# Media en AWS S3 (django-storages + boto3)
# -----------------------------------------------------------------------------
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="") or None

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None              # respeta la política/bucket-owner-enforced
AWS_QUERYSTRING_AUTH = False        # URLs públicas y cacheables
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_S3_SIGNATURE_VERSION = "s3v4"

STORAGES["default"] = {  # noqa: F405
    "BACKEND": "storages.backends.s3.S3Storage",
}

# -----------------------------------------------------------------------------
# Email vía SMTP
# -----------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = 20

# -----------------------------------------------------------------------------
# Logging a stdout (capturado por Docker)
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "axes": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
