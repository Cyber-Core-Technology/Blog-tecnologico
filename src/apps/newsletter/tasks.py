"""Tareas Celery del newsletter: envíos asíncronos."""
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_confirmation_email(self, subscriber_id):
    """Envía el email de confirmación (double opt-in)."""
    from .models import Subscriber

    try:
        subscriber = Subscriber.objects.get(id=subscriber_id)
    except Subscriber.DoesNotExist:
        return

    base = settings.WAGTAIL_BASE_URL.rstrip("/")
    confirm_url = base + reverse("newsletter:confirm", args=[subscriber.token])

    context = {"confirm_url": confirm_url, "email": subscriber.email}
    subject = "Confirma tu suscripción al CyCoTech Blog"
    text_body = render_to_string("newsletter/email/confirm.txt", context)
    html_body = render_to_string("newsletter/email/confirm.html", context)

    try:
        msg = EmailMultiAlternatives(
            subject, text_body, settings.DEFAULT_FROM_EMAIL, [subscriber.email]
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_broadcast(self, subject, html_body, text_body):
    """
    Envía un boletín a todos los suscriptores confirmados.
    Incluye un enlace de baja individual por destinatario.
    """
    from .models import Subscriber

    base = settings.WAGTAIL_BASE_URL.rstrip("/")
    recipients = Subscriber.objects.filter(status=Subscriber.Status.CONFIRMED)

    sent = 0
    for sub in recipients.iterator():
        unsub_url = base + reverse("newsletter:unsubscribe", args=[sub.token])
        personal_html = html_body.replace("{{unsubscribe_url}}", unsub_url)
        personal_text = text_body.replace("{{unsubscribe_url}}", unsub_url)
        try:
            msg = EmailMultiAlternatives(
                subject, personal_text, settings.DEFAULT_FROM_EMAIL, [sub.email]
            )
            msg.attach_alternative(personal_html, "text/html")
            msg.send()
            sent += 1
        except Exception:  # noqa: BLE001 — no abortar el lote por un fallo individual
            continue
    return {"sent": sent}
