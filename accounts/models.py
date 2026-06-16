"""
accounts/models.py

Custom User (telefon bilan kirish) + rollar + StaffProfile.

- AUTH_USER_MODEL = 'accounts.User' (config/settings/base.py da o'rnatilgan).
- USERNAME_FIELD = 'phone' — login telefon raqami orqali.
- StaffProfile: PIN kodi (4 raqam, hashlangan), lavozim, ishga qabul sanasi.
- Rollar: CUSTOMER → WAITER → BARMAN → ACCOUNTANT → MANAGER → OWNER + ADMIN
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password
from core.models import TimeStampedModel


class Role(models.TextChoices):
    CUSTOMER = 'customer', _('Mijoz')
    WAITER = 'waiter', _('Ofitsiant')
    BARMAN = 'barman', _('Barman')
    ACCOUNTANT = 'accountant', _('Bugalter')
    MANAGER = 'manager', _('Menejer')
    OWNER = 'owner', _('Ega')
    ADMIN = 'admin', _('Admin')

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Telefon raqami kiritilishi shart!')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi shart!')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi shart!')

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    """
    Mayli Restobar uchun maxsus foydalanuvchi modeli.
    USERNAME_FIELD = 'phone' — telefon raqam bilan kirish.
    """
    username = None  # username o'rniga phone ishlatiladi

    phone = models.CharField(
        _('Telefon raqami'),
        max_length=20,
        unique=True,
        help_text=_('+998 XX XXX-XX-XX formatida'),
    )
    full_name = models.CharField(_('To\'liq ism'), max_length=150, blank=True)
    role = models.CharField(
        _('Rol'), max_length=20, choices=Role.choices, default=Role.CUSTOMER
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = _('Foydalanuvchi')
        verbose_name_plural = _('Foydalanuvchilar')

    def __str__(self):
        return self.phone

    def get_full_name(self):
        """Custom `full_name` maydonini ishlatadi (AbstractUser first/last o'rniga)."""
        return self.full_name or self.phone

    def get_short_name(self):
        return self.full_name or self.phone

    @property
    def is_staff_member(self):
        return self.role not in (Role.CUSTOMER,)

    @property
    def is_customer(self):
        return self.role == Role.CUSTOMER


class StaffProfile(TimeStampedModel):
    """
    Xodim profili — xodimlarning qo'shimcha ma'lumotlari.
    Hozir accounts.User ga bog'langan.
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='staff_profile',
        verbose_name=_('Xodim'),
    )
    role = models.CharField(
        _('Rol'), max_length=20, choices=Role.choices, default=Role.WAITER
    )
    position = models.CharField(_('Lavozim'), max_length=100, blank=True)
    hired_at = models.DateField(_('Ishga qabul sanasi'), null=True, blank=True)
    pin_hash = models.CharField(
        _('PIN hash'), max_length=128, blank=True,
        help_text=_('4 raqamli PIN kod hashlangan holda saqlanadi'),
    )

    class Meta:
        verbose_name = _('Xodim profili')
        verbose_name_plural = _('Xodimlar profillari')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    def set_pin(self, raw_pin: str):
        """4 raqamli PIN kodni hashlaydi."""
        if not raw_pin.isdigit() or len(raw_pin) != 4:
            raise ValueError('PIN faqat 4 ta raqamdan iborat bo\'lishi kerak!')
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin: str) -> bool:
        """Kiritilgan PINni hash bilan solishtiradi."""
        return check_password(raw_pin, self.pin_hash)


# RBAC yordamchi funksiyalar
# (Kelajakda DRF permission_classes ichida ishlatiladi)
def has_role(user, *roles) -> bool:
    """Foydalanuvchining roli ko'rsatilgan rollar ichida ekanligini tekshiradi."""
    try:
        return user.role in roles
    except AttributeError:
        return False


def is_staff_role(role: str) -> bool:
    """Rol xodimga tegishli ekanligini tekshiradi (mijoz emas)."""
    return role not in (Role.CUSTOMER,)
