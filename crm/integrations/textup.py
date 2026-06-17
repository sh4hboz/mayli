"""
crm/integrations/textup.py — TextUp (textup.uz) SMS API integratsiyasi.

Oqim: login (JWT) -> accessToken + userId -> SMS yuborish.
Token jarayon xotirasida keshlanadi; 401 (token eskirgan) bo'lsa qayta login qilinadi.

urllib.request pattern — notifications/telegram._post namunasi asosida.
Real qiymatlar (email/parol) settings orqali .env'dan olinadi (TEXTUP_EMAIL/TEXTUP_PASSWORD).
Endpoint'lar ham settings'da sozlanadi, shuning uchun TextUp API o'zgarsa kod tegmaydi.
"""

import json as _json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

# Standart endpoint'lar (settings'da qayta yozish mumkin)
DEFAULT_LOGIN_URL = 'https://api-auth.textup.uz/v1/login'
DEFAULT_SMS_URL = 'https://sms-api.textup.uz/v1/send'


class TextUpError(Exception):
    """TextUp API xatosi."""


def normalize_phone(phone):
    """Telefonni E.164 (+998XXXXXXXXX, chiziqchasiz) formatga keltiradi.

    '+998 (90) 820-10-04', '998908201004', '908201004' -> '+998908201004'.
    Yaroqsiz O'zbekiston raqami bo'lsa None qaytaradi.
    """
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 9:
        digits = '998' + digits
    if len(digits) == 12 and digits.startswith('998'):
        return '+' + digits
    return None


def _dig(data, *keys):
    """Javobdan birinchi mavjud kalitni qaytaradi (turli API shakllariga bardosh).

    Masalan _dig(resp, 'accessToken', 'access_token', 'token').
    Nested 'data' obyektini ham tekshiradi.
    """
    if not isinstance(data, dict):
        return None
    for k in keys:
        if k in data and data[k]:
            return data[k]
    inner = data.get('data')
    if isinstance(inner, dict):
        for k in keys:
            if k in inner and inner[k]:
                return inner[k]
    return None


# Modul darajasidagi token keshi (jarayon davomida login'ni takrorlamaslik uchun)
_token_cache = {'token': None, 'user_id': None}


class TextUpClient:
    """TextUp API mijozi — login + SMS yuborish."""

    def __init__(self, email=None, password=None):
        self.email = email if email is not None else getattr(settings, 'TEXTUP_EMAIL', '')
        self.password = password if password is not None else getattr(settings, 'TEXTUP_PASSWORD', '')
        self.login_url = getattr(settings, 'TEXTUP_LOGIN_URL', '') or DEFAULT_LOGIN_URL
        self.sms_url = getattr(settings, 'TEXTUP_SMS_URL', '') or DEFAULT_SMS_URL
        self.nickname_id = getattr(settings, 'TEXTUP_NICKNAME_ID', '') or ''
        self.timeout = 10

    # ── HTTP ────────────────────────────────────────────────────────────────
    def _request(self, url, payload, token=None):
        """JSON POST so'rovi yuboradi, JSON javobini qaytaradi.

        HTTP xato (4xx/5xx) bo'lsa TextUpError ko'taradi (status kodi bilan).
        """
        body = _json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout)
            raw = resp.read()
            return _json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = ''
            try:
                detail = e.read().decode('utf-8', 'replace')
            except Exception:
                pass
            raise TextUpError(f'HTTP {e.code}: {detail[:200]}') from e
        except urllib.error.URLError as e:
            raise TextUpError(f'Ulanish xatosi: {e.reason}') from e

    # ── Auth ────────────────────────────────────────────────────────────────
    def login(self):
        """TextUp'ga login qiladi, token va userId'ni keshga yozadi."""
        if not self.email or not self.password:
            raise TextUpError("TextUp kreditallari sozlanmagan (TEXTUP_EMAIL/TEXTUP_PASSWORD).")

        data = self._request(self.login_url, {'email': self.email, 'password': self.password})
        token = _dig(data, 'accessToken', 'access_token', 'token')
        user_id = _dig(data, 'userId', 'user_id')
        if not user_id:
            user = _dig(data, 'user') or {}
            if isinstance(user, dict):
                user_id = user.get('id')

        if not token:
            raise TextUpError(f"Login javobida token topilmadi: {str(data)[:200]}")

        _token_cache['token'] = token
        _token_cache['user_id'] = user_id
        logger.info("TextUp login muvaffaqiyatli (userId=%s).", user_id)
        return token

    def _ensure_token(self):
        if not _token_cache.get('token'):
            self.login()
        return _token_cache['token'], _token_cache.get('user_id')

    # ── SMS ─────────────────────────────────────────────────────────────────
    def send_sms(self, recipients, message, name=''):
        """Bir yoki bir nechta raqamga SMS yuboradi.

        Args:
            recipients: list[str] yoki str — E.164 raqam(lar) (+998...).
            message: str — SMS matni.
            name: str — yuboruvchi nomi (ixtiyoriy).

        Returns:
            dict: {'success': bool, 'error': str|None, 'sms_id': str|None}
        """
        if isinstance(recipients, str):
            recipients = [recipients]
        recipients = [r for r in (normalize_phone(p) for p in recipients) if r]
        if not recipients:
            return {'success': False, 'error': "Yaroqli telefon raqami yo'q", 'sms_id': None}
        if not message:
            return {'success': False, 'error': "Xabar matni bo'sh", 'sms_id': None}

        try:
            token, user_id = self._ensure_token()
            payload = {
                'message': message,
                'userId': user_id,
                'recipients': recipients,
                'name': name or '',
            }
            if self.nickname_id:
                payload['nicknameId'] = self.nickname_id

            try:
                data = self._request(self.sms_url, payload, token=token)
            except TextUpError as e:
                # Token eskirgan bo'lishi mumkin — bir marta qayta login qilib urinib ko'ramiz.
                if 'HTTP 401' in str(e) or 'HTTP 403' in str(e):
                    logger.info("TextUp token eskirgan, qayta login qilinmoqda.")
                    _token_cache['token'] = None
                    token, user_id = self._ensure_token()
                    payload['userId'] = user_id
                    data = self._request(self.sms_url, payload, token=token)
                else:
                    raise

            sms_id = _dig(data, 'smsId', 'sms_id', 'id')
            return {'success': True, 'error': None, 'sms_id': sms_id}

        except TextUpError as e:
            logger.error("TextUp SMS xatosi: %s", e)
            return {'success': False, 'error': str(e), 'sms_id': None}
        except Exception as e:  # noqa: BLE001 — kutilmagan xatoni ham log qilib qaytaramiz
            logger.exception("TextUp SMS kutilmagan xato")
            return {'success': False, 'error': str(e), 'sms_id': None}
