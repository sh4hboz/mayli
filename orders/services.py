"""
orders/services.py — OTP tasdig'i va buyurtma yaratish biznes-logikasi.

Xavfsizlik prinsiplari:
  - Narx/nom HAR DOIM DB'dan olinadi (frontend yuborgan qiymatga ishonilmaydi).
  - Buyurtma faqat telefon OTP bilan tasdiqlangach yaratiladi.
  - Minimum summa va "buyurtma ochiqmi" tekshiruvlari server tomonda.
"""

import logging
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from crm.integrations.textup import TextUpClient, normalize_phone
from menu.models import Dish
from notifications.telegram import notify_order

from .models import Order, OrderItem, OrderSettings, OtpCode, PaymentMethod

logger = logging.getLogger(__name__)

OTP_PURPOSE = 'order'
MAX_QTY_PER_ITEM = 99


class OrderError(Exception):
    """Foydalanuvchiga ko'rsatiladigan buyurtma/OTP xatosi."""


def _otp_ttl():
    return timedelta(minutes=getattr(settings, 'ORDER_OTP_TTL_MINUTES', 5))


def _max_attempts():
    return getattr(settings, 'ORDER_OTP_MAX_ATTEMPTS', 5)


class OtpService:
    """Telefon tasdig'i uchun bir martalik kod (SMS — TextUp)."""

    COOLDOWN = 60     # soniya — bir telefonga qayta yuborishdan oldin
    HOURLY_LIMIT = 5  # bir telefon uchun soatlik so'rovlar

    @classmethod
    def request(cls, phone):
        """OTP kod yaratadi va SMS yuboradi. Returns {success, error, dev_code}."""
        norm = normalize_phone(phone)
        if not norm:
            return {'success': False, 'error': _("Telefon raqami noto'g'ri.")}

        cd_key = f'order_otp_cd:{norm}'
        if cache.get(cd_key):
            return {'success': False, 'error': _("Iltimos, biroz kuting va qayta urinib ko'ring.")}

        hr_key = f'order_otp_hr:{norm}'
        sent = cache.get(hr_key, 0)
        if sent >= cls.HOURLY_LIMIT:
            return {'success': False, 'error': _("Juda ko'p urinish. Bir soatdan so'ng urinib ko'ring.")}

        # Eski ishlatilmagan kodlarni bekor qilamiz (bir vaqtda 1 ta amaldagi kod).
        OtpCode.objects.filter(phone=norm, purpose=OTP_PURPOSE, consumed=False).update(consumed=True)

        code = f'{random.randint(0, 999999):06d}'
        OtpCode.objects.create(
            phone=norm, code=code, purpose=OTP_PURPOSE,
            expires_at=timezone.now() + _otp_ttl(),
        )
        cache.set(cd_key, 1, cls.COOLDOWN)
        cache.set(hr_key, sent + 1, 3600)

        sent_ok = cls._send_sms(norm, code)
        if not sent_ok and not settings.DEBUG:
            return {'success': False, 'error': _("SMS yuborib bo'lmadi. Birozdan so'ng urinib ko'ring.")}

        result = {'success': True, 'error': None}
        if settings.DEBUG:
            # Dev qulayligi: shablon hali tasdiqlanmagan bo'lsa kodni qaytaramiz.
            result['dev_code'] = code
        return result

    @staticmethod
    def _send_sms(phone, code):
        """OTP SMS yuboradi. Shablon (template_id) bo'lmasa dev-stub (faqat log)."""
        template_id = getattr(settings, 'ORDER_OTP_TEMPLATE_ID', '')
        text = (getattr(settings, 'ORDER_OTP_TEXT', '') or '').format(code=code)
        if not template_id:
            logger.warning("ORDER OTP (stub — SMS yuborilmadi): %s -> %s", phone, code)
            return False
        try:
            res = TextUpClient().send_sms([phone], text, name='Mayli', template_id=template_id)
            if not res.get('success'):
                logger.error("OTP SMS xatosi: %s", res.get('error'))
            return bool(res.get('success'))
        except Exception:  # noqa: BLE001
            logger.exception("OTP SMS yuborishda kutilmagan xato")
            return False

    @classmethod
    def verify(cls, phone, code):
        """Kodni tekshiradi. Returns {verified, error}. Consume QILMAYDI."""
        norm = normalize_phone(phone)
        if not norm:
            return {'verified': False, 'error': _("Telefon raqami noto'g'ri.")}
        code = (code or '').strip()

        otp = (OtpCode.objects
               .filter(phone=norm, purpose=OTP_PURPOSE, consumed=False)
               .order_by('-created_at').first())
        if not otp or otp.is_expired:
            return {'verified': False, 'error': _("Kod muddati o'tgan. Qaytadan kod oling.")}
        if otp.attempts >= _max_attempts():
            return {'verified': False, 'error': _("Juda ko'p urinish. Qaytadan kod oling.")}

        otp.attempts += 1
        if otp.code != code:
            otp.save(update_fields=['attempts', 'updated_at'])
            return {'verified': False, 'error': _("Kod noto'g'ri.")}

        otp.is_verified = True
        otp.save(update_fields=['attempts', 'is_verified', 'updated_at'])
        return {'verified': True, 'error': None}


