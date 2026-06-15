"""Template tags de i18n: selector de idioma consciente de la página."""
from django import template
from django.utils.translation import get_language
from wagtail.models import Locale

from apps.core.context_processors import LANG_OPTIONS

register = template.Library()


@register.inclusion_tag("includes/lang_switcher.html", takes_context=True)
def language_switcher(context):
    """
    Construye las opciones del selector de idioma.

    - Si hay una página Wagtail en contexto: muestra solo los idiomas a los que
      ESA página está traducida y publicada, enlazando a cada traducción.
    - Si no (vistas no-página): enlaza a la home de cada locale disponible.

    Así nunca se enlaza a una URL inexistente (sin 404).
    """
    current = get_language() or "es"
    page = context.get("page")
    options = []

    if page is not None:
        try:
            translations = page.get_translations(inclusive=True).live().specific()
            url_by_lang = {t.locale.language_code: t.url for t in translations}
        except Exception:  # noqa: BLE001
            url_by_lang = {}
        for code, flag, name in LANG_OPTIONS:
            if code in url_by_lang:
                options.append({
                    "code": code, "flag": flag, "name": name,
                    "url": url_by_lang[code], "active": code == current,
                })

    if not options:
        content_codes = set(Locale.objects.values_list("language_code", flat=True))
        for code, flag, name in LANG_OPTIONS:
            if code in content_codes:
                options.append({
                    "code": code, "flag": flag, "name": name,
                    "url": "/" if code == "es" else "/%s/" % code,
                    "active": code == current,
                })

    return {"options": options, "current_lang": current}
