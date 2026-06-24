from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import BookingSettings, OtpCode, Reservation, Table, Zone


@admin.register(Zone)
class ZoneAdmin(TranslationAdmin):
    list_display = ('name', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'zone', 'capacity', 'shape', 'status', 'is_active')
    list_filter = ('zone', 'shape', 'status', 'is_active')
    list_editable = ('capacity', 'status', 'is_active')
    search_fields = ('number',)
    fieldsets = (
        (None, {'fields': ('zone', 'number', 'capacity', 'shape', 'status', 'is_active')}),
        ('Sxema joylashuvi (2D)', {'fields': ('pos_x', 'pos_y', 'width', 'height')}),
        ('3D (ixtiyoriy)', {'fields': ('model_object_id',)}),
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_phone', 'table', 'date', 'time',
                    'guests', 'status', 'otp_verified', 'created_at')
    list_filter = ('status', 'date', 'source', 'table__zone')
    search_fields = ('customer_name', 'customer_phone')
    date_hierarchy = 'date'
    autocomplete_fields = ('table',)


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    list_display = ('conflict_window', 'open_time', 'close_time', 'advance_days', 'is_open')


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'is_verified', 'consumed', 'attempts', 'expires_at', 'created_at')
    list_filter = ('is_verified', 'consumed')
    search_fields = ('phone',)