class OrderService:
    """Buyurtma yaratish — OTP tasdig'i + DB narxlari + min-summa tekshiruvi."""

    @classmethod
    def create(cls, name, phone, items, comment='', payment_method=''):
        """Buyurtma yaratadi. items: [{'id': int, 'qty': int}]. OrderError ko'taradi."""
        valid_methods = {m.value for m in PaymentMethod}
        if payment_method not in valid_methods:
            payment_method = PaymentMethod.CASH
        with transaction.atomic():
            cfg = OrderSettings.get()
            if not cfg.is_open:
                raise OrderError(_("Hozircha buyurtma qabul qilinmayapti."))

            name = (name or '').strip()
            norm = normalize_phone(phone)
            if not name:
                raise OrderError(_("Ism majburiy."))
            if not norm:
                raise OrderError(_("Telefon raqami noto'g'ri."))

            # Telefon tasdiqlangan bo'lishi shart (verify'dan keyin, hali consume bo'lmagan).
            otp = (OtpCode.objects
                   .select_for_update()
                   .filter(phone=norm, purpose=OTP_PURPOSE, is_verified=True, consumed=False)
                   .order_by('-created_at').first())
            if not otp or otp.is_expired:
                raise OrderError(_("Telefon tasdiqlanmagan. Avval SMS kodni tasdiqlang."))

            norm_items = cls._normalize_items(items)
            if not norm_items:
                raise OrderError(_("Savat bo'sh."))

            dishes = {d.pk: d for d in Dish.objects.filter(
                pk__in=list(norm_items.keys()), is_active=True, is_available=True)}

            total = Decimal('0')
            line_items = []
            for did, qty in norm_items.items():
                dish = dishes.get(did)
                if not dish:
                    continue  # faol bo'lmagan / o'chirilgan taomni tashlab ketamiz
                total += dish.price * qty
                line_items.append((dish, qty))
            if not line_items:
                raise OrderError(_("Tanlangan taomlar mavjud emas."))

            if cfg.min_order_amount and total < cfg.min_order_amount:
                raise OrderError(
                    _("Minimum buyurtma summasi: %(amount)s so'm.")
                    % {'amount': f'{cfg.min_order_amount:,.0f}'.replace(',', ' ')}
                )

            customer = cls._upsert_customer(name[:120], norm)
            order = Order.objects.create(
                customer_name=name[:120], phone=norm,
                comment=(comment or '').strip()[:2000], total_amount=total,
                payment_method=payment_method, customer=customer,
            )
            OrderItem.objects.bulk_create([
                OrderItem(order=order, dish=dish, dish_name=dish.name,
                          unit_price=dish.price, quantity=qty)
                for dish, qty in line_items
            ])
            otp.consumed = True
            otp.save(update_fields=['consumed'])

            # Telegram — commit'dan keyin (xato bo'lsa ham buyurtma saqlanadi).
            transaction.on_commit(lambda: cls._notify(order.pk))
            return order

    @staticmethod
    def _upsert_customer(name, phone):
        """Mijozni telefon bo'yicha CRM'ga saqlaydi/yangilaydi (telefon — asosiy kalit)."""
        try:
            from crm.models import Customer, CustomerSource
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={'first_name': name or 'Mijoz', 'source': CustomerSource.WEBSITE},
            )
            # Mavjud mijozda ism bo'sh bo'lsa — buyurtmadagi ism bilan to'ldiramiz.
            if not created and name and (not customer.first_name or customer.first_name == 'Mijoz'):
                customer.first_name = name
                customer.save(update_fields=['first_name', 'updated_at'])
            return customer
        except Exception:  # noqa: BLE001 — CRM xatosi buyurtmani to'xtatmasin
            logger.exception("Mijozni CRM'ga saqlashda xato (phone=%s)", phone)
            return None

    @staticmethod
    def _notify(order_pk):
        try:
            order = Order.objects.prefetch_related('items').get(pk=order_pk)
            notify_order(order)
        except Exception:  # noqa: BLE001
            logger.exception("notify_order yuborishda xato (order=%s)", order_pk)

    @staticmethod
    def _normalize_items(items):
        """[{'id','qty'}] -> {dish_id: qty}; yaroqsizlarni tashlaydi."""
        out = {}
        if not isinstance(items, list):
            return out
        for it in items:
            if not isinstance(it, dict):
                continue
            try:
                did = int(it.get('id'))
                qty = int(it.get('qty'))
            except (TypeError, ValueError):
                continue
            if did <= 0 or qty <= 0:
                continue
            out[did] = min(out.get(did, 0) + qty, MAX_QTY_PER_ITEM)
        return out
