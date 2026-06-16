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


def notify_chat_message(message: str, visitor_id: str = '', lang: str = '') -> bool:
    """Sayt chat oynasidan kelgan xabarni admin guruhiga yuboradi (bir tomonlama)."""
    message = html.escape(message)
    visitor_id = html.escape(visitor_id)
    lang = html.escape(lang)
    text = (
        f"💬 <b>Sayt chat xabari</b>\n"
        f"🆔 Mehmon: {visitor_id or '—'}\n"
        f"🌐 Til: {lang or '—'}\n"
        f"📝 Xabar: {message}"
    )
    return notify_admin(text)


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
