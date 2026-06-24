"""
notifications/views.py

Telegram webhook — admin botdagi xabarga «Reply» qilganda, javobni mos chat
sessiyasiga (ChatMessage out) yozadi. Sayt chat oynasi uni poll orqali oladi.
"""
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ChatMessage

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request, secret):
    """Telegram update'larini qabul qiladi. Faqat reply'ni chat sessiyasiga yozadi.

    Xavfsizlik: URL'dagi `secret` + `X-Telegram-Bot-Api-Secret-Token` header
    `TELEGRAM_WEBHOOK_SECRET` bilan mos kelishi shart.
    """
    expected = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')
    header_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not expected or secret != expected or header_secret != expected:
        return HttpResponseForbidden('forbidden')

    try:
        update = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse('ok')  # noto'g'ri payload — jim o'tkazib yuboramiz

    # Inline tugma bosilishi (buyurtmani Qabul/Rad qilish — dashboard'siz)
    if 'callback_query' in update:
        _handle_order_callback(update['callback_query'])
        return HttpResponse('ok')

    message = update.get('message') or update.get('edited_message') or {}
    reply_to = message.get('reply_to_message') or {}
    reply_msg_id = reply_to.get('message_id')
    text = (message.get('text') or '').strip()

    # Faqat botning bildirishnomasiga Reply qilingan matnli xabarlar.
    if reply_msg_id and text:
        inbound = (
            ChatMessage.objects
            .filter(telegram_message_id=reply_msg_id, direction=ChatMessage.IN)
            .select_related('session')
            .first()
        )
        if inbound:
            ChatMessage.objects.create(
                session=inbound.session,
                direction=ChatMessage.OUT,
                text=text[:2000],
            )

    return HttpResponse('ok')


def _handle_order_callback(callback):
    """Telegram inline tugma: buyurtmani Qabul/Rad qilish (dashboard'siz)."""
    from django.utils import timezone

    from orders.models import Order, OrderStatus
    from .telegram import answer_callback, edit_message_text, order_message_text

    cq_id = callback.get('id')
    data = callback.get('data') or ''
    msg = callback.get('message') or {}
    chat_id = (msg.get('chat') or {}).get('id')
    message_id = msg.get('message_id')
    actor = (callback.get('from') or {}).get('first_name', '') or 'admin'

    if ':' not in data:
        return answer_callback(cq_id)
    action, _, raw_pk = data.partition(':')
    try:
        order = Order.objects.get(pk=int(raw_pk))
    except (ValueError, Order.DoesNotExist):
        return answer_callback(cq_id, "Buyurtma topilmadi.")

    if order.status != OrderStatus.NEW:
        answer_callback(cq_id, f"Allaqachon: {order.get_status_display()}")
        return

    if action == 'order_accept':
        order.status = OrderStatus.ACCEPTED
        order.accepted_at = timezone.now()
        order.is_read = True
        order.save(update_fields=['status', 'accepted_at', 'is_read', 'updated_at'])
        tail = f"\n\n✅ <b>Qabul qilindi</b> ({_esc(actor)})"
        answer_callback(cq_id, "Qabul qilindi ✅")
    elif action == 'order_reject':
        order.status = OrderStatus.REJECTED
        order.rejected_at = timezone.now()
        order.reject_reason = f"Telegram orqali rad etildi ({actor})"
        order.is_read = True
        order.save(update_fields=['status', 'rejected_at', 'reject_reason', 'is_read', 'updated_at'])
        tail = f"\n\n❌ <b>Bekor qilindi</b> ({_esc(actor)})"
        answer_callback(cq_id, "Bekor qilindi ❌")
    else:
        return answer_callback(cq_id)

    # Xabarni yangilaymiz va tugmalarni olib tashlaymiz.
    if chat_id and message_id:
        edit_message_text(chat_id, message_id, order_message_text(order) + tail,
                          reply_markup={'inline_keyboard': []})


def _esc(s):
    import html as _html
    return _html.escape(str(s or ''))
