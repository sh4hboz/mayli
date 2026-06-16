"""
notifications/telegram.py

Telegram outbound bildirishnoma utilitalari.

Sayt formalaridan (aloqa, vakansiya) admin guruhiga xabar yuboradi.
Kelajakda CRM marketing kampaniyalari (SMS/Email/Telegram) ham shu
`send_message` / `notify_admin` infratuzilmasidan foydalanadi.
"""

import html
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
    payload = {'url': url, 'allowed_updates': ['message']}
    if secret:
        payload['secret_token'] = secret
    return _post('setWebhook', payload)


# ─── Sayt bildirishnomalari ───────────────────────────────────────────────────

def notify_contact_form(name: str, phone: str, message: str, is_booking: bool = False) -> bool:
    # parse_mode=HTML — foydalanuvchi matnini escape qilamiz (HTML injection himoyasi).
    name = html.escape(name)
    phone = html.escape(phone)
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
    phone = html.escape(phone)
    vacancy_title = html.escape(vacancy_title)
    text = (
        f"📋 <b>Yangi ish arizasi</b>\n"
        f"👤 To'liq ism: {full_name}\n"
        f"📱 Telefon: {phone}\n"
        f"💼 Vakansiya: {vacancy_title or '—'}"
    )
    return notify_admin(text)
