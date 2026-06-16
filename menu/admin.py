from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Category, Dish


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Dish)
class DishAdmin(TranslationAdmin):
    list_display = ('name', 'category_names', 'price', 'is_available', 'is_active', 'created_at')
    list_filter = ('categories', 'is_available', 'is_active')
    list_editable = ('price', 'is_available', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('categories',)

    @admin.display(description='Kategoriyalar')
    def category_names(self, obj):
        return ", ".join(c.name for c in obj.categories.all()) or "—"
