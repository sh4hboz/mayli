"""
reservations/models.py — Joy band qilish (bron) tizimi modellari.

2 qatlam (MAYLI_BRON_REJA.md):
  1) Backend — Zone / Table / Reservation + holat mantig'i (shu fayl).
  2) Vizualizatsiya (2D SVG / 3D) — keyingi bosqichlar, backend o'zgarmaydi.

Holat modeli: belgilangan slot YO'Q — stol holatini MANAGER boshqaradi.
`conflict_window` faqat bir stolni bir vaqtda ikki kishi bron qilmasligi uchun
yumshoq oraliq (BookingSettings'da, default 120 daqiqa).
"""

from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class Zone(TimeStampedModel):
    """Restoran bo'limi/qavati: Hovli-ko'cha, Ayvon, Ichki 1-qavat va h.k."""
    name = models.CharField(_('Nomi'), max_length=100)
    order = models.PositiveIntegerField(_('Tartib'), default=0)
    bg_image = models.ImageField(
        _('Sxema fon rasmi'), upload_to='zones/', blank=True, null=True,
        help_text=_('2D sxema uchun ixtiyoriy fon (zona plani).'),
    )
    is_active = models.BooleanField(_('Faol'), default=True)

    class Meta:
        verbose_name = _('Zona')
        verbose_name_plural = _('Zonalar')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class TableShape(models.TextChoices):
    SQUARE = 'square', _('Kvadrat')
    ROUND = 'round', _('Dumaloq')
    RECT = 'rect', _('To\'rtburchak')


class TableStatus(models.TextChoices):
    FREE = 'free', _('Bo\'sh')
    OCCUPIED = 'occupied', _('Band')


class Table(TimeStampedModel):
    """Stol — sxemadagi joylashuvi (pos_x/pos_y) bilan. Holatni manager boshqaradi."""
    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name='tables',
        verbose_name=_('Zona'),
    )
    number = models.CharField(
        _('Stol raqami/nomi'), max_length=20,
        help_text=_('Masalan: 12, A1, VIP-3'),
    )
    capacity = models.PositiveIntegerField(_('Sig\'im (kishi)'), default=4)
    shape = models.CharField(
        _('Shakl'), max_length=10, choices=TableShape.choices,
        default=TableShape.SQUARE,
    )
    # Sxemadagi joylashuv (admin drag-drop bilan to'ldiradi — BOSQICH 3).
    pos_x = models.FloatField(_('X koordinata'), default=0)
    pos_y = models.FloatField(_('Y koordinata'), default=0)
    width = models.FloatField(_('Kenglik'), default=60)
    height = models.FloatField(_('Balandlik'), default=60)
    status = models.CharField(
        _('Holat'), max_length=10, choices=TableStatus.choices,
        default=TableStatus.FREE,
        help_text=_('Hozirgi jonli holat — manager boshqaradi.'),
    )
    is_active = models.BooleanField(_('Faol'), default=True)
    # 3D model obyekti bilan bog'lash uchun (BOSQICH 4). Bo'sh — 2D yetarli.
    model_object_id = models.CharField(
        _('3D model obyekt ID'), max_length=64, blank=True,
        help_text=_('glTF/GLB modeldagi shu stol obyektining nomi (bog\'lash uchun).'),
    )

    class Meta:
        verbose_name = _('Stol')
        verbose_name_plural = _('Stollar')
        ordering = ['zone__order', 'number']
        constraints = [
            models.UniqueConstraint(
                fields=['zone', 'number'], name='uniq_table_number_per_zone',
            ),
        ]

    def __str__(self):
        return f'{self.zone.name} — {self.number}'


class ReservationStatus(models.TextChoices):
    PENDING = 'pending', _('Kutilmoqda')
    CONFIRMED = 'confirmed', _('Tasdiqlangan')
    SEATED = 'seated', _('Joylashdi')
    COMPLETED = 'completed', _('Yakunlandi')
    CANCELLED = 'cancelled', _('Bekor qilindi')
    NO_SHOW = 'no_show', _('Kelmadi')


