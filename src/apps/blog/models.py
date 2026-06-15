"""Modelos del blog: índice, artículos, categorías y autores."""
from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from apps.core.blocks import BodyStreamBlock


# -----------------------------------------------------------------------------
# Snippets reutilizables
# -----------------------------------------------------------------------------
@register_snippet
class Category(models.Model):
    """Categoría temática: Programación, Ciberseguridad, DevOps, etc."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True, verbose_name="Descripción")
    # Color de acento (clase Tailwind o hex) para los badges.
    color = models.CharField(
        max_length=20, default="indigo", verbose_name="Color de acento"
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("description"),
        FieldPanel("color"),
    ]

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["name"]

    def __str__(self):
        return self.name


@register_snippet
class Author(models.Model):
    """Autor del artículo (desacoplado del usuario de Django)."""

    name = models.CharField(max_length=120, verbose_name="Nombre")
    slug = models.SlugField(max_length=140, unique=True)
    bio = models.TextField(blank=True, verbose_name="Biografía")
    avatar = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Avatar",
    )
    website = models.URLField(blank=True, verbose_name="Sitio web")

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("bio"),
        FieldPanel("avatar"),
        FieldPanel("website"),
    ]

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ArticleTag(TaggedItemBase):
    content_object = ParentalKey(
        "blog.ArticlePage", related_name="tagged_items", on_delete=models.CASCADE
    )


# -----------------------------------------------------------------------------
# Páginas
# -----------------------------------------------------------------------------
class BlogIndexPage(Page):
    """Listado de artículos con paginación y filtro por categoría/tag."""

    intro = models.CharField(max_length=255, blank=True, verbose_name="Introducción")

    content_panels = Page.content_panels + [FieldPanel("intro")]

    subpage_types = ["blog.ArticlePage"]
    parent_page_types = ["core.HomePage"]

    def get_articles(self, request):
        articles = (
            ArticlePage.objects.child_of(self)
            .live()
            .public()
            .order_by("-date")
            .select_related("category", "author")
        )
        category = request.GET.get("categoria")
        if category:
            articles = articles.filter(category__slug=category)
        tag = request.GET.get("tag")
        if tag:
            articles = articles.filter(tags__name=tag)
        query = request.GET.get("q")
        if query:
            articles = articles.search(query)
        return articles

    def get_context(self, request, *args, **kwargs):
        from django.core.paginator import Paginator

        context = super().get_context(request, *args, **kwargs)
        articles = self.get_articles(request)

        paginator = Paginator(articles, 9)
        page = request.GET.get("page")
        context["articles"] = paginator.get_page(page)
        context["categories"] = Category.objects.all()
        context["active_category"] = request.GET.get("categoria", "")
        context["search_query"] = request.GET.get("q", "")
        return context

    class Meta:
        verbose_name = "Índice del blog"


class ArticlePage(Page):
    """Artículo individual del blog."""

    date = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de publicación"
    )
    excerpt = models.TextField(
        max_length=400,
        blank=True,
        verbose_name="Extracto",
        help_text="Resumen breve para listados y SEO.",
    )
    category = models.ForeignKey(
        "blog.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles",
        verbose_name="Categoría",
    )
    author = models.ForeignKey(
        "blog.Author",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles",
        verbose_name="Autor",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Imagen de portada",
    )
    tags = ClusterTaggableManager(through=ArticleTag, blank=True, verbose_name="Tags")
    body = StreamField(
        BodyStreamBlock(),
        use_json_field=True,
        verbose_name="Cuerpo",
    )
    reading_time = models.PositiveSmallIntegerField(
        default=0, verbose_name="Tiempo de lectura (min)", editable=False
    )
    allow_comments = models.BooleanField(
        default=True, verbose_name="Permitir comentarios"
    )

    # Índices de búsqueda (PostgreSQL FTS vía Wagtail).
    search_fields = Page.search_fields + [
        index.SearchField("excerpt"),
        index.SearchField("body"),
        index.FilterField("date"),
        index.RelatedFields("category", [index.SearchField("name")]),
        index.RelatedFields("tags", [index.SearchField("name")]),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("author"),
                FieldPanel("category"),
                FieldPanel("tags"),
            ],
            heading="Metadatos",
        ),
        FieldPanel("cover_image"),
        FieldPanel("excerpt"),
        FieldPanel("body"),
        FieldPanel("allow_comments"),
    ]

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    def save(self, *args, **kwargs):
        # Calcula el tiempo de lectura (~200 palabras/min) a partir del cuerpo.
        words = len(str(self.body).split())
        self.reading_time = max(1, round(words / 200))
        super().save(*args, **kwargs)

    @property
    def approved_comments(self):
        return self.comments.filter(is_approved=True, parent__isnull=True)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["related"] = (
            ArticlePage.objects.live()
            .public()
            .filter(category=self.category)
            .exclude(id=self.id)
            .order_by("-date")[:3]
        )
        return context

    class Meta:
        verbose_name = "Artículo"
