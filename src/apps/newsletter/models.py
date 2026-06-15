"""Modelos del newsletter: suscriptores con double opt-in."""
import secrets

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


def generate_token():
    return secrets.token_urlsafe(32)


@register_snippet
class Subscriber(models.Model):
    """Suscriptor del boletín con confirmación por email (double opt-in)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmado"
        UNSUBSCRIBED = "unsubscribed", "Dado de baja"

    email = models.EmailField(unique=True, verbose_name="Email")
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Estado",
    )
    # Token usado tanto para confirmar como para darse de baja.
    token = models.CharField(
        max_length=64, default=generate_token, unique=True, editable=False
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    confirmed_at = models.DateTimeField(null=True, blank=True, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True, editable=False)

    panels = [
        FieldPanel("email", read_only=True),
        FieldPanel("status"),
        FieldPanel("created_at", read_only=True),
        FieldPanel("confirmed_at", read_only=True),
    ]

    class Meta:
        verbose_name = "Suscriptor"
        verbose_name_plural = "Suscriptores"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_status_display()})"

    def confirm(self):
        self.status = self.Status.CONFIRMED
        self.confirmed_at = timezone.now()
        # Rota el token tras confirmar (el viejo link queda inservible).
        self.token = generate_token()
        self.save(update_fields=["status", "confirmed_at", "token"])

    def unsubscribe(self):
        self.status = self.Status.UNSUBSCRIBED
        self.save(update_fields=["status"])
