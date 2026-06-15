"""
Traduce el árbol de páginas a otros idiomas con wagtail-localize + DeepL.

Uso:
    # Traducir a los locales por defecto (todos menos el de origen)
    python manage.py translate_content

    # Solo a idiomas concretos
    python manage.py translate_content --locales en fr pt

    # Sin traducción automática (solo crea la estructura para traducir a mano)
    python manage.py translate_content --no-machine

Es idempotente: re-ejecútalo cuando publiques artículos nuevos; solo traduce
los segmentos que aún no estén traducidos.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from wagtail.models import Locale, Page
from wagtail_localize.machine_translators import get_machine_translator
from wagtail_localize.models import Translation, TranslationSource
from wagtail_localize.views.edit_translation import apply_machine_translation


class Command(BaseCommand):
    help = "Traduce las páginas a otros idiomas (wagtail-localize + DeepL)."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="es", help="Idioma de origen (def. es)")
        parser.add_argument("--locales", nargs="*", help="Idiomas destino (def. todos)")
        parser.add_argument("--no-machine", action="store_true",
                            help="No usar traducción automática (solo estructura)")
        parser.add_argument("--no-publish", action="store_true",
                            help="Crear como borrador en vez de publicar")

    def handle(self, *args, **opts):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).order_by("id").first()
        if user is None:
            raise CommandError("No hay superusuario. Crea uno con createsuperuser.")

        try:
            source_locale = Locale.objects.get(language_code=opts["source"])
        except Locale.DoesNotExist:
            raise CommandError("No existe el locale de origen '%s'." % opts["source"])

        if opts["locales"]:
            # Crea los locales destino que aún no existan.
            targets = []
            for code in opts["locales"]:
                loc, created = Locale.objects.get_or_create(language_code=code)
                if created:
                    self.stdout.write(self.style.SUCCESS("Locale creado: %s" % code))
                targets.append(loc)
        else:
            targets = list(Locale.objects.exclude(id=source_locale.id))
        if not targets:
            raise CommandError(
                "No hay locales destino. Indícalos con --locales en fr pt")

        translator = None if opts["no_machine"] else get_machine_translator()
        if translator is None and not opts["no_machine"]:
            self.stdout.write(self.style.WARNING(
                "Sin traductor automático (¿falta DEEPL_API_KEY?). "
                "Se creará solo la estructura; tradúcela en el admin."))

        # Páginas del árbol de origen, en orden (padres antes que hijos).
        pages = list(
            Page.objects.filter(locale=source_locale)
            .exclude(depth=1)  # excluye la raíz del árbol
            .order_by("depth", "path")
            .specific()
        )
        publish = not opts["no_publish"]

        for locale in targets:
            self.stdout.write(self.style.MIGRATE_HEADING(
                "→ %s" % locale.get_display_name()))
            for page in pages:
                source, _ = TranslationSource.get_or_create_from_instance(page)
                translation, _ = Translation.objects.get_or_create(
                    source=source, target_locale=locale)
                if translator and translator.can_translate(source_locale, locale):
                    try:
                        apply_machine_translation(translation.id, user, translator)
                    except Exception as e:  # noqa: BLE001
                        self.stdout.write(self.style.ERROR(
                            "   ! %s: %s" % (page.title, repr(e)[:120])))
                try:
                    translation.save_target(publish=publish)
                    self.stdout.write("   ✓ %s" % page.title)
                except Exception as e:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(
                        "   ! save %s: %s" % (page.title, repr(e)[:120])))

        self.stdout.write(self.style.SUCCESS("Listo."))
