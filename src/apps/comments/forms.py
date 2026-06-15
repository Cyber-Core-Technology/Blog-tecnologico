"""Formulario de comentarios con honeypot anti-spam."""
from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    # Campo trampa: los bots lo rellenan, los humanos no lo ven.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "tabindex": "-1", "aria-hidden": "true"}
        ),
        label="",
    )

    class Meta:
        model = Comment
        fields = ["author_name", "author_email", "body", "parent"]
        widgets = {
            "parent": forms.HiddenInput(),
            "author_name": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Tu nombre", "maxlength": 80}
            ),
            "author_email": forms.EmailInput(
                attrs={"class": "form-input", "placeholder": "tu@email.com"}
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Escribe tu comentario…",
                    "maxlength": 3000,
                }
            ),
        }

    def clean_website(self):
        # Si el honeypot trae datos, es spam.
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detectado.")
        return ""

    def clean_body(self):
        body = self.cleaned_data.get("body", "").strip()
        if len(body) < 2:
            raise forms.ValidationError("El comentario es demasiado corto.")
        return body
