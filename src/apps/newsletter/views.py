"""Vistas del newsletter: alta (HTMX), confirmación y baja."""
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Subscriber
from .tasks import send_confirmation_email


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@require_POST
def subscribe(request):
    """Alta vía HTMX. Crea/reactiva al suscriptor y dispara el email de confirmación."""
    email = (request.POST.get("email") or "").strip().lower()

    # Honeypot.
    if request.POST.get("website"):
        return render(request, "newsletter/_response.html", {"success": "¡Gracias!"})

    if not email or "@" not in email:
        return render(
            request,
            "newsletter/_response.html",
            {"error": "Introduce un email válido."},
            status=400,
        )

    # Rate limit por IP.
    ip = _client_ip(request)
    key = f"newsletter_rate:{ip}"
    if cache.get(key, 0) >= 5:
        return render(
            request,
            "newsletter/_response.html",
            {"error": "Demasiados intentos. Inténtalo más tarde."},
            status=429,
        )
    cache.set(key, cache.get(key, 0) + 1, 600)

    subscriber, created = Subscriber.objects.get_or_create(
        email=email, defaults={"ip_address": ip}
    )

    if subscriber.status == Subscriber.Status.CONFIRMED:
        return render(
            request,
            "newsletter/_response.html",
            {"success": "Ya estabas suscrito. ¡Gracias!"},
        )

    # (Re)activa el flujo de confirmación.
    if not created:
        subscriber.status = Subscriber.Status.PENDING
        subscriber.save(update_fields=["status"])

    send_confirmation_email.delay(subscriber.id)

    return render(
        request,
        "newsletter/_response.html",
        {"success": "Te enviamos un email para confirmar tu suscripción."},
    )


def confirm(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if subscriber.status == Subscriber.Status.PENDING:
        subscriber.confirm()
    return render(request, "newsletter/confirmed.html", {"subscriber": subscriber})


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    subscriber.unsubscribe()
    return render(request, "newsletter/unsubscribed.html", {"subscriber": subscriber})
