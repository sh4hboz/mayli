"""
chat/models.py

BOSQICH 0.7 — Jonli chat modellari.

Arxitektura (master reja 3.6):
  - ChatConversation: har bir suhbat (visitor UUID / user FK)
  - ChatMessage:      har bir xabar (VISITOR / STAFF / BOT / SYSTEM)

Oqim:
  Mijoz yozadi → saqlanadi → dashboard WS push + Telegram topicga.
  Admin javob beradi (Telegram yoki dashboard) → saqlanadi → mijoz vidjetiga WS push.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel


class ConversationStatus(models.TextChoices):
    OPEN = 'open', _('Ochiq')
    PENDING = 'pending', _('Kutilmoqda')
    CLOSED = 'closed', _('Yopilgan')


class SenderType(models.TextChoices):
    VISITOR = 'visitor', _('Tashrif buyuruvchi')
    STAFF = 'staff', _('Xodim')
    BOT = 'bot', _('Bot')
    SYSTEM = 'system', _('Tizim')


class ViaChannel(models.TextChoices):
    WEB = 'web', _('Sayt')
    TELEGRAM = 'telegram', _('Telegram')
    DASHBOARD = 'dashboard', _('Dashboard')


class ChatConversation(TimeStampedModel):
    """
    Har bir suhbat sessiyasi.
    Anonim mijoz: visitor_id (UUID, localStorage'dan).
    Ro'yxatdan o'tgan: user FK.
    Telegram bilan: telegram_chat_id + telegram_topic_id.
    """
    visitor_id = models.UUIDField(
        _('Visitor UUID'),
        default=uuid.uuid4,
        db_index=True,
        help_text=_('Anonim mijoz identifikatori (localStorage\'dan)'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_conversations',
        verbose_name=_('Foydalanuvchi (ro\'yxatdan o\'tgan bo\'lsa)'),
    )
    visitor_name = models.CharField(_('Ismi'), max_length=100, blank=True)
    visitor_phone = models.CharField(_('Telefon'), max_length=20, blank=True)
    language = models.CharField(
        _('Til'), max_length=5, default='uz',
        choices=[('uz', 'O\'zbek'), ('ru', 'Русский'), ('en', 'English')],
    )
    status = models.CharField(
        _('Holat'), max_length=20,
        choices=ConversationStatus.choices,
        default=ConversationStatus.OPEN,
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_chats',
        verbose_name=_('Biriktirilgan xodim'),
    )
    # Telegram mapping (master reja 3.6 — forum-topic guruh)
    telegram_chat_id = models.BigIntegerField(
        _('Telegram Chat ID'), null=True, blank=True
    )
    telegram_topic_id = models.IntegerField(
        _('Telegram Topic ID'), null=True, blank=True,
        help_text=_('Forum-topic ID — har suhbat alohida topic'),
    )
    last_message_at = models.DateTimeField(
        _('Oxirgi xabar vaqti'), null=True, blank=True
    )

    class Meta:
        verbose_name = _('Suhbat')
        verbose_name_plural = _('Suhbatlar')
        ordering = ['-last_message_at', '-created_at']

    def __str__(self):
        name = self.visitor_name or str(self.visitor_id)[:8]
        return f"Suhbat #{self.pk} — {name} ({self.get_status_display()})"

    @property
    def display_name(self):
        if self.visitor_name:
            return self.visitor_name
        if self.user:
            return self.user.get_full_name() or self.user.username
        return f"Mehmon-{str(self.visitor_id)[:6]}"

    def get_channel_group_name(self):
        """WebSocket guruh nomi (ChatConsumer uchun)."""
        return f"chat_{self.visitor_id}"


class ChatMessage(TimeStampedModel):
    """Suhbat xabari."""
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Suhbat'),
    )
    sender_type = models.CharField(
        _('Yuboruvchi turi'), max_length=10,
        choices=SenderType.choices,
        default=SenderType.VISITOR,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_chat_messages',
        verbose_name=_('Yuboruvchi (xodim bo\'lsa)'),
    )
    via = models.CharField(
        _('Kanal'), max_length=20,
        choices=ViaChannel.choices,
        default=ViaChannel.WEB,
    )
    text = models.TextField(_('Matn'))
    is_read = models.BooleanField(_('O\'qildi'), default=False, db_index=True)

    class Meta:
        verbose_name = _('Xabar')
        verbose_name_plural = _('Xabarlar')
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_sender_type_display()}] {self.text[:60]}"
