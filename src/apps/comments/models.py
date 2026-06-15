"""Sistema de comentarios propio con moderación e hilos."""
from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Comment(models.Model):
    """
    Comentario sobre un artículo del blog.

    Se modera desde el admin de Wagtail (snippet). Los comentarios entran
    como NO aprobados por defecto y solo se muestran tras revisión.
    """

    article = models.ForeignKey(
        "blog.ArticlePage",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Artículo",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Respuesta a",
    )
    author_name = models.CharField(max_length=80, verbose_name="Nombre")
    author_email = models.EmailField(verbose_name="Email", help_text="No se publica.")
    body = models.TextField(max_length=3000, verbose_name="Comentario")

    is_approved = models.BooleanField(default=False, verbose_name="Aprobado")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    # Metadatos para moderación / anti-abuso.
    ip_address = models.GenericIPAddressField(null=True, blank=True, editable=False)
    user_agent = models.CharField(max_length=255, blank=True, editable=False)

    panels = [
        FieldPanel("is_approved"),
        FieldPanel("article", read_only=True),
        FieldPanel("parent", read_only=True),
        FieldPanel("author_name", read_only=True),
        FieldPanel("author_email", read_only=True),
        FieldPanel("body", read_only=True),
    ]

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["article", "is_approved"]),
        ]

    def __str__(self):
        return f"{self.author_name} en «{self.article}»"

    @property
    def approved_replies(self):
        return self.replies.filter(is_approved=True).order_by("created_at")
