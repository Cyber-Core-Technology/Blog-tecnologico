"""
Bloques reutilizables de StreamField para el contenido del blog.

El bloque de código resalta la sintaxis en el servidor con Pygments
(cero JavaScript en el cliente).
"""
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock

# Lenguajes ofrecidos en el selector del bloque de código.
LANGUAGE_CHOICES = (
    ("text", "Texto plano"),
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("typescript", "TypeScript"),
    ("bash", "Bash / Shell"),
    ("go", "Go"),
    ("rust", "Rust"),
    ("c", "C"),
    ("cpp", "C++"),
    ("java", "Java"),
    ("php", "PHP"),
    ("ruby", "Ruby"),
    ("sql", "SQL"),
    ("html", "HTML"),
    ("css", "CSS"),
    ("json", "JSON"),
    ("yaml", "YAML"),
    ("dockerfile", "Dockerfile"),
    ("nginx", "Nginx"),
    ("diff", "Diff"),
)


class CodeBlock(blocks.StructBlock):
    """Bloque de código con resaltado server-side (Pygments)."""

    language = blocks.ChoiceBlock(
        choices=LANGUAGE_CHOICES, default="python", label="Lenguaje"
    )
    caption = blocks.CharBlock(required=False, label="Título / nombre de archivo")
    code = blocks.TextBlock(label="Código")

    class Meta:
        icon = "code"
        label = "Bloque de código"
        template = "blocks/code_block.html"

    def render_basic(self, value, context=None):
        # No se usa: el render real ocurre en get_context + template.
        return super().render_basic(value, context)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        language = value.get("language") or "text"
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            lexer = get_lexer_by_name("text")
        formatter = HtmlFormatter(
            cssclass="codehilite",
            wrapcode=True,
        )
        context["highlighted"] = mark_safe(  # noqa: S308 — salida de Pygments es segura
            highlight(value.get("code") or "", lexer, formatter)
        )
        return context


class CalloutBlock(blocks.StructBlock):
    """Aviso/callout destacado (info, warning, danger, success)."""

    style = blocks.ChoiceBlock(
        choices=[
            ("info", "Información"),
            ("success", "Éxito"),
            ("warning", "Advertencia"),
            ("danger", "Peligro / Seguridad"),
        ],
        default="info",
        label="Estilo",
    )
    title = blocks.CharBlock(required=False, label="Título")
    body = blocks.RichTextBlock(
        features=["bold", "italic", "link", "code"], label="Contenido"
    )

    class Meta:
        icon = "warning"
        label = "Callout"
        template = "blocks/callout_block.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(label="Imagen")
    caption = blocks.CharBlock(required=False, label="Pie de foto")
    alt_text = blocks.CharBlock(required=False, label="Texto alternativo (accesibilidad)")

    class Meta:
        icon = "image"
        label = "Imagen"
        template = "blocks/image_block.html"


class QuoteBlock(blocks.StructBlock):
    quote = blocks.TextBlock(label="Cita")
    attribution = blocks.CharBlock(required=False, label="Autor de la cita")

    class Meta:
        icon = "openquote"
        label = "Cita"
        template = "blocks/quote_block.html"


class BodyStreamBlock(blocks.StreamBlock):
    """Cuerpo del artículo: bloques modulares reordenables."""

    heading = blocks.CharBlock(
        form_classname="title", icon="title", label="Encabezado"
    )
    paragraph = blocks.RichTextBlock(
        features=[
            "bold", "italic", "link", "ol", "ul", "hr",
            "blockquote", "code", "document-link",
        ],
        icon="pilcrow",
        label="Párrafo",
    )
    code = CodeBlock()
    callout = CalloutBlock()
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock(icon="media", label="Embed (YouTube, gist, etc.)")
    table = blocks.RawHTMLBlock(
        icon="table", label="HTML/tabla (avanzado)", required=False
    )

    class Meta:
        block_counts = {}
