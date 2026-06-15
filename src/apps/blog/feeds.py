"""Feed RSS/Atom de los últimos artículos."""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from .models import ArticlePage


class LatestArticlesFeed(Feed):
    title = "CyCoTech Blog — Últimos artículos"
    link = "/feed/"
    description = "Programación, ciberseguridad, DevOps y más."
    feed_type = Atom1Feed

    def get_object(self, request, *args, **kwargs):
        # Guardamos el request para construir URLs absolutas correctas
        # (basadas en el host real, no en el hostname del Site de Wagtail).
        self.request = request
        return super().get_object(request, *args, **kwargs)

    def items(self):
        return ArticlePage.objects.live().public().order_by("-date")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.search_description

    def item_link(self, item):
        # Construye la URL absoluta a partir del host REAL de la petición
        # (no del hostname del Site de Wagtail). Correcto en dev y, tras NPM,
        # usa el dominio real con https.
        request = getattr(self, "request", None)
        path = item.url or ""
        if request is not None:
            return request.build_absolute_uri(path)
        return item.full_url or path

    def item_pubdate(self, item):
        return item.date

    def item_categories(self, item):
        return [item.category.name] if item.category else []

    def item_author_name(self, item):
        return item.author.name if item.author else None
