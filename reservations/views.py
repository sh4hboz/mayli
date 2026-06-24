"""
reservations/views.py — Sayt bron API endpointlari (tilsiz, JSON).

Oqim (MAYLI_BRON_REJA.md §4): availability → otp/request → otp/verify → create.
Standart Django CSRF (frontend `X-CSRFToken` header yuboradi). Honeypot + IP
rate-limit `website.views` patternidan qayta ishlatiladi (orders/views.py namunasi).

Dashboard bron boshqaruvi (ro'yxat, tasdiq, stol holati) — BOSQICH 3.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from website.views import _is_rate_limited

from .services import (
    AvailabilityService,
    OtpService,
    ReservationError,
    ReservationService,
)

logger = logging.getLogger(__name__)


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return {}


def _is_bot(data):
    """Honeypot: 'website' maydoni to'ldirilgan bo'lsa — bot."""
    return bool(str(data.get('website', '')).strip())


@require_GET
def availability(request):
    """So'ralgan sana/vaqt/kishi bo'yicha stollar holati (2D sxema uchun)."""
    if _is_rate_limited(request, prefix='booking_avail', limit=120, window=600):
        return JsonResponse({'tables': []}, status=429)
    tables = AvailabilityService.for_query(
        date=request.GET.get('date', ''),
        time=request.GET.get('time', ''),
        guests=request.GET.get('guests', ''),
    )
    return JsonResponse({'tables': tables})


@require_POST
def otp_request(request):
    data = _json_body(request)
    if _is_bot(data):
        return JsonResponse({'success': True})  # jim qabul qilgandek
    if _is_rate_limited(request, prefix='booking_otp', limit=8, window=600):
        return JsonResponse(
            {'success': False, 'error': "Juda ko'p urinish. Birozdan so'ng urinib ko'ring."},
            status=429,
        )
    phone = str(data.get('phone', '')).strip()[:20]
    result = OtpService.request(phone)
    return JsonResponse(result, status=200 if result.get('success') else 400)


@require_POST
def otp_verify(request):
    data = _json_body(request)
    if _is_rate_limited(request, prefix='booking_otp_verify', limit=20, window=600):
        return JsonResponse({'verified': False, 'error': "Juda ko'p urinish."}, status=429)
    phone = str(data.get('phone', '')).strip()[:20]
    code = str(data.get('code', '')).strip()[:6]
    result = OtpService.verify(phone, code)
    return JsonResponse(result, status=200 if result.get('verified') else 400)


@require_POST
def reservation_create(request):
    data = _json_body(request)
    if _is_bot(data):
        return JsonResponse({'success': True, 'message': "So'rovingiz qabul qilindi."})
    if _is_rate_limited(request, prefix='booking_create', limit=10, window=600):
        return JsonResponse(
            {'success': False, 'error': "Juda ko'p urinish. Birozdan so'ng urinib ko'ring."},
            status=429,
        )
    try:
        reservation = ReservationService.create(
            name=str(data.get('name', '')),
            phone=str(data.get('phone', '')),
            table_id=data.get('table_id'),
            date=str(data.get('date', '')),
            time=str(data.get('time', '')),
            guests=data.get('guests'),
            note=str(data.get('note', '')),
        )
    except ReservationError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception:  # noqa: BLE001
        logger.exception("Bron yaratishda xato")
        return JsonResponse(
            {'success': False, 'error': "Xatolik yuz berdi. Birozdan so'ng urinib ko'ring."},
            status=500,
        )
    return JsonResponse({
        'success': True,
        'message': "So'rovingiz qabul qilindi! Operator tez orada tasdiqlash uchun bog'lanadi.",
        'reservation_id': reservation.pk,
    })
