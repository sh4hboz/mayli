from django.contrib import admin
from .models import TelegramSettings, DeviceToken


@admin.register(TelegramSettings)
class TelegramSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Bot', {'fields': ('bot_token', 'webhook_secret', 'is_active')}),
        ('Guruhlar', {'fields': ('admin_chat_id', 'forum_group_id')}),
    )


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
