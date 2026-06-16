from django.contrib import admin
from .models import TelegramSettings, DeviceToken, ChatSession, ChatMessage


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


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ('direction', 'text', 'is_auto', 'delivered', 'created_at')
    readonly_fields = ('direction', 'text', 'is_auto', 'delivered', 'created_at')
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('visitor_id', 'lang', 'updated_at', 'created_at')
    search_fields = ('visitor_id',)
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'direction', 'is_auto', 'delivered', 'created_at')
    list_filter = ('direction', 'is_auto', 'delivered')
    search_fields = ('text', 'session__visitor_id')
