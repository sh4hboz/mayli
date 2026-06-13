from django import template
from django.urls import translate_url as _translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def lang_url(context, lang_code):
    """
    Joriy sahifaning URL'ini ko'rsatilgan tildagi variantini qaytaradi.
    i18n_patterns + prefix_default_language=False bilan to'g'ri ishlaydi.

    Misol:
      /ru/menu/  → {% lang_url 'uz' %} → /menu/
      /menu/     → {% lang_url 'ru' %} → /ru/menu/
    """
    request = context.get('request')
    if not request:
        return '/'
    try:
        return _translate_url(request.path, lang_code)
    except Exception:
        return '/'