# Stolni "band" qiladigan (conflict beradigan) faol holatlar.
ACTIVE_RESERVATION_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.SEATED,
)


class ReservationSource(models.TextChoices):
    WEBSITE_2D = 'website_2d', _('Sayt (2D sxema)')
    WEBSITE_3D = 'website_3d', _('Sayt (3D)')
    PHONE = 'phone', _('Telefon')
    WALK_IN = 'walk_in', _('Restoranda')
    OTHER = 'other', _('Boshqa')


class Reservation(TimeStampedModel):
    """Bitta bron so'rovi. Mijoz login'siz (faqat ism+telefon, OTP tasdig'i)."""
    table = models.ForeignKey(
        Table, on_delete=models.PROTECT, related_name='reservations',
        verbose_name=_('Stol'),
    )
    customer_name = models.CharField(_('Ism'), max_length=120)
    customer_phone = models.CharField(_('Telefon'), max_length=20)
    date = models.DateField(_('Sana'))
    time = models.TimeField(_('Vaqt'))
    guests = models.PositiveIntegerField(_('Kishi soni'), default=1)
    status = models.CharField(
        _('Holat'), max_length=12, choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
    )
    note = models.TextField(_('Izoh'), blank=True)
    otp_verified = models.BooleanField(_('OTP tasdiqlangan'), default=False)
    source = models.CharField(
        _('Manba'), max_length=12, choices=ReservationSource.choices,
        default=ReservationSource.WEBSITE_2D,
    )

    class Meta:
        verbose_name = _('Bron')
        verbose_name_plural = _('Bronlar')
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['table', 'date']),
            models.Index(fields=['customer_phone']),
        ]

    def __str__(self):
        return f'{self.customer_name} — {self.table} — {self.date} {self.time}'

    @property
    def is_active(self):
        return self.status in ACTIVE_RESERVATION_STATUSES


class BookingSettings(models.Model):
    """Bron tizimi sozlamalari (singleton, pk=1)."""
    conflict_window = models.PositiveIntegerField(
        _('Ziddiyat oynasi (daqiqa)'), default=120,
        help_text=_('Bir stolga shu oraliq ichida ikkinchi bron qabul qilinmaydi.'),
    )
    open_time = models.TimeField(_('Bron qabul boshlanishi'), default='10:00')
    close_time = models.TimeField(_('Bron qabul tugashi'), default='23:00')
    advance_days = models.PositiveIntegerField(
        _('Oldindan necha kun'), default=30,
        help_text=_('Bugundan necha kun oldinga bron qilsa bo\'ladi.'),
    )
    is_open = models.BooleanField(
        _('Bron qabul qilinmoqda'), default=True,
        help_text=_('O\'chirilsa — sayt bron formasi vaqtincha yopiladi.'),
    )

    class Meta:
        verbose_name = _('Bron sozlamalari')
        verbose_name_plural = _('Bron sozlamalari')

    def __str__(self):
        return 'Bron sozlamalari'

    @classmethod
    def get(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class OtpCode(TimeStampedModel):
    """Telefon tasdig'i uchun bir martalik kod (SMS — TextUp orqali).

    Bron yaratishdan oldin telefon tasdiqlanadi. Kod ishlatilgach `consumed=True`.
    """
    phone = models.CharField(_('Telefon'), max_length=20, db_index=True)
    code = models.CharField(_('Kod'), max_length=6)
    is_verified = models.BooleanField(_('Tasdiqlandi'), default=False)
    consumed = models.BooleanField(_('Ishlatildi'), default=False)
    attempts = models.PositiveIntegerField(_('Urinishlar'), default=0)
    expires_at = models.DateTimeField(_('Amal qilish muddati'))

    class Meta:
        verbose_name = _('OTP kodi')
        verbose_name_plural = _('OTP kodlari')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', '-created_at']),
        ]

    def __str__(self):
        return f'{self.phone} — {self.code}'

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
