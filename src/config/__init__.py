# Asegura que la app de Celery se cargue al iniciar Django,
# para que el decorador @shared_task pueda usar la instancia.
from .celery import app as celery_app

__all__ = ("celery_app",)
