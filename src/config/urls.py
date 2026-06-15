"""URLs raíz del proyecto."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.contrib import admin
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap as wagtail_sitemap
from wagtail.documents import urls as wagtaildocs_urls

from apps.blog.feeds import LatestArticlesFeed
from apps.core.views import healthz

urlpatterns = [
    # Healthcheck (usado por el healthcheck del contenedor).
    path("healthz/", healthz, name="healthz"),

    # Cambio de idioma (set_language) — i18n.
    path("i18n/", include("django.conf.urls.i18n")),

    # Admin de Django (protegido por axes). El admin principal es Wagtail.
    path("django-admin/", admin.site.urls),

    # Admin de Wagtail (2FA forzado por wagtail-2fa).
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),

    # Funcionalidades del blog.
    path("comments/", include("apps.comments.urls")),
    path("newsletter/", include("apps.newsletter.urls")),

    # SEO.
    path("sitemap.xml", wagtail_sitemap),
    path("feed/", LatestArticlesFeed(), name="rss_feed"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass

# Páginas de Wagtail servidas por idioma (i18n_patterns).
# El idioma por defecto (es) se sirve SIN prefijo; el resto con /<lang>/.
# Debe ir al FINAL: captura todas las rutas de páginas.
urlpatterns += i18n_patterns(
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)
