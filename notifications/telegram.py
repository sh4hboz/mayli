"""
notifications/telegram.py

Telegram bildirishnoma va chat ko'prigi utilitalari.

BOSQICH 0.7: oddiy notify funksiyalar (send_message, notify_admin, ...)
BOSQICH 2.2: forum-topic ko'prigi (create_forum_topic, send_to_topic,
             notify_chat_message_to_topic)
"""

import logging
import json as _json
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _token() -> str:
    return getattr(settings, 'TELEGRAM_BOT_TOKEN', '')


def _admin_chat_id() -> str:
    return str(getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', ''))


def _post(method: str, payload: dict) -> dict | None:
    """Telegram API ga POST so'rov yuboradi, JSON javobini qaytaradi."""
    token = _token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN yo'q — so'rov bekor qilindi.")
        return None
    url = TELEGRAM_API.format(token=token, method=method)
    try:
        body = _json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return _json.loads(resp.read())
    except Exception as e:
        logger.error(f"Telegram API [{method}] xatosi: {e}")
        return None


# ─── Asosiy utilita ────────────────────────────────────────────────────────────

def send_message(chat_id, text: str, **kwargs) -> bool:
    """Telegram'ga xabar yuboradi."""
    data = _post('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        **kwargs,
    })
    return bool(data and data.get('ok'))


def notify_admin(text: str) -> bool:
    """Admin guruhiga bildirishnoma yuboradi."""
    chat_id = _admin_chat_id()
    if not chat_id:
        return False
    return send_message(chat_id, text)


# ─── Sayt bildirishnomalari ───────────────────────────────────────────────────

def notify_contact_form(name: str, phone: str, message: str) -> bool:
    text = (
        f"📩 <b>Yangi aloqa xabari</b>\n"
        f"👤 Ism: {name}\n"
        f"📱 Telefon: {phone or '—'}\n"
        f"💬 Xabar: {message}"
    )
    return notify_admin(text)


def notify_job_application(full_name: str, phone: str, vacancy_title: str = '') -> bool:
    text = (
        f"📋 <b>Yangi ish arizasi</b>\n"
        f"👤 To'liq ism: {full_name}\n"
        f"📱 Telefon: {phone}\n"
        f"💼 Vakansiya: {vacancy_title or '—'}"
    )
    return notify_admin(text)


def notify_new_order(order) -> bool:
    """Yangi delivery/takeaway buyurtmasi haqida admin'ga bildirishnoma."""
    is_delivery = order.order_type == 'delivery'
    type_emoji = '🚚' if is_delivery else '🏃'
    type_label = 'Yetkazib berish' if is_delivery else 'Olib ketish'

    items_text = ''
    for item in order.items.select_related('dish').all():
        items_text += f"  • {item.dish.name} × {item.qty} = {int(item.unit_price * item.qty):,} so'm\n"

    address_line = ''
    if is_delivery and order.delivery_address:
        address_line = f"📍 Manzil: {order.delivery_address}\n"
    elif not is_delivery and order.pickup_time:
        address_line = f"⏰ Olib ketish: {order.pickup_time}\n"

    notes_line = f"📝 Izoh: {order.notes}\n" if order.notes else ''

    text = (
        f"{type_emoji} <b>Yangi buyurtma #{order.id}</b> — {type_label}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 {order.customer_name}\n"
        f"📱 {order.customer_phone}\n"
        f"{address_line}"
        f"{notes_line}"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{items_text}"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 Jami: <b>{int(order.total):,} so'm</b>\n"
        f"💵 To'lov: Naqd"
    )
    return notify_admin(text)


def notify_new_chat_message(visitor_name: str, language: str, text: str) -> bool:
    """Oddiy xabar (forum-topic mavjud bo'lmasa fallback sifatida)."""
    lang_emoji = {'uz': '🇺🇿', 'ru': '🇷🇺', 'en': '🇬🇧'}.get(language, '🌐')
    msg = (
        f"💬 <b>Yangi chat xabari</b> {lang_emoji}\n"
        f"👤 {visitor_name}\n"
        f"📝 {text[:300]}"
    )
    return notify_admin(msg)


