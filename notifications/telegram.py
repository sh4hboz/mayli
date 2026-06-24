"""
notifications/telegram.py

Telegram outbound bildirishnoma utilitalari.

Sayt formalaridan (aloqa, vakansiya) admin guruhiga xabar yuboradi.
Kelajakda CRM marketing kampaniyalari (SMS/Email/Telegram) ham shu
`send_message` / `notify_admin` infratuzilmasidan foydalanadi.
"""

import html
import logging
import re
import json as _json
import urllib.request
import urllib.error
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def format_uz_phone(phone: str) -> str:
    """Telefonni Telegram xabari uchun chiroyli formatga keltiradi.

    Masalan: '+998 (90) 820-10-04' yoki '998908201004' -> '+998-90-820-10-04'.
    Standart O'zbekiston raqami bo'lmasa, asl qiymatni o'zgartirmay qaytaradi.
    """
    if not phone:
        return phone
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 9:
        digits = '998' + digits
    if len(digits) == 12 and digits.startswith('998'):
        d = digits[3:]
        return f"+998-{d[0:2]}-{d[2:5]}-{d[5:7]}-{d[7:9]}"
    return phone


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


def send_message_return_id(chat_id, text: str, **kwargs) -> int | None:
    """Xabar yuboradi va Telegram message_id'ni qaytaradi (reply bog'lash uchun)."""
    data = _post('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        **kwargs,
    })
    if data and data.get('ok'):
        return data.get('result', {}).get('message_id')
    return None


def set_webhook(url: str, secret: str = '') -> dict | None:
    """Telegram setWebhook — botning yangilanishlarni shu URL'ga yuborishini ta'minlaydi.

    `secret` berilsa, Telegram har so'rovda `X-Telegram-Bot-Api-Secret-Token` header'ini
    qo'shadi (webhook view'da tekshiriladi).
    """
    payload = {'url': url, 'allowed_updates': ['message', 'callback_query']}
    if secret:
        payload['secret_token'] = secret
    return _post('setWebhook', payload)


# ─── Sayt bildirishnomalari ───────────────────────────────────────────────────

def notify_contact_form(name: str, phone: str, message: str, is_booking: bool = False) -> bool:
    # parse_mode=HTML — foydalanuvchi matnini escape qilamiz (HTML injection himoyasi).
    name = html.escape(name)
    phone = html.escape(format_uz_phone(phone))
    message = html.escape(message)
    if is_booking:
        title = "📅 <b>Yangi bron so'rovi</b>"
    else:
        title = "📩 <b>Yangi aloqa xabari</b>"
    text = (
        f"{title}\n"
        f"👤 Ism: {name}\n"
        f"📱 Telefon: {phone or '—'}\n"
        f"💬 Xabar: {message or '—'}"
    )
    return notify_admin(text)


def notify_chat_message(message: str, visitor_id: str = '', lang: str = '') -> int | None:
    """Sayt chat xabarini admin guruhiga yuboradi va bildirishnoma message_id'ni qaytaradi.

    Admin shu xabarga **Reply** qilib javob yozsa, webhook reply_to_message orqali
    mehmonni topadi. Shuning uchun message_id qaytariladi (saqlash uchun).
    """
    chat_id = _admin_chat_id()
    if not chat_id:
        return None
    message = html.escape(message)
    visitor_id = html.escape(visitor_id)
    lang = html.escape(lang)
    text = (
        f"💬 <b>Sayt chat xabari</b>\n"
        f"🆔 Mehmon: {visitor_id or '—'}\n"
        f"🌐 Til: {lang or '—'}\n"
        f"📝 Xabar: {message}\n\n"
        f"↩️ <i>Javob berish uchun shu xabarga «Reply» qiling.</i>"
    )
    return send_message_return_id(chat_id, text)


def notify_job_application(full_name: str, phone: str, vacancy_title: str = '') -> bool:
    full_name = html.escape(full_name)
    phone = html.escape(format_uz_phone(phone))
    vacancy_title = html.escape(vacancy_title)
    text = (
        f"📋 <b>Yangi ish arizasi</b>\n"
        f"👤 To'liq ism: {full_name}\n"
        f"📱 Telefon: {phone}\n"
        f"💼 Vakansiya: {vacancy_title or '—'}"
    )
    return notify_admin(text)


def order_message_text(order) -> str:
    """Buyurtma xabari matnini (HTML) tuzadi — yuborish va tahrirlash uchun umumiy."""
    name = html.escape(order.customer_name)
    phone = html.escape(format_uz_phone(order.phone))
    lines = [
        f"🛒 <b>Yangi buyurtma #{order.pk}</b>",
        f"👤 Mijoz: {name}",
        f"📱 Telefon: {phone}",
        "",
        "<b>Tarkibi:</b>",
    ]
    for it in order.items.all():
        dish_name = html.escape(it.dish_name)
        lines.append(f"• {dish_name} × {it.quantity} = {it.line_total:,.0f} so'm".replace(',', ' '))
    lines.append("")
    lines.append(f"💰 <b>Jami: {order.total_amount:,.0f} so'm</b>".replace(',', ' '))
    lines.append(f"💳 To'lov: {html.escape(order.get_payment_method_display())}")
    if order.comment:
        lines.append(f"📝 Izoh: {html.escape(order.comment)}")
    return "\n".join(lines)


def _order_keyboard(order_pk):
    return {'inline_keyboard': [[
        {'text': '✅ Qabul qilish', 'callback_data': f'order_accept:{order_pk}'},
        {'text': '❌ Rad etish', 'callback_data': f'order_reject:{order_pk}'},
    ]]}


def notify_order(order) -> bool:
    """Yangi buyurtmani admin guruhiga yuboradi + Qabul/Rad inline tugmalari bilan."""
    chat_id = _admin_chat_id()
    if not chat_id:
        return False
    return send_message(chat_id, order_message_text(order), reply_markup=_order_keyboard(order.pk))


def notify_reservation(reservation) -> bool:
    """Yangi bron so'rovini admin guruhiga yuboradi (manager tasdiqlashi uchun)."""
    name = html.escape(reservation.customer_name)
    phone = html.escape(format_uz_phone(reservation.customer_phone))
    table = html.escape(str(reservation.table))
    date = reservation.date.strftime('%d.%m.%Y')
    time = reservation.time.strftime('%H:%M')
    lines = [
        f"🪑 <b>Yangi bron so'rovi #{reservation.pk}</b>",
        f"👤 Mijoz: {name}",
        f"📱 Telefon: {phone}",
        f"📍 Stol: {table}",
        f"📅 Sana: {date} {time}",
        f"👥 Kishi: {reservation.guests}",
    ]
    if reservation.note:
        lines.append(f"📝 Izoh: {html.escape(reservation.note)}")
    lines.append("")
    lines.append("⏳ <i>Tasdiqlash uchun dashboard'ga kiring.</i>")
    return notify_admin("\n".join(lines))


def answer_callback(callback_query_id: str, text: str = '') -> bool:
    """Telegram callback (tugma bosilishi)ga javob — foydalanuvchiga toast ko'rsatadi."""
    data = _post('answerCallbackQuery', {'callback_query_id': callback_query_id, 'text': text})
    return bool(data and data.get('ok'))


def edit_message_text(chat_id, message_id, text: str, reply_markup=None) -> bool:
    """Mavjud xabar matnini (va tugmalarini) tahrirlaydi."""
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup is not None:
        payload['reply_markup'] = reply_markup
    data = _post('editMessageText', payload)
    return bool(data and data.get('ok'))
