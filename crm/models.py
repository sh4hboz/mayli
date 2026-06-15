"""
crm/models.py — Mijozlar bazasi (CRM).

Maqsad: mijozlarni doimiy ko'paytirish va marketing (SMS/email/Telegram).
Customer — mustaqil yozuv: xodim qo'lda qo'shishi mumkin (akkaunt shart emas);
agar mijozning tizimda akkaunti bo'lsa, `user` orqali ixtiyoriy bog'lanadi.
"""

from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class Gender(models.TextChoices):
    MALE = 'male', _('Erkak')
    FEMALE = 'female', _('Ayol')


class CustomerSource(models.TextChoices):
    WALK_IN = 'walk_in', _('Restoranda')
    WEBSITE = 'website', _('Veb-sayt')
    INSTAGRAM = 'instagram', _('Instagram')
    TELEGRAM = 'telegram', _('Telegram')
    REFERRAL = 'referral', _('Tavsiya (do\'st)')
    OTHER = 'other', _('Boshqa')


class Tag(TimeStampedModel):
    """Mijozlarni segmentlash uchun teg (masalan: VIP, doimiy, tug'ilgan kun)."""
    name = models.CharField(_('Teg nomi'), max_length=50, unique=True)
    color = models.CharField(
        _('Rang'), max_length=20, blank=True, default='secondary',
        help_text=_('Bootstrap rang nomi: primary, success, warning, danger, info, secondary'),
    )

    class Meta:
        verbose_name = _('Teg')
        verbose_name_plural = _('Teglar')
        ordering = ['name']

    def __str__(self):
        return self.name


class Customer(TimeStampedModel):
    # Asosiy ma'lumotlar
    first_name = models.CharField(_('Ism'), max_length=100)
    last_name = models.CharField(_('Familiya'), max_length=100, blank=True)
    phone = models.CharField(
        _('Telefon'), max_length=20, unique=True,
        help_text=_('+998 XX XXX-XX-XX'),
    )
    birth_date = models.DateField(_('Tug\'ilgan kun'), null=True, blank=True)
    gender = models.CharField(_('Jins'), max_length=10, choices=Gender.choices, blank=True)

    # Qo'shimcha aloqa kanallari (kelajak marketing uchun)
    email = models.EmailField(_('Email'), blank=True)
    telegram_username = models.CharField(_('Telegram username'), max_length=64, blank=True)
    telegram_user_id = models.CharField(_('Telegram user ID'), max_length=32, blank=True)

    # CRM / marketing
    source = models.CharField(
        _('Manba'), max_length=20, choices=CustomerSource.choices,
        default=CustomerSource.WALK_IN,
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name='customers', verbose_name=_('Teglar'),
    )
    sms_consent = models.BooleanField(_('SMS rozilik'), default=True)
    email_consent = models.BooleanField(_('Email rozilik'), default=True)
    telegram_consent = models.BooleanField(_('Telegram rozilik'), default=True)
    notes = models.TextField(_('Izoh'), blank=True)
    is_active = models.BooleanField(_('Faol'), default=True)

    # Bog'lanishlar
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='customer_profile',
        verbose_name=_('Foydalanuvchi akkaunti'),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_customers',
        verbose_name=_('Kim qo\'shgan'),
    )

    class Meta:
        verbose_name = _('Mijoz')
        verbose_name_plural = _('Mijozlar')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.full_name or self.phone

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class CampaignChannel(models.TextChoices):
    SMS = 'sms', _('SMS')
    EMAIL = 'email', _('Email')
    TELEGRAM = 'telegram', _('Telegram')


class CampaignStatus(models.TextChoices):
    DRAFT = 'draft', _('Qoralama')
    SCHEDULED = 'scheduled', _('Rejalashtirylgan')
    SENT = 'sent', _('Jo\'natilgan')


class Campaign(TimeStampedModel):
    name = models.CharField(_('Kampaniya nomi'), max_length=200)
    description = models.TextField(_('Tavsif'), blank=True)
    channel = models.CharField(_('Kanal'), max_length=20, choices=CampaignChannel.choices)
    template = models.TextField(
        _('Shablon'),
        help_text=_('{{first_name}}, {{full_name}}, {{phone}} ishlatish mumkin'),
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name='campaigns', verbose_name=_('Teglar (filtr)'),
        help_text=_('Bo\'sh bo\'lsa — barcha mijozlarga'),
    )
    status = models.CharField(
        _('Holat'), max_length=20, choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
    )
    scheduled_at = models.DateTimeField(_('Jo\'natish vaqti'), null=True, blank=True)
    sent_count = models.IntegerField(_('Yuborilan soni'), default=0)
    failed_count = models.IntegerField(_('Muvaffaqiyatsiz soni'), default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_campaigns',
        verbose_name=_('Kim yaratgan'),
    )

    class Meta:
        verbose_name = _('Kampaniya')
        verbose_name_plural = _('Kampaniyalar')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


class CampaignLogStatus(models.TextChoices):
    PENDING = 'pending', _('Kutayotgan')
    SENT = 'sent', _('Jo\'natilgan')
    FAILED = 'failed', _('Muvaffaqiyatsiz')


class CampaignLog(TimeStampedModel):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='logs',
        verbose_name=_('Kampaniya'),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='campaign_logs',
        verbose_name=_('Mijoz'),
    )
    status = models.CharField(
        _('Holat'), max_length=20, choices=CampaignLogStatus.choices,
        default=CampaignLogStatus.PENDING,
    )
    message_text = models.TextField(_('Xabar'), blank=True)
    error_message = models.TextField(_('Xato xabari'), blank=True)
    sent_at = models.DateTimeField(_('Jo\'natilgan'), null=True, blank=True)

    class Meta:
        verbose_name = _('Kampaniya logi')
        verbose_name_plural = _('Kampaniya loglari')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['customer']),
        ]
        unique_together = [('campaign', 'customer')]

    def __str__(self):
        return f"{self.campaign.name} → {self.customer.full_name}"