# ─── Forum-topic ko'prigi (BOSQICH 2.2) ───────────────────────────────────────

def create_forum_topic(title: str) -> int | None:
    """
    Admin guruhida yangi forum-topic yaratadi.
    Guruh supergroup + Topics rejimida bo'lishi shart.
    Muvaffaqiyatli bo'lsa message_thread_id qaytaradi.
    """
    chat_id = _admin_chat_id()
    if not chat_id:
        return None
    data = _post('createForumTopic', {
        'chat_id': int(chat_id),
        'name': title[:128],
    })
    if data and data.get('ok'):
        return data['result']['message_thread_id']
    logger.warning(f"createForumTopic muvaffaqiyatsiz: {data}")
    return None


def send_to_topic(topic_id: int, text: str) -> bool:
    """Muayyan forum-topicga xabar yuboradi."""
    chat_id = _admin_chat_id()
    if not chat_id or not topic_id:
        return False
    data = _post('sendMessage', {
        'chat_id': int(chat_id),
        'message_thread_id': topic_id,
        'text': text,
        'parse_mode': 'HTML',
    })
    return bool(data and data.get('ok'))


def send_staff_reply_to_topic(conversation_id: int, sender_name: str, text: str) -> bool:
    """
    Xodim dashboard'dan yozgan javobini Telegram forum-topicga yuboradi.
    Topic yo'q bo'lsa — ignore (visitor hali yozmagan demak).
    """
    from chat.models import ChatConversation
    try:
        conv = ChatConversation.objects.only(
            'telegram_topic_id', 'telegram_chat_id'
        ).get(id=conversation_id)
    except ChatConversation.DoesNotExist:
        return False

    if not conv.telegram_topic_id:
        return False

    msg_text = f"<b>👨‍💼 {sender_name}:</b>\n{text}"
    return send_to_topic(conv.telegram_topic_id, msg_text)


def notify_chat_message_to_topic(conversation_id: int, visitor_name: str,
                                  language: str, text: str) -> bool:
    """
    Visitor xabari kelganda admin guruhidagi forum-topicga yuboradi.

    Oqim:
    1. Conversation'da telegram_topic_id bor → mavjud topicga yubor.
    2. Yo'q → yangi topic yarat → conv'ga saqlash → topicga yubor.
    3. Topic yaratish imkonsiz (guruh forum emas) → oddiy xabar (fallback).
    """
    from chat.models import ChatConversation

    try:
        conv = ChatConversation.objects.get(id=conversation_id)
    except ChatConversation.DoesNotExist:
        return notify_new_chat_message(visitor_name, language, text)

    admin_chat_id = _admin_chat_id()
    if not admin_chat_id:
        return notify_new_chat_message(visitor_name, language, text)

    lang_emoji = {'uz': '🇺🇿', 'ru': '🇷🇺', 'en': '🇬🇧'}.get(language, '🌐')

    # Topic yo'q — yangi yaratish
    if not conv.telegram_topic_id:
        phone_suffix = f" · {conv.visitor_phone}" if conv.visitor_phone else ''
        topic_title = f"{lang_emoji} {visitor_name}{phone_suffix}"
        topic_id = create_forum_topic(topic_title)

        if not topic_id:
            # Guruh forum emas — oddiy xabar
            return notify_new_chat_message(visitor_name, language, text)

        ChatConversation.objects.filter(id=conversation_id).update(
            telegram_chat_id=int(admin_chat_id),
            telegram_topic_id=topic_id,
        )
        conv.telegram_topic_id = topic_id

        # Topicga kirish xabari (birinchi xabar — kontekst uchun)
        intro = (
            f"🆕 <b>Yangi suhbat</b>\n"
            f"👤 {visitor_name} {lang_emoji}\n"
            f"📱 {conv.visitor_phone or '—'}\n"
            f"🌐 Til: {language.upper()}\n\n"
            f"Javob berish uchun shu topicga yozing ↓"
        )
        send_to_topic(conv.telegram_topic_id, intro)

    # Xabarni topicga yuborish
    msg_text = f"<b>{visitor_name}:</b>\n{text}"
    return send_to_topic(conv.telegram_topic_id, msg_text)
