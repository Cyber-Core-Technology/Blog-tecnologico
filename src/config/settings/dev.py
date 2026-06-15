"""
Settings de DESARROLLO.

DEBUG activo, email a consola, media en disco local, sin S3 ni SSL.
"""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "web"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# Email a consola en dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Sin redirección SSL en local.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Debug toolbar y extensions (instaladas vía requirements/dev.txt).
# Se cargan solo si están disponibles, para que el proyecto no se caiga si la
# imagen se construyó con requirements de producción.
from importlib.util import find_spec  # noqa: E402

if find_spec("debug_toolbar") and find_spec("django_extensions"):
    INSTALLED_APPS += ["debug_toolbar", "django_extensions"]  # noqa: F405
    MIDDLEWARE.insert(  # noqa: F405
        0, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )
    INTERNAL_IPS = ["127.0.0.1"]
    # En Docker el cliente no es 127.0.0.1; muestra la toolbar siempre en dev.
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}

# Relaja la CSP en dev para no estorbar la toolbar.
CSP_IMG_SRC = ("'self'", "data:", "https:", "http:")  # noqa: F405
