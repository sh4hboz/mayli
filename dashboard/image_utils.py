"""Rasm yuklashda WebP'ga siqish yordamchisi.

Mavjud (allaqachon saqlangan) rasmlarga tegmaydi — faqat yangi yuklanayotgan
fayllarni serverda saqlashdan oldin WebP'ga aylantiradi va hajmni solishtiradi.
Faqat WebP asl rasmdan kichikroq bo'lsa almashtiriladi.
"""
import io
import os

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

WEBP_QUALITY = 82

# WebP'ga aylantirishga arzimaydigan / mos kelmaydigan formatlar
_SKIP_EXTENSIONS = ('.svg', '.gif', '.webp', '.ico')
_SKIP_CONTENT_TYPES = {'image/svg+xml', 'image/gif', 'image/webp', 'image/x-icon'}


def _skip_result(uploaded, original_size, webp_size=None, reason='skipped'):
    uploaded.seek(0)
    return {
        'used_webp': False,
        'file': uploaded,
        'original_size': original_size,
        'webp_size': webp_size,
        'saved_pct': 0,
        'reason': reason,
    }


def convert_image_to_webp(uploaded, quality=WEBP_QUALITY):
    """Yuklangan rasmni WebP'ga aylantirib, hajmini asl bilan solishtiradi.

    Returns dict:
      used_webp     — WebP saqlanadimi (faqat kichikroq bo'lsa True)
      file          — saqlash uchun fayl (webp yoki asl)
      original_size — asl bayt hajmi
      webp_size     — webp bayt hajmi (None — agar aylantirilmagan bo'lsa)
      saved_pct     — tejalgan foiz
      reason        — 'converted' | 'webp_larger' | 'skipped' | 'error'
    """
    original_size = uploaded.size
    name = (uploaded.name or 'image').lower()
    content_type = (getattr(uploaded, 'content_type', '') or '').lower()

    # SVG/GIF/WebP/ICO — tegmaymiz
    if name.endswith(_SKIP_EXTENSIONS) or content_type in _SKIP_CONTENT_TYPES:
        return _skip_result(uploaded, original_size, reason='skipped')

    try:
        uploaded.seek(0)
        img = Image.open(uploaded)
        img.load()
    except Exception:
        return _skip_result(uploaded, original_size, reason='error')

    # Rejimni WebP qo'llaydigan ko'rinishga keltirish (alfa saqlanadi)
    if img.mode in ('P', 'LA'):
        img = img.convert('RGBA')
    elif img.mode == 'CMYK':
        img = img.convert('RGB')

    buffer = io.BytesIO()
    try:
        img.save(buffer, format='WEBP', quality=quality, method=6)
    except Exception:
        return _skip_result(uploaded, original_size, reason='error')

    webp_size = buffer.tell()

    # Faqat WebP kichikroq bo'lsa almashtiramiz
    if webp_size >= original_size:
        buffer.close()
        return _skip_result(uploaded, original_size, webp_size=webp_size, reason='webp_larger')

    buffer.seek(0)
    base = os.path.splitext(os.path.basename(uploaded.name or 'image'))[0]
    webp_file = InMemoryUploadedFile(
        buffer, field_name=None, name=f'{base}.webp',
        content_type='image/webp', size=webp_size, charset=None,
    )
    saved_pct = round((original_size - webp_size) / original_size * 100, 1)
    return {
        'used_webp': True,
        'file': webp_file,
        'original_size': original_size,
        'webp_size': webp_size,
        'saved_pct': saved_pct,
        'reason': 'converted',
    }
