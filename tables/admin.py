from django.contrib import admin
from .models import Table, TableSession


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'is_occupied', 'zone', 'status', 'qr_token', 'created_at')
    list_filter = ('is_occupied', 'zone', 'status')
    list_editable = ('is_occupied', 'status', 'zone')
    search_fields = ('number', 'zone')
    readonly_fields = ('qr_token', 'created_at', 'updated_at')


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ('table', 'waiter', 'is_closed', 'created_at', 'updated_at')
    list_filter = ('is_closed', 'waiter')
    list_editable = ('is_closed',)
    search_fields = ('table__number', 'waiter__phone', 'waiter__full_name')
