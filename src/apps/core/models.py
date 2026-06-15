"""Modelos del núcleo: página de inicio y ajustes globales del sitio."""
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Page


class HomePage(Page):
    """Página de inicio del blog."""

    subtitle = models.CharField(
        max_length=255, blank=True, verbose_name="Subtítulo"
    )
    intro = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        verbose_name="Introducción",
    )
    hero_cta_text = models.CharField(
        max_length=80, blank=True, verbose_name="Texto del botón principal"
    )
    # CharField (no URLField) para permitir enlaces internos relativos como "/blog/".
    hero_cta_link = models.CharField(
        max_length=255, blank=True, verbose_name="Enlace del botón",
        help_text="URL absoluta o ruta interna (p. ej. /blog/).",
    )

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("intro"),
        MultiFieldPanel(
            [FieldPanel("hero_cta_text"), FieldPanel("hero_cta_link")],
            heading="Llamada a la acción",
        ),
    ]

    # Solo puede haber una home; permite blog index como hijo.
    subpage_types = ["blog.BlogIndexPage", "core.GenericPage"]
    max_count = 1

    def get_context(self, request, *args, **kwargs):
        from apps.blog.models import ArticlePage

        context = super().get_context(request, *args, **kwargs)
        context["latest_articles"] = (
            ArticlePage.objects.live().public().order_by("-date")[:6]
        )
        return context

    class Meta:
        verbose_name = "Página de inicio"


class GenericPage(Page):
    """Página estática genérica (Acerca de, Contacto, Privacidad...)."""

    body = RichTextField(blank=True, verbose_name="Contenido")

    content_panels = Page.content_panels + [FieldPanel("body")]

    class Meta:
        verbose_name = "Página genérica"


@register_setting
class SiteSettings(BaseGenericSetting):
    """Ajustes globales editables desde el admin de Wagtail."""

    tagline = models.CharField(
        max_length=255, blank=True, verbose_name="Eslogan"
    )
    github_url = models.URLField(blank=True, verbose_name="GitHub")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter / X")
    mastodon_url = models.URLField(blank=True, verbose_name="Mastodon")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    footer_text = RichTextField(
        blank=True, features=["bold", "italic", "link"], verbose_name="Texto del pie"
    )

    panels = [
        FieldPanel("tagline"),
        MultiFieldPanel(
            [
                FieldPanel("github_url"),
                FieldPanel("twitter_url"),
                FieldPanel("mastodon_url"),
                FieldPanel("linkedin_url"),
            ],
            heading="Redes sociales",
        ),
        FieldPanel("footer_text"),
    ]

    class Meta:
        verbose_name = "Ajustes del sitio"
