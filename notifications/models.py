"""
notifications/models.py

BOSQICH 0.7 — Bildirishnomalar modeli skeleti.

DeviceToken: mobil push uchun (kelajak — BOSQICH 6).
TelegramSettings: Telegram bot sozlamalari (singleton).
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel


class TelegramSettings(models.Model):
    """Telegram bot sozlamalari singleton modeli."""
    bot_token = models.CharField(_('Bot Token'), max_length=200, blank=True)
    admin_chat_id = models.CharField(
        _('Admin Guruh/Chat ID'), max_length=50, blank=True,
        help_text=_('Bildirishnomalar yuboriluvchi guruh yoki chat ID'),
    )
    forum_group_id = models.CharField(
        _('Forum Guruh ID'), max_length=50, blank=True,
        help_text=_('Chat ko\'prigi uchun forum-topic guruh ID'),
    )
    webhook_secret = models.CharField(
        _('Webhook Secret'), max_length=200, blank=True
    )
    is_active = models.BooleanField(_('Faol'), default=True)

    class Meta:
        verbose_name = _('Telegram sozlamalari')
        verbose_name_plural = _('Telegram sozlamalari')

    def __str__(self):
        return 'Telegram Bot Sozlamalari'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class DeviceToken(TimeStampedModel):
    """Mobil push bildirishnoma tokeni (FCM — kelajak BOSQICH 6)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name=_('Foydalanuvchi'),
    )
    token = models.CharField(_('Token'), max_length=500, unique=True)
    platform = models.CharField(
        _('Platforma'), max_length=20,
        choices=[('android', 'Android'), ('ios', 'iOS')],
        default='android',
    )
    is_active = models.BooleanField(_('Faol'), default=True)

    class Meta:
        verbose_name = _('Qurilma tokeni')
        verbose_name_plural = _('Qurilma tokenlari')

    def __str__(self):
        return f"{self.user} ({self.platform})"
