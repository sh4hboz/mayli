from django.contrib import admin

from .models import (
    Campaign, CampaignLog, Customer, Tag,
    LoyaltySettings, LoyaltyTransaction,
)


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


class CampaignLogInline(admin.TabularInline):
    model = CampaignLog
    extra = 0
    readonly_fields = ('customer', 'status', 'message_text', 'error_message', 'sent_at', 'created_at')
    can_delete = False


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel', 'status', 'sent_count', 'failed_count', 'created_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('tags',)
    readonly_fields = ('sent_count', 'failed_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'description', 'channel', 'created_by')
        }),
        ('Shablon va filtr', {
            'fields': ('template', 'tags')
        }),
        ('Holat', {
            'fields': ('status', 'scheduled_at')
        }),
        ('Statistika', {
            'fields': ('sent_count', 'failed_count', 'created_at', 'updated_at')
        }),
    )
    inlines = (CampaignLogInline,)


@admin.register(CampaignLog)
class CampaignLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'customer', 'status', 'sent_at', 'created_at')
    list_filter = ('campaign', 'status', 'created_at')
    search_fields = ('campaign__name', 'customer__first_name', 'customer__last_name', 'customer__phone')
    readonly_fields = ('campaign', 'customer', 'status', 'message_text', 'error_message', 'sent_at', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(admin.ModelAdmin):
    list_display = ('is_enabled', 'earn_percent', 'som_per_point', 'silver_threshold', 'gold_threshold')


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'kind', 'points', 'balance_after', 'order', 'created_at')
    list_filter = ('kind', 'created_at')
    search_fields = ('customer__first_name', 'customer__last_name', 'customer__phone', 'note')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
