"""
crm/models.py — Mijozlar bazasi (CRM).

Maqsad: mijozlarni doimiy ko'paytirish va marketing (SMS/email/Telegram).
Customer — mustaqil yozuv: xodim qo'lda qo'shishi mumkin (akkaunt shart emas);
agar mijozning tizimda akkaunti bo'lsa, `user` orqali ixtiyoriy bog'lanadi.
"""

from datetime import date
from decimal import Decimal

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
    birthday_sms_sent_year = models.IntegerField(
        _('Tug\'ilgan kun SMS yuborilgan yil'), null=True, blank=True,
        help_text=_('Bir yilda ikki marta tabriklamaslik uchun: oxirgi tabrik yuborilgan yil.'),
    )
    notes = models.TextField(_('Izoh'), blank=True)
    is_active = models.BooleanField(_('Faol'), default=True)

    # Sodiqlik dasturi (loyalty)
    loyalty_points = models.IntegerField(
        _('Joriy ballar'), default=0,
        help_text=_('Mavjud (sarflanmagan) ball balansi.'),
    )
    lifetime_points = models.IntegerField(
        _('Umrlik ballar'), default=0,
        help_text=_('Jami to\'plangan ball (daraja shu bo\'yicha hisoblanadi; sarflasa kamaymaydi).'),
    )

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

    @property
    def loyalty_tier(self):
        """Mijoz darajasi (umrlik ball bo'yicha) — (kod, nom)."""
        return LoyaltySettings.get().tier_for(self.lifetime_points)


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
    sms_template_id = models.CharField(
        _('SMS shablon ID (TextUp)'), max_length=64, blank=True,
        help_text=_('Faqat SMS uchun: TextUp kabinetida tasdiqlangan shablonning templateId\'si. '
                    'Bo\'sh bo\'lsa, matn TextUp moderatsiyasidan o\'tmasa rad etilishi mumkin.'),
    )
    send_to_all_customers = models.BooleanField(
        _('Barcha mijozlarga'), default=False,
        help_text=_('Belgilansa — barcha faol, rozilik bergan mijozlarga yuboriladi (guruh tanlovi e\'tiborsiz qoladi).'),
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name='campaigns', verbose_name=_('Guruhlar (teglar)'),
        help_text=_('Tanlangan guruh(lar)dagi mijozlarga yuboriladi.'),
    )
    recipients_raw = models.TextField(
        _('Qo\'lda raqamlar'), blank=True,
        help_text=_('Har qatorda yoki vergul bilan telefon raqamlar. Guruh/barcha mijozlar bilan '
                    'birga ishlatilsa — bu raqamlar ham qo\'shiladi (takrorlanadiganlari chiqarib tashlanadi).'),
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


# ── Sodiqlik dasturi (loyalty) ──────────────────────────────────────────────

class LoyaltyTier(models.TextChoices):
    BRONZE = 'bronze', _('Bronza')
    SILVER = 'silver', _('Kumush')
    GOLD = 'gold', _('Oltin')


class LoyaltySettings(models.Model):
    """Sodiqlik dasturi sozlamalari (singleton, pk=1)."""
    is_enabled = models.BooleanField(
        _('Sodiqlik dasturi yoqilgan'), default=True,
        help_text=_("O'chirilsa — buyurtmalardan ball berilmaydi."),
    )
    earn_percent = models.DecimalField(
        _('Ball foizi (%)'), max_digits=5, decimal_places=2, default=Decimal('5'),
        help_text=_('Yetkazilgan buyurtma summasining shu foizi ball sifatida beriladi.'),
    )
    som_per_point = models.DecimalField(
        _("1 ball qiymati (so'm)"), max_digits=8, decimal_places=2, default=Decimal('1'),
        help_text=_('Ball chegirmaga aylantirilganda: 1 ball necha so\'m (kelajakda checkout uchun).'),
    )
    silver_threshold = models.IntegerField(
        _('Kumush daraja (umrlik ball)'), default=50000,
        help_text=_('Shu umrlik balldan boshlab — Kumush daraja.'),
    )
    gold_threshold = models.IntegerField(
        _('Oltin daraja (umrlik ball)'), default=200000,
        help_text=_('Shu umrlik balldan boshlab — Oltin daraja.'),
    )

    class Meta:
        verbose_name = _('Sodiqlik sozlamalari')
        verbose_name_plural = _('Sodiqlik sozlamalari')

    def __str__(self):
        return 'Sodiqlik sozlamalari'

    @classmethod
    def get(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def tier_for(self, lifetime_points):
        """Umrlik ball bo'yicha daraja — (kod, nom)."""
        if lifetime_points >= self.gold_threshold:
            return (LoyaltyTier.GOLD, LoyaltyTier.GOLD.label)
        if lifetime_points >= self.silver_threshold:
            return (LoyaltyTier.SILVER, LoyaltyTier.SILVER.label)
        return (LoyaltyTier.BRONZE, LoyaltyTier.BRONZE.label)

    def points_for_amount(self, amount):
        """Buyurtma summasidan beriladigan ball (butun son)."""
        return int((Decimal(amount) * self.earn_percent) / Decimal('100'))


class LoyaltyKind(models.TextChoices):
    EARN = 'earn', _('Ball to\'plandi')
    REDEEM = 'redeem', _('Ball sarflandi')
    ADJUST = 'adjust', _('Qo\'lda tuzatish')


class LoyaltyTransaction(TimeStampedModel):
    """Ball harakatlari jurnali (to'plash / sarflash / qo'lda tuzatish)."""
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='loyalty_transactions',
        verbose_name=_('Mijoz'),
    )
    order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='loyalty_transactions', verbose_name=_('Buyurtma'),
    )
    kind = models.CharField(_('Turi'), max_length=10, choices=LoyaltyKind.choices)
    points = models.IntegerField(
        _('Ball'), help_text=_('Musbat — qo\'shildi, manfiy — ayrildi.'),
    )
    balance_after = models.IntegerField(_('Keyingi balans'), default=0)
    note = models.CharField(_('Izoh'), max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='loyalty_transactions', verbose_name=_('Kim'),
    )

    class Meta:
        verbose_name = _('Ball harakati')
        verbose_name_plural = _('Ball harakatlari')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"{self.customer} — {self.points:+d} ({self.get_kind_display()})"
