"""
Configura el Site por defecto de Wagtail a partir de WAGTAIL_BASE_URL.

Idempotente: se ejecuta en cada arranque (entrypoint) para que el hostname
coincida con el dominio productivo (p. ej. blog.cyco.tech).
"""
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import Site


class Command(BaseCommand):
    help = "Ajusta el hostname/puerto del Site por defecto desde WAGTAIL_BASE_URL."

    def handle(self, *args, **opts):
        base_url = getattr(settings, "WAGTAIL_BASE_URL", "") or ""
        parsed = urlparse(base_url)
        hostname = parsed.hostname
        if not hostname:
            self.stdout.write(self.style.WARNING(
                "WAGTAIL_BASE_URL no define un hostname; no se cambia el Site."))
            return

        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            self.stdout.write(self.style.WARNING("No hay Site por defecto todavía."))
            return

        changed = []
        if site.hostname != hostname:
            site.hostname = hostname
            changed.append("hostname=%s" % hostname)
        if site.port != port:
            site.port = port
            changed.append("port=%s" % port)
        if site.site_name != settings.WAGTAIL_SITE_NAME:
            site.site_name = settings.WAGTAIL_SITE_NAME
            changed.append("site_name")

        if changed:
            site.save()
            self.stdout.write(self.style.SUCCESS(
                "Site actualizado: %s" % ", ".join(changed)))
        else:
            self.stdout.write("Site ya estaba correcto (%s:%s)." % (hostname, port))
