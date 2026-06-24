"""
reservations/services.py — OTP tasdig'i, stol bo'shligi va bron yaratish logikasi.

Xavfsizlik / izchillik prinsiplari (MAYLI_BRON_REJA.md §3, §4):
  - Bron faqat telefon OTP bilan tasdiqlangach yaratiladi.
  - Bron yaratish ATOMIC + tanlangan stolga `select_for_update()` → bir stolga
    bir vaqtda ikki parallel so'rovdan faqat bittasi o'tadi (race-condition himoyasi).
  - "Slot" YO'Q: `conflict_window` (BookingSettings, default 120 daq) faqat shu
    oraliqda ikkinchi bronni to'sadi. Stol holatini manager qo'lda boshqaradi.

`orders/services.py` namunasi asosida (OtpService bir xil yondashuv).
"""

import logging
import random
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from crm.integrations.textup import TextUpClient, normalize_phone

from .models import (
    ACTIVE_RESERVATION_STATUSES,
    BookingSettings,
    OtpCode,
    Reservation,
    ReservationSource,
    ReservationStatus,
    Table,
)

logger = logging.getLogger(__name__)

MAX_GUESTS = 50


class ReservationError(Exception):
    """Foydalanuvchiga ko'rsatiladigan bron/OTP xatosi."""


def _otp_ttl():
    return timedelta(minutes=getattr(settings, 'BOOKING_OTP_TTL_MINUTES', 5))


