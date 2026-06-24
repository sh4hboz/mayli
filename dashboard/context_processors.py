"""
dashboard/context_processors.py

Topbar bildirishnomalari — barcha dashboard sahifalarida (base.html → topbar) kerak.
Manbalar: yangi (o'qilmagan) aloqa murojaatlari/bron (ContactMessage), javob
kutayotgan sayt chat sessiyalari va yangi (o'qilmagan) buyurtmalar.
Hisoblagich o'qilgan-holatga asoslanadi — o'qilgach kamayadi, "Hammasi o'qildi" 0 qiladi.
"""

from datetime import timedelta

from django.db.models import OuterRef, Subquery
from django.urls import reverse
from django.utils import timezone


def build_notifications(user):
    """Topbar bildirishnomalari uchun items/count/birthday ni qaytaradi.

    Context processor ham, AJAX hisoblagich endpoint ham shu funksiyadan foydalanadi.
    """
    items = []
    count = 0
    try:
        from website.models import ContactMessage
        from notifications.models import ChatSession, ChatMessage
        from orders.models import Order, OrderStatus

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

        # 2) Javob kutayotgan sayt chat sessiyalari (oxirgi xabar mehmondan)
        last_dir = (ChatMessage.objects
                    .filter(session=OuterRef('pk')).order_by('-id').values('direction')[:1])
        awaiting_sessions = (ChatSession.objects
                             .annotate(_last_dir=Subquery(last_dir))
                             .filter(_last_dir=ChatMessage.IN)
                             .order_by('-updated_at'))
        for s in awaiting_sessions[:6]:
            last = s.messages.order_by('-id').first()
            items.append({
                'icon': 'ti-brand-hipchat',
                'color': 'success',
                'title': 'Sayt chat',
                'text': (last.text[:50] if last else ''),
                'when': s.updated_at,
                'url': reverse('dashboard_chat_detail', args=[s.pk]),
            })

        # 3) Yangi (ko'rilmagan) buyurtmalar
        for o in Order.objects.filter(status=OrderStatus.NEW, is_read=False).order_by('-created_at')[:6]:
            items.append({
                'icon': 'ti-shopping-cart',
                'color': 'primary',
                'title': f'Buyurtma — {o.customer_name}',
                'text': f"{o.total_amount:,.0f} so'm".replace(',', ' '),
                'when': o.created_at,
                'url': reverse('dashboard_order_detail', args=[o.pk]),
            })

        items.sort(key=lambda x: x['when'], reverse=True)
        items = items[:8]

        # Badge: o'qilmagan murojaat + javob kutayotgan chat + yangi buyurtma
        count = (
            ContactMessage.objects.filter(is_read=False).count()
            + awaiting_sessions.count()
            + Order.objects.filter(status=OrderStatus.NEW, is_read=False).count()
        )
    except Exception:
        items, count = [], 0

    # ── Bugungi tug'ilgan kunlar (qisman avtomatik SMS tabrik) ──────────────
    birthday = None
    try:
        from crm.services import BirthdayService

        pending = list(BirthdayService.todays_pending()[:10])
        bcount = len(pending)
        if bcount:
            if bcount == 1:
                label = f"Bugun {pending[0].full_name or pending[0].phone}ning tug'ilgan kuni 🎂"
            else:
                label = f"Bugun {bcount} kishining tug'ilgan kuni 🎂"
            birthday = {
                'count': bcount,
                'label': label,
                'url': reverse('dashboard_birthday_congratulate'),
            }
            count += bcount
    except Exception:
        birthday = None

    return {
        'topbar_notifications': items,
        'topbar_notifications_count': count,
        'topbar_birthday': birthday,
    }


def topbar_notifications(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    return build_notifications(user)
