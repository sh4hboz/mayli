from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import (SiteSettings, News, Promotion, GalleryItem,
                     TeamMember, Testimonial, Vacancy, JobApplication, ContactMessage, Feature, StatItem)


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationAdmin):
    fieldsets = (
        ('Asosiy', {'fields': ('name', 'tagline', 'logo', 'logo_dark', 'favicon', 'hero_bg_image')}),
        ('Kontakt', {'fields': ('phone_main', 'phone_secondary', 'email')}),
        ('Manzil', {'fields': ('address', 'city', 'working_hours', 'latitude', 'longitude', 'map_embed_code')}),
        ('Ijtimoiy tarmoqlar', {
            'fields': (
                ('instagram_url', 'instagram_active'),
                'instagram_title',
                ('telegram_channel_url', 'telegram_channel_active'),
                'telegram_channel_title',
                ('telegram_bot_url', 'telegram_bot_active'),
                'telegram_bot_title',
            )
        }),
        ('Biz haqimizda', {'fields': ('about_text', 'about_image')}),
        ('SEO & Tahlil', {'fields': ('google_verify', 'yandex_verify', 'google_analytics_id')}),
    )


@admin.register(News)
class NewsAdmin(TranslationAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Promotion)
class PromotionAdmin(TranslationAdmin):
    list_display = ('title', 'valid_until', 'is_active')
    list_editable = ('is_active',)


@admin.register(GalleryItem)
class GalleryItemAdmin(TranslationAdmin):
    list_display = ('caption', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationAdmin):
    list_display = ('name', 'position', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Testimonial)
class TestimonialAdmin(TranslationAdmin):
    list_display = ('author', 'rating', 'is_active')
    list_editable = ('is_active',)


@admin.register(Vacancy)
class VacancyAdmin(TranslationAdmin):
    list_display = ('title', 'salary', 'is_active', 'created_at')
    list_editable = ('is_active',)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'vacancy', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'is_read', 'created_at')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)


@admin.register(Feature)
class FeatureAdmin(TranslationAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(StatItem)
class StatItemAdmin(TranslationAdmin):
    list_display = ('value', 'label', 'placement', 'order', 'is_active')
    list_editable = ('order', 'is_active')
