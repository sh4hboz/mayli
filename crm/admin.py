from django.contrib import admin

from .models import Customer, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'gender', 'source', 'is_active', 'created_at')
    list_filter = ('gender', 'source', 'is_active', 'sms_consent', 'tags')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
