"""Context processors propios disponibles en todas las plantillas."""

# Opciones del selector de idioma: (código, bandera, nombre nativo).
LANG_OPTIONS = [
    ("es", "🇲🇽", "Español"),
    ("en", "🇺🇸", "English"),
    ("fr", "🇫🇷", "Français"),
    ("it", "🇮🇹", "Italiano"),
    ("pt", "🇧🇷", "Português"),
    ("de", "🇩🇪", "Deutsch"),
    ("zh-hans", "🇨🇳", "中文"),
    ("ja", "🇯🇵", "日本語"),
    ("ru", "🇷🇺", "Русский"),
    ("ko", "🇰🇷", "한국어"),
    ("ar", "🇸🇦", "العربية"),
    ("nl", "🇳🇱", "Nederlands"),
]


def language_options(request):
    return {"lang_options": LANG_OPTIONS}


def nav_urls(request):
    """
    URLs de navegación localizadas (home e índice del blog) según el idioma
    activo, para que el menú apunte a la versión del locale correcto.
    """
    from django.utils.translation import get_language
    from wagtail.models import Locale

    from apps.blog.models import BlogIndexPage
    from apps.core.models import HomePage

    home_url, blog_url = "/", "/blog/"
    try:
        locale = Locale.objects.get(language_code=get_language())
        home = HomePage.objects.filter(locale=locale).live().first()
        idx = BlogIndexPage.objects.filter(locale=locale).live().first()
        if home:
            home_url = home.url or home_url
        if idx:
            blog_url = idx.url or blog_url
    except Locale.DoesNotExist:
        pass
    except Exception:  # noqa: BLE001 — nunca romper el render por la navegación
        pass
    return {"nav_home_url": home_url, "nav_blog_url": blog_url}
