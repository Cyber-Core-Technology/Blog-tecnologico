from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """
    Healthcheck ligero para el contenedor / NPM.
    Verifica que la app responde y que la base de datos está accesible.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # noqa: BLE001
        return JsonResponse({"status": "error", "db": "down"}, status=503)
    return JsonResponse({"status": "ok"})
