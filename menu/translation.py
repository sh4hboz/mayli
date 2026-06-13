from modeltranslation.translator import register, TranslationOptions
from .models import Category, Dish


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Dish)
class DishTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)
