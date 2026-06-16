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
