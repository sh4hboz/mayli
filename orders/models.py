from django.db import models
from core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class OrderType(models.TextChoices):
    DINE_IN = 'dine_in', _('Stolda')
    DELIVERY = 'delivery', _('Yetkazib berish')
    TAKEAWAY = 'takeaway', _('Olib ketish')


class OrderStatus(models.TextChoices):
    PENDING = 'pending', _('Kutilmoqda')
    # Delivery/Takeaway uchun
    COOKING = 'cooking', _('Tayyorlanmoqda')
    DELIVERING = 'delivering', _("Yo'lda")
    # Dine-in (mavjud) uchun
    PREPARING = 'preparing', _('Tayyorlanmoqda (stol)')
    READY = 'ready', _('Tayyor')
    DELIVERED = 'delivered', _('Yetkazildi')
    # Umumiy
    COMPLETED = 'completed', _('Yakunlandi')
    CANCELLED = 'cancelled', _('Bekor qilindi')


class Order(TimeStampedModel):
    order_type = models.CharField(
        _("Buyurtma turi"),
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DINE_IN
    )
    table = models.ForeignKey(
        'tables.Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Stol")
    )
    customer = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name=_("Mijoz")
    )
    waiter = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waiter_orders',
        verbose_name=_("Ofitsiant")
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(_("Jami narx"), max_digits=12, decimal_places=2, default=0.00)
    checkout_requested = models.BooleanField(_("Hisob so'ralgan"), default=False)

    # Delivery / Takeaway veb-buyurtma uchun
    customer_name = models.CharField(_("Mijoz ismi"), max_length=100, blank=True)
    customer_phone = models.CharField(_("Mijoz telefoni"), max_length=20, blank=True)
    delivery_address = models.CharField(_("Yetkazib berish manzili"), max_length=500, blank=True)
    delivery_lat = models.FloatField(_("Kenglik (lat)"), null=True, blank=True)
    delivery_lng = models.FloatField(_("Uzunlik (lng)"), null=True, blank=True)
    pickup_time = models.CharField(_("Olib ketish vaqti"), max_length=100, blank=True)
    notes = models.TextField(_("Izoh"), blank=True)
    marketing_consent = models.BooleanField(_("Marketingga rozilik"), default=False)

    # Kunlik tartib raqamlar (race-condition bilan yaratiladi)
    daily_id = models.PositiveIntegerField(
        _("Kunlik tartib #"), null=True, blank=True, db_index=True
    )
    type_daily_id = models.PositiveIntegerField(
        _("Tur tartib #"), null=True, blank=True,
        help_text=_("Faqat delivery buyurtmalar uchun")
    )

    # Kuryer
    delivery_courier = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courier_orders',
        verbose_name=_("Kuryer"),
        limit_choices_to={'role': 'courier'},
    )

    # Vaqt muhrlari
    accepted_at = models.DateTimeField(_("Qabul vaqti"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Yo'lga chiqqan vaqt"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Yakunlangan vaqt"), null=True, blank=True)

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ['-created_at']

    def __str__(self):
        return f"Buyurtma #{self.id} ({self.get_order_type_display()}) - {self.get_status_display()}"

    def calculate_total(self):
        total_sum = sum(item.unit_price * item.qty for item in self.items.all())
        self.subtotal = total_sum
        self.total = total_sum
        self.save()


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Buyurtma")
    )
    dish = models.ForeignKey(
        'menu.Dish',
        on_delete=models.CASCADE,
        verbose_name=_("Taom")
    )
    qty = models.IntegerField(_("Soni"), default=1)
    unit_price = models.DecimalField(_("Birlik narxi"), max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _("Buyurtma mahsuloti")
        verbose_name_plural = _("Buyurtma mahsulotlari")

    def __str__(self):
        return f"{self.dish.name} x {self.qty}"


class WaiterCall(TimeStampedModel):
    class CallStatus(models.TextChoices):
        PENDING = 'pending', _('Kutilmoqda')
        RESOLVED = 'resolved', _('Bajarildi')

    table = models.ForeignKey(
        'tables.Table',
        on_delete=models.CASCADE,
        verbose_name=_("Stol")
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=CallStatus.choices,
        default=CallStatus.PENDING
    )

    class Meta:
        verbose_name = _("Ofitsiant chaqiruvi")
        verbose_name_plural = _("Ofitsiant chaqiruvlari")
        ordering = ['-created_at']

    def __str__(self):
        return f"Chaqiruv (Stol #{self.table.number}) - {self.get_status_display()}"
