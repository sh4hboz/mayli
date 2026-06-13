"""
notifications/views.py — BOSQICH 2.2

Telegram Webhook handler.
URL: /telegram/webhook/<secret>/

Oqim:
  Admin Telegram'da topic ichida javob yozadi
    → Telegram webhookni chaqiradi
    → Suhbat topiladi (telegram_chat_id + telegram_topic_id)
    → ChatMessage (STAFF, via=TELEGRAM) saqlanadi
    → Visitor WebSocket guruhiga push (mijozga real-time yetadi)
    → Support room'ga ham push (dashboard ko'radi)
"""

import json
import logging
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request, secret: str):
    expected = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', '')
    if secret != expected:
        logger.warning(f"Webhook: noto'g'ri secret '{secret}'")
        return HttpResponseForbidden('Forbidden')

    if request.method != 'POST':
        return HttpResponse('OK')

    try:
        update = json.loads(request.body)
    except Exception:
        return HttpResponse('OK')

    # Faqat oddiy xabarlarni qayta ishlaymiz
    message = update.get('message')
    if not message:
        return HttpResponse('OK')

    _handle_message(message)
    return HttpResponse('OK')


def _handle_message(message: dict):
    """Telegram xabarini qayta ishlaydi."""
    thread_id = message.get('message_thread_id')
    chat_id = message.get('chat', {}).get('id')
    text = (message.get('text') or '').strip()
    from_user = message.get('from', {})

    # Forum-topic xabari bo'lmasa — ignore
    if not thread_id or not text or not chat_id:
        return

    # Bot o'zining xabarini ignore qiladi
    if from_user.get('is_bot'):
        return

    # Admin chat ID bilan mos kelishini tekshirish
    admin_chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '')
    if admin_chat_id and str(chat_id) != str(admin_chat_id):
        logger.debug(f"Boshqa guruhdan xabar (chat_id={chat_id}) — ignore")
        return

    # Suhbatni topish
    from chat.models import ChatConversation, ChatMessage, SenderType, ViaChannel

    conv = (
        ChatConversation.objects
        .filter(telegram_chat_id=chat_id, telegram_topic_id=thread_id)
        .order_by('-created_at')
        .first()
    )
    if not conv:
        logger.debug(f"topic {thread_id} uchun suhbat topilmadi — ignore")
        return

    # Xabarni saqlash
    msg = ChatMessage.objects.create(
        conversation=conv,
        sender_type=SenderType.STAFF,
        via=ViaChannel.TELEGRAM,
        text=text,
    )
    conv.last_message_at = timezone.now()
    conv.save(update_fields=['last_message_at'])

    time_str = msg.created_at.strftime('%H:%M')

    # Visitor WebSocket guruhiga push
    _push_to_channels(conv, text, time_str)


def _push_to_channels(conv, text: str, time_str: str):
    """Channel layer orqali visitor va support room'ga push."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
    except ImportError:
        logger.warning("channels yoki asgiref o'rnatilmagan")
        return

    layer = get_channel_layer()
    if not layer:
        return

    push = async_to_sync(layer.group_send)

    # Mijoz vidjetiga (real-time)
    try:
        push(f"chat_{conv.visitor_id}", {
            'type': 'chat_message',
            'sender': 'staff',
            'message': text,
            'time': time_str,
        })
    except Exception as e:
        logger.error(f"Visitor WS push xatosi: {e}")

    # Dashboard (support_room)
    try:
        push('support_room', {
            'type': 'support_message',
            'visitor_id': str(conv.visitor_id),
            'conversation_id': conv.id,
            'sender_name': 'Telegram',
            'message': text,
            'time': time_str,
        })
    except Exception as e:
        logger.error(f"Support room push xatosi: {e}")
