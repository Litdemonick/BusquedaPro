from django import template
import re
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()

HASHTAG_RE = re.compile(r'(?P<tag>#\w+)')
MENTION_RE = re.compile(r'(?P<at>@[A-Za-z0-9_\.\-]+)')

@register.filter
def linkify(text: str):
    if not text:
        return ''
    def link_tag(m):
        tag = m.group('tag')[1:]
        url = reverse('tag', args=[tag])
        return f'<a class="text-blue-600 hover:underline" href="{url}">#{tag}</a>'
    def link_mention(m):
        user = m.group('at')[1:]
        url = reverse('profile', args=[user])
        return f'<a class="text-blue-600 hover:underline" href="{url}">@{user}</a>'
    html = HASHTAG_RE.sub(link_tag, text)
    html = MENTION_RE.sub(link_mention, html)
    return mark_safe(html)

# NUEVO TEMPLATE TAG - Agrega esto al final
@register.filter
def get_tema_by_id(temas, tema_id):
    """Obtiene el nombre de un tema por su ID desde un queryset de temas"""
    try:
        tema_id = int(tema_id)
        for tema in temas:
            if tema.id == tema_id:
                return tema.nombre
    except (ValueError, TypeError):
        pass
    return "Desconocido"