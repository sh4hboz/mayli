"""
accounts/models.py

Custom User (username bilan kirish) + rollar + StaffProfile.

- AUTH_USER_MODEL = 'accounts.User' (config/settings/base.py da o'rnatilgan).
- USERNAME_FIELD = 'username' — oddiy login (username) + parol orqali kirish.
- phone — xodimning ixtiyoriy aloqa raqami (login uchun ishlatilmaydi).
- StaffProfile: lavozim, ishga qabul sanasi.
- Rollar (faqat xodim): WAITER → BARMAN → ACCOUNTANT → MANAGER → OWNER + ADMIN.
  Mijozlar tizimga KIRMAYDI (CUSTOMER roli yo'q) — sayt to'liq ommaviy.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from core.models import TimeStampedModel


class Role(models.TextChoices):
    WAITER = 'waiter', _('Ofitsiant')
    BARMAN = 'barman', _('Barman')
    ACCOUNTANT = 'accountant', _('Bugalter')
    MANAGER = 'manager', _('Menejer')
    OWNER = 'owner', _('Ega')
    ADMIN = 'admin', _('Admin')


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Foydalanuvchi nomi (login) kiritilishi shart!')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', Role.OWNER)  # superuser dashboard'ga kira olsin

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi shart!')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi shart!')

        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    """
    Mayli Restobar uchun maxsus foydalanuvchi modeli.
    USERNAME_FIELD = 'username' — oddiy login + parol bilan kirish.
    """
    phone = models.CharField(
        _('Telefon raqami'),
        max_length=20,
        null=True,
        blank=True,
        help_text=_('Ixtiyoriy aloqa raqami (login uchun ishlatilmaydi)'),
    )
    full_name = models.CharField(_('To\'liq ism'), max_length=150, blank=True)
    role = models.CharField(
        _('Rol'), max_length=20, choices=Role.choices, default=Role.WAITER
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = _('Foydalanuvchi')
        verbose_name_plural = _('Foydalanuvchilar')

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Custom `full_name` maydonini ishlatadi (AbstractUser first/last o'rniga)."""
        return self.full_name or self.username

    def get_short_name(self):
        return self.full_name or self.username


class StaffProfile(TimeStampedModel):
    """
    Xodim profili — xodimlarning qo'shimcha ma'lumotlari.
    accounts.User ga bog'langan.
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

    class Meta:
        verbose_name = _('Xodim profili')
        verbose_name_plural = _('Xodimlar profillari')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


# RBAC yordamchi funksiya (kelajakda DRF permission_classes ichida ishlatiladi)
def has_role(user, *roles) -> bool:
    """Foydalanuvchining roli ko'rsatilgan rollar ichida ekanligini tekshiradi."""
    try:
        return user.role in roles
    except AttributeError:
        return False
