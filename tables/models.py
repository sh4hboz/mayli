import uuid
from django.db import models
from core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class TableStatus(models.TextChoices):
    ACTIVE = 'active', _('Faol')
    INACTIVE = 'inactive', _('Nofaol')


class Table(TimeStampedModel):
    number = models.IntegerField(_("Stol raqami"), unique=True)
    capacity = models.IntegerField(_("Sig'imi"), default=4)
    is_occupied = models.BooleanField(_("Band"), default=False)
    qr_token = models.UUIDField(_("QR Token"), default=uuid.uuid4, unique=True, editable=False)
    zone = models.CharField(
        _("Zona"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Masalan: Zal, Terrasa, VIP")
    )
    status = models.CharField(
        _("Holati"),
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.ACTIVE
    )

    class Meta:
        verbose_name = _("Stol")
        verbose_name_plural = _("Stollar")
        ordering = ['number']

    def __str__(self):
        return f"{self.number}-stol"


class TableSession(TimeStampedModel):
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Stol")
    )
    waiter = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        verbose_name=_("Ofitsiant")
    )
    is_closed = models.BooleanField(_("Yopilgan"), default=False)

    class Meta:
        verbose_name = _("Stol sessiyasi")
        verbose_name_plural = _("Stol sessiyalari")

    def __str__(self):
        return f"Sessiya: {self.table} - {'Yopilgan' if self.is_closed else 'Ochiq'}"
