"""
orders/models.py — Menyu'dan buyurtma berish tizimi modellari.

Oqim: mijoz savatga taom yig'adi → telefon OTP bilan tasdiqlanadi → buyurtma
yaratiladi (Telegram guruhga + dashboard'ga). Manzil/yetkazib berish YO'Q.
Mijoz holatni ko'rmaydi — manager qo'ng'iroq qilib qabul/rad qiladi (sabab bilan).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class OrderSettings(models.Model):
    """Buyurtma tizimi sozlamalari (singleton, pk=1)."""
    is_open = models.BooleanField(
        _('Buyurtma qabul qilinmoqda'), default=True,
        help_text=_("O'chirilsa — sayt buyurtma berishni vaqtincha to'xtatadi."),
    )
    min_order_amount = models.DecimalField(
        _('Minimum buyurtma summasi'), max_digits=12, decimal_places=2,
        default=Decimal('0'),
        help_text=_("Shu summadan kam buyurtma qabul qilinmaydi (0 — cheklov yo'q)."),
    )

    class Meta:
        verbose_name = _('Buyurtma sozlamalari')
        verbose_name_plural = _('Buyurtma sozlamalari')

    def __str__(self):
        return 'Buyurtma sozlamalari'

    @classmethod
    def get(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class OrderStatus(models.TextChoices):
    NEW = 'new', _('Yangi')
    ACCEPTED = 'accepted', _('Qabul qilindi')
    COMPLETED = 'completed', _('Yetkazildi')
    REJECTED = 'rejected', _('Bekor qilindi')


# Mijoz uchun "faol" (jarayonda) hisoblanadigan holatlar.
ACTIVE_ORDER_STATUSES = (OrderStatus.NEW, OrderStatus.ACCEPTED)


class PaymentMethod(models.TextChoices):
    CASH = 'cash', _('Naqd')
    CARD = 'card', _('Karta')


class Order(TimeStampedModel):
    """Bitta buyurtma. Mijoz login'siz (ism + telefon, OTP tasdig'i)."""
    customer_name = models.CharField(_('Ism'), max_length=120)
    phone = models.CharField(_('Telefon'), max_length=20, db_index=True)
    comment = models.TextField(_('Izoh'), blank=True)
    total_amount = models.DecimalField(
        _('Jami summa'), max_digits=12, decimal_places=2, default=Decimal('0'),
        help_text=_('Buyurtma vaqtidagi jami summa (DB narxlaridan hisoblangan).'),
    )
    payment_method = models.CharField(
        _('To\'lov usuli'), max_length=10, choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text=_('Mijoz tanlovi (ma\'lumot uchun — manager telefonda aniqlashtiradi).'),
    )
    status = models.CharField(
        _('Holat'), max_length=10, choices=OrderStatus.choices,
        default=OrderStatus.NEW, db_index=True,
    )
    reject_reason = models.TextField(
        _('Rad etish sababi'), blank=True,
        help_text=_('Buyurtma rad etilsa — sababi (manager kiritadi).'),
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='handled_orders', verbose_name=_('Kim ko\'rib chiqdi'),
    )
    customer = models.ForeignKey(
        'crm.Customer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', verbose_name=_('Mijoz (CRM)'),
    )
    is_read = models.BooleanField(_('O\'qildi'), default=False)
    accepted_at = models.DateTimeField(_('Qabul qilingan vaqt'), null=True, blank=True)
    rejected_at = models.DateTimeField(_('Rad etilgan vaqt'), null=True, blank=True)
    source = models.CharField(_('Manba'), max_length=20, default='web')

    class Meta:
        verbose_name = _('Buyurtma')
        verbose_name_plural = _('Buyurtmalar')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f'#{self.pk} — {self.customer_name} — {self.total_amount}'

    @property
    def is_active(self):
        return self.status in ACTIVE_ORDER_STATUSES


class OrderItem(models.Model):
    """Buyurtmadagi bitta satr. Nom/narx — buyurtma vaqtidagi snapshot."""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items',
        verbose_name=_('Buyurtma'),
    )
    dish = models.ForeignKey(
        'menu.Dish', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name=_('Taom'),
    )
    dish_name = models.CharField(_('Taom nomi'), max_length=120)
    unit_price = models.DecimalField(_('Narxi'), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Soni'), default=1)

    class Meta:
        verbose_name = _('Buyurtma satri')
        verbose_name_plural = _('Buyurtma satrlari')

    def __str__(self):
        return f'{self.dish_name} × {self.quantity}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class OtpCode(TimeStampedModel):
    """Telefon tasdig'i uchun bir martalik kod (SMS — TextUp orqali).

    Buyurtma yaratishdan oldin telefon tasdiqlanadi. Kod ishlatilgach `consumed=True`.
    `purpose` — kelajakda boshqa oqimlar (masalan bron) ham shu modeldan foydalanishi uchun.
    """
    phone = models.CharField(_('Telefon'), max_length=20, db_index=True)
    code = models.CharField(_('Kod'), max_length=6)
    purpose = models.CharField(_('Maqsad'), max_length=20, default='order')
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
