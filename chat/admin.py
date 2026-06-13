from django.contrib import admin
from .models import ChatConversation, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender_type', 'sender', 'via', 'text', 'is_read', 'created_at')
    can_delete = False
    max_num = 0


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'display_name', 'language', 'status', 'assigned_to', 'last_message_at')
    list_filter = ('status', 'language')
    search_fields = ('visitor_name', 'visitor_phone', 'visitor_id')
    readonly_fields = ('visitor_id', 'created_at', 'updated_at', 'last_message_at',
                       'telegram_chat_id', 'telegram_topic_id')
    inlines = [ChatMessageInline]
    list_editable = ('status', 'assigned_to')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'conversation', 'sender_type', 'via', 'text_short', 'is_read', 'created_at')
    list_filter = ('sender_type', 'via', 'is_read')
    readonly_fields = ('created_at',)

    def text_short(self, obj):
        return obj.text[:60]
    text_short.short_description = 'Matn'
