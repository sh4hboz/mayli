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
    list_display = ('name', 'category', 'price', 'is_available', 'prep_time', 'created_at')
    list_filter = ('category', 'is_available')
    list_editable = ('price', 'is_available', 'prep_time')
    search_fields = ('name', 'description')
