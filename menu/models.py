from django.db import models
from django.utils.text import slugify
from core.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class Category(TimeStampedModel):
    name = models.CharField(_("Nomi"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Dish(TimeStampedModel):
    categories = models.ManyToManyField(
        Category,
        related_name='dishes',
        verbose_name=_("Kategoriyalar"),
        blank=True,
        help_text=_("Bitta taom bir nechta kategoriyada bo'lishi mumkin"),
    )
    name = models.CharField(_("Nomi"), max_length=100)
    description = models.TextField(_("Tavsifi"), blank=True, null=True)
    price = models.DecimalField(_("Narxi"), max_digits=12, decimal_places=2)
    image = models.ImageField(_("Rasmi"), upload_to='dishes/', blank=True, null=True)
    is_available = models.BooleanField(_("Mavjud"), default=True)
    is_active = models.BooleanField(_("Faol"), default=True)
    prep_time = models.PositiveIntegerField(_("Tayyorlanish vaqti (daqiqa)"), default=15)

    class Meta:
        verbose_name = _("Taom")
        verbose_name_plural = _("Taomlar")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.price} UZS"
