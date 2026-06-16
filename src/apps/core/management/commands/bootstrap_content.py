"""
Crea el contenido inicial del sitio (Home + índice + artículo de ejemplo) y lo
enlaza al Site por defecto. Idempotente: si ya existe, no duplica.

Uso:
    python manage.py bootstrap_content
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wagtail.models import Page, Site


class Command(BaseCommand):
    help = "Crea la Home, el índice del blog y un artículo de ejemplo."

    @transaction.atomic
    def handle(self, *args, **opts):
        from apps.blog.models import ArticlePage, Author, BlogIndexPage, Category
        from apps.core.models import HomePage

        from django.conf import settings

        root = Page.objects.get(depth=1)

        # Página "Welcome" por defecto de Wagtail (un Page normal en depth 2).
        welcome = (
            Page.objects.filter(depth=2)
            .exclude(id__in=HomePage.objects.values("id"))
            .first()
        )

        # 1. HomePage (con slug temporal para evitar choque con 'home' del welcome)
        home = HomePage.objects.first()
        if not home:
            home = HomePage(
                title="CyCoTech Blog",
                slug="home-cyco",
                subtitle="Programación, ciberseguridad y DevOps sin rodeos.",
                hero_cta_text="Explorar artículos",
                hero_cta_link="/blog/",
            )
            root.add_child(instance=home)
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("HomePage creada."))
        else:
            self.stdout.write("HomePage ya existe.")

        # 2. Repuntar el Site por defecto a la Home ANTES de borrar la welcome
        #    (si no, al borrar la raíz del Site se borra el Site en cascada).
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            site = Site.objects.create(
                is_default_site=True, hostname="localhost", port=80,
                root_page=home, site_name=settings.WAGTAIL_SITE_NAME)
        elif site.root_page_id != home.id:
            site.root_page = home
            site.save()
        self.stdout.write(self.style.SUCCESS("Site enlazado a la HomePage."))

        # 3. Borrar la welcome (ya no es raíz del Site) y liberar el slug 'home'
        if welcome and welcome.id != home.id:
            welcome.delete()
        if home.slug != "home":
            home.slug = "home"
            home.save_revision().publish()

        # 3. Índice del blog
        idx = BlogIndexPage.objects.first()
        if not idx:
            idx = BlogIndexPage(
                title="Artículos", slug="blog",
                intro="Lo último que he escrito.",
            )
            home.add_child(instance=idx)
            idx.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Índice del blog creado."))

        # 4. Categoría y autor de ejemplo
        cat, _ = Category.objects.get_or_create(
            slug="ciberseguridad",
            defaults={"name": "Ciberseguridad", "color": "maroon"},
        )
        Category.objects.get_or_create(
            slug="programacion",
            defaults={"name": "Programación", "color": "steel"},
        )
        author, _ = Author.objects.get_or_create(
            slug="cyco", defaults={"name": "CyCoTech", "bio": "Equipo de CyCoTech."}
        )

        # 5. Artículo de ejemplo
        if not ArticlePage.objects.exists():
            art = ArticlePage(
                title="Hardening de un servidor Linux: primeros 10 pasos",
                slug="hardening-linux",
                date=timezone.now(),
                excerpt="Una guía práctica para asegurar un VPS recién creado.",
                category=cat, author=author,
                body=[
                    ("heading", "Introducción"),
                    ("paragraph", "<p>Asegurar un servidor empieza por lo básico: "
                                  "usuarios, SSH y firewall.</p>"),
                    ("code", {"language": "bash", "caption": "ufw.sh",
                              "code": "sudo ufw default deny incoming\n"
                                      "sudo ufw allow 22/tcp\nsudo ufw enable"}),
                    ("callout", {"style": "danger", "title": "Cuidado",
                                 "body": "<p>Permite SSH antes de activar el "
                                         "firewall para no bloquearte.</p>"}),
                ],
            )
            idx.add_child(instance=art)
            art.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Artículo de ejemplo creado."))

        home.refresh_from_db()
        idx.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            "Listo. Home: %s | Índice: %s" % (home.url or "/", idx.url or "/blog/")))
