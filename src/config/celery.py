"""Configuración de Celery para el proyecto."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("blog")

# Toma la configuración desde los settings de Django con el prefijo CELERY_.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubre tasks.py en todas las apps instaladas.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
