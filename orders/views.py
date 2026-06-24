"""
orders/views.py — Sayt buyurtma API endpointlari (tilsiz, JSON).

Oqim: otp/request → otp/verify → create. Standart Django CSRF ishlatiladi
(frontend `X-CSRFToken` header yuboradi). Honeypot + IP rate-limit website.views
patternidan qayta ishlatiladi.
"""

import json
import logging

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from crm.integrations.textup import normalize_phone
from website.views import _is_rate_limited

from .models import Order, OrderStatus
from .services import OrderError, OrderService, OtpService

logger = logging.getLogger(__name__)


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return {}


def _is_bot(data):
    """Honeypot: 'website' maydoni to'ldirilgan bo'lsa — bot."""
    return bool(str(data.get('website', '')).strip())


@require_POST
def otp_request(request):
    data = _json_body(request)
    if _is_bot(data):
        return JsonResponse({'success': True})  # jim qabul qilgandek
    if _is_rate_limited(request, prefix='order_otp', limit=8, window=600):
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
    if _is_rate_limited(request, prefix='order_otp_verify', limit=20, window=600):
        return JsonResponse(
            {'verified': False, 'error': "Juda ko'p urinish."}, status=429,
        )
    phone = str(data.get('phone', '')).strip()[:20]
    code = str(data.get('code', '')).strip()[:6]
    result = OtpService.verify(phone, code)
    return JsonResponse(result, status=200 if result.get('verified') else 400)


@require_POST
def order_create(request):
    data = _json_body(request)
    if _is_bot(data):
        return JsonResponse({'success': True, 'message': "Buyurtmangiz qabul qilindi."})
    if _is_rate_limited(request, prefix='order_create', limit=10, window=600):
        return JsonResponse(
            {'success': False, 'error': "Juda ko'p urinish. Birozdan so'ng urinib ko'ring."},
            status=429,
        )
    try:
        order = OrderService.create(
            name=str(data.get('name', '')),
            phone=str(data.get('phone', '')),
            items=data.get('items', []),
            comment=str(data.get('comment', '')),
            payment_method=str(data.get('payment_method', '')),
        )
    except OrderError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception:  # noqa: BLE001
        logger.exception("Buyurtma yaratishda xato")
        return JsonResponse(
            {'success': False, 'error': "Xatolik yuz berdi. Birozdan so'ng urinib ko'ring."},
            status=500,
        )
    return JsonResponse({
        'success': True,
        'message': "Buyurtmangiz qabul qilindi! Tez orada operator siz bilan bog'lanadi.",
        'order_id': order.pk,
        'phone': order.phone,
    })


@require_GET
def my_orders(request):
    """Telefon raqami bo'yicha mijozning buyurtmalari (Buyurtmalarim sahifasi uchun)."""
    if _is_rate_limited(request, prefix='my_orders', limit=60, window=600):
        return JsonResponse({'orders': []}, status=429)
    phone = normalize_phone(request.GET.get('phone', ''))
    if not phone:
        return JsonResponse({'orders': []})
    qs = (Order.objects.filter(phone=phone)
          .prefetch_related('items').order_by('-created_at')[:50])
    orders = []
    for o in qs:
        orders.append({
            'id': o.pk,
            'created_at': timezone.localtime(o.created_at).strftime('%d.%m.%Y %H:%M'),
            'total': float(o.total_amount),
            'status': o.status,
            'status_label': str(o.get_status_display()),
            'is_active': o.is_active,
            'reject_reason': o.reject_reason if o.status == OrderStatus.REJECTED else '',
            'items': [
                {'name': it.dish_name, 'qty': it.quantity, 'total': float(it.line_total)}
                for it in o.items.all()
            ],
        })
    return JsonResponse({'orders': orders})