def _max_attempts():
    return getattr(settings, 'BOOKING_OTP_MAX_ATTEMPTS', 5)


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

        cd_key = f'booking_otp_cd:{norm}'
        if cache.get(cd_key):
            return {'success': False, 'error': _("Iltimos, biroz kuting va qayta urinib ko'ring.")}

        hr_key = f'booking_otp_hr:{norm}'
        sent = cache.get(hr_key, 0)
        if sent >= cls.HOURLY_LIMIT:
            return {'success': False, 'error': _("Juda ko'p urinish. Bir soatdan so'ng urinib ko'ring.")}

        # Eski ishlatilmagan kodlarni bekor qilamiz (bir vaqtda 1 ta amaldagi kod).
        OtpCode.objects.filter(phone=norm, consumed=False).update(consumed=True)

        code = f'{random.randint(0, 999999):06d}'
        OtpCode.objects.create(
            phone=norm, code=code,
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
        template_id = getattr(settings, 'BOOKING_OTP_TEMPLATE_ID', '')
        text = (getattr(settings, 'BOOKING_OTP_TEXT', '') or '').format(code=code)
        if not template_id:
            logger.warning("BRON OTP (stub — SMS yuborilmadi): %s -> %s", phone, code)
            return False
        try:
            res = TextUpClient().send_sms([phone], text, name='Mayli', template_id=template_id)
            if not res.get('success'):
                logger.error("Bron OTP SMS xatosi: %s", res.get('error'))
            return bool(res.get('success'))
        except Exception:  # noqa: BLE001
            logger.exception("Bron OTP SMS yuborishda kutilmagan xato")
            return False

    @classmethod
    def verify(cls, phone, code):
        """Kodni tekshiradi. Returns {verified, error}. Consume QILMAYDI."""
        norm = normalize_phone(phone)
        if not norm:
            return {'verified': False, 'error': _("Telefon raqami noto'g'ri.")}
        code = (code or '').strip()

        otp = (OtpCode.objects
               .filter(phone=norm, consumed=False)
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


def _parse_date(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d').date()
        except ValueError:
            return None
    return value


def _parse_time(value):
    if isinstance(value, str):
        for fmt in ('%H:%M', '%H:%M:%S'):
            try:
                return datetime.strptime(value.strip(), fmt).time()
            except ValueError:
                continue
        return None
    return value


def _minutes_apart(t1, t2):
    """Ikki `time` orasidagi farq (daqiqa, musbat)."""
    m1 = t1.hour * 60 + t1.minute
    m2 = t2.hour * 60 + t2.minute
    return abs(m1 - m2)


class AvailabilityService:
    """So'ralgan sana/vaqt/kishi bo'yicha har stolning holatini hisoblaydi."""

    @classmethod
    def for_query(cls, date, time, guests):
        """Returns list[dict]: har stol uchun {id, number, zone, capacity, shape,
        pos_x, pos_y, width, height, state} — state: free|busy|small.

        - small: capacity < guests
        - busy: shu stol+sanada faol bron `conflict_window` ichida, yoki status=occupied
        - free: aks holda
        """
        d = _parse_date(date)
        t = _parse_time(time)
        guests = cls._clean_guests(guests)
        cfg = BookingSettings.get()

        tables = (Table.objects.filter(is_active=True, zone__is_active=True)
                  .select_related('zone'))

        # Conflict tekshiruvi uchun shu sanadagi faol bronlarni stol bo'yicha guruhlaymiz.
        busy_by_table = {}
        if d is not None and t is not None:
            res_qs = Reservation.objects.filter(
                date=d, status__in=ACTIVE_RESERVATION_STATUSES,
            ).values_list('table_id', 'time')
            for table_id, r_time in res_qs:
                if _minutes_apart(t, r_time) < cfg.conflict_window:
                    busy_by_table.setdefault(table_id, True)

        out = []
        for tbl in tables:
            if guests and tbl.capacity < guests:
                state = 'small'
            elif tbl.status == 'occupied' or busy_by_table.get(tbl.pk):
                state = 'busy'
            else:
                state = 'free'
            out.append({
                'id': tbl.pk,
                'number': tbl.number,
                'zone_id': tbl.zone_id,
                'zone': tbl.zone.name,
                'capacity': tbl.capacity,
                'shape': tbl.shape,
                'pos_x': tbl.pos_x,
                'pos_y': tbl.pos_y,
                'width': tbl.width,
                'height': tbl.height,
                'state': state,
            })
        return out

    @staticmethod
    def _clean_guests(guests):
        try:
            g = int(guests)
        except (TypeError, ValueError):
            return 0
        return g if 0 < g <= MAX_GUESTS else 0


class ReservationService:
    """Bron yaratish — OTP tasdig'i + race-condition himoyasi + conflict tekshiruvi."""

    @classmethod
    def create(cls, name, phone, table_id, date, time, guests, note='',
               source=ReservationSource.WEBSITE_2D):
        """Bron (pending) yaratadi. ReservationError ko'taradi."""
        cfg = BookingSettings.get()
        if not cfg.is_open:
            raise ReservationError(_("Hozircha bron qabul qilinmayapti."))

        name = (name or '').strip()
        norm = normalize_phone(phone)
        if not name:
            raise ReservationError(_("Ism majburiy."))
        if not norm:
            raise ReservationError(_("Telefon raqami noto'g'ri."))

        d = _parse_date(date)
        t = _parse_time(time)
        if d is None or t is None:
            raise ReservationError(_("Sana yoki vaqt noto'g'ri."))

        today = timezone.localdate()
        if d < today:
            raise ReservationError(_("O'tgan sanaga bron qilib bo'lmaydi."))
        if d > today + timedelta(days=cfg.advance_days):
            raise ReservationError(
                _("Faqat %(n)s kun oldinga bron qilish mumkin.") % {'n': cfg.advance_days}
            )
        if not (cfg.open_time <= t <= cfg.close_time):
            raise ReservationError(
                _("Bron qabul soatlari: %(o)s – %(c)s.")
                % {'o': cfg.open_time.strftime('%H:%M'), 'c': cfg.close_time.strftime('%H:%M')}
            )

        try:
            guests_n = int(guests)
        except (TypeError, ValueError):
            guests_n = 0
        if not (0 < guests_n <= MAX_GUESTS):
            raise ReservationError(_("Kishi soni noto'g'ri."))

        try:
            table_id = int(table_id)
        except (TypeError, ValueError):
            raise ReservationError(_("Stol tanlanmagan."))

        with transaction.atomic():
            # Telefon tasdiqlangan bo'lishi shart (verify'dan keyin, hali consume bo'lmagan).
            otp = (OtpCode.objects
                   .select_for_update()
                   .filter(phone=norm, is_verified=True, consumed=False)
                   .order_by('-created_at').first())
            if not otp or otp.is_expired:
                raise ReservationError(_("Telefon tasdiqlanmagan. Avval SMS kodni tasdiqlang."))

            # 🔴 Stol qatorini lock qilamiz → shu stolga parallel bron yaratish serializatsiya bo'ladi.
            try:
                table = (Table.objects.select_for_update()
                         .select_related('zone')
                         .get(pk=table_id, is_active=True, zone__is_active=True))
            except Table.DoesNotExist:
                raise ReservationError(_("Stol topilmadi."))

            if table.capacity < guests_n:
                raise ReservationError(_("Bu stol tanlangan kishi soniga kichik."))

            # Conflict: shu stol+sanada faol bron `conflict_window` ichida bormi?
            existing = Reservation.objects.filter(
                table=table, date=d, status__in=ACTIVE_RESERVATION_STATUSES,
            ).values_list('time', flat=True)
            for r_time in existing:
                if _minutes_apart(t, r_time) < cfg.conflict_window:
                    raise ReservationError(_("Bu stol tanlangan vaqtga band. Boshqa vaqt yoki stol tanlang."))

            reservation = Reservation.objects.create(
                table=table,
                customer_name=name[:120],
                customer_phone=norm,
                date=d, time=t, guests=guests_n,
                note=(note or '').strip()[:2000],
                otp_verified=True,
                status=ReservationStatus.PENDING,
                source=source if source in ReservationSource.values else ReservationSource.WEBSITE_2D,
            )
            otp.consumed = True
            otp.save(update_fields=['consumed', 'updated_at'])

            # Telegram — commit'dan keyin (xato bo'lsa ham bron saqlanadi).
            transaction.on_commit(lambda: cls._notify(reservation.pk))
            return reservation

    @staticmethod
    def _notify(reservation_pk):
        try:
            from notifications.telegram import notify_reservation
            reservation = Reservation.objects.select_related('table', 'table__zone').get(pk=reservation_pk)
            notify_reservation(reservation)
        except Exception:  # noqa: BLE001
            logger.exception("notify_reservation yuborishda xato (reservation=%s)", reservation_pk)
