"""Vista de envío de comentarios (compatible con HTMX)."""
from django.core.cache import cache
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.blog.models import ArticlePage

from .forms import CommentForm

# Límite anti-spam: nº de comentarios por IP en la ventana indicada.
RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW = 600  # segundos (10 min)


def _client_ip(request):
    # NPM coloca la IP real en X-Forwarded-For.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@require_POST
def post_comment(request, article_id):
    article = get_object_or_404(
        ArticlePage.objects.live().public(), id=article_id
    )

    if not article.allow_comments:
        return render(
            request,
            "comments/_form_response.html",
            {"error": "Los comentarios están cerrados en este artículo."},
            status=403,
        )

    ip = _client_ip(request)
    rate_key = f"comment_rate:{ip}"
    count = cache.get(rate_key, 0)
    if count >= RATE_LIMIT_COUNT:
        return render(
            request,
            "comments/_form_response.html",
            {"error": "Has enviado demasiados comentarios. Inténtalo más tarde."},
            status=429,
        )

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.ip_address = ip
        comment.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
        comment.is_approved = False  # entra a moderación
        comment.save()

        cache.set(rate_key, count + 1, RATE_LIMIT_WINDOW)

        return render(
            request,
            "comments/_form_response.html",
            {"success": "¡Gracias! Tu comentario se publicará tras ser revisado."},
        )

    return render(
        request,
        "comments/_form_response.html",
        {"form": form, "article": article, "error": "Revisa los campos del formulario."},
        status=400,
    )
