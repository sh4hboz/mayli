from modeltranslation.translator import register, TranslationOptions

from .models import Zone


@register(Zone)
class ZoneTranslation(TranslationOptions):
    fields = ('name',)
