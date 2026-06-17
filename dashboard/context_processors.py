"""
dashboard/context_processors.py

Topbar bildirishnomalari — barcha dashboard sahifalarida (base.html → topbar) kerak.
Manbalar: yangi aloqa murojaatlari, bron so'rovlari (ContactMessage) va
sayt chat xabarlari (ChatMessage). Faqat tizimga kirgan xodimlar uchun hisoblanadi.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone


def topbar_notifications(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}

    items = []
    count = 0
    try:
        from website.models import ContactMessage
        from notifications.models import ChatMessage

        # 1) Yangi (o'qilmagan) murojaat va bron so'rovlari
        for c in ContactMessage.objects.filter(is_read=False).order_by('-created_at')[:6]:
            is_booking = (c.kind == ContactMessage.KIND_BOOKING)
            items.append({
                'icon': 'ti-calendar-event' if is_booking else 'ti-message-2',
                'color': 'info' if is_booking else 'warning',
                'title': c.name,
                'text': ('Bron so\'rovi' if is_booking else 'Yangi murojaat')
                        + (f' — {c.message[:40]}' if c.message else ''),
                'when': c.created_at,
                'url': reverse('dashboard_contact_detail', args=[c.pk]),
            })

        # 2) So'nggi sayt chat xabarlari (mehmondan)
        chats = (ChatMessage.objects
                 .filter(direction=ChatMessage.IN)
                 .select_related('session')
                 .order_by('-created_at')[:6])
        for m in chats:
            items.append({
                'icon': 'ti-brand-hipchat',
                'color': 'success',
                'title': 'Sayt chat',
                'text': m.text[:50],
                'when': m.created_at,
                'url': None,
            })

        items.sort(key=lambda x: x['when'], reverse=True)
        items = items[:8]

        # Badge: o'qilmagan murojaatlar + oxirgi 24 soatdagi chat xabarlari
        day_ago = timezone.now() - timedelta(hours=24)
        count = (
            ContactMessage.objects.filter(is_read=False).count()
            + ChatMessage.objects.filter(direction=ChatMessage.IN, created_at__gte=day_ago).count()
        )
    except Exception:
        items, count = [], 0

    return {
        'topbar_notifications': items,
        'topbar_notifications_count': count,
    }
