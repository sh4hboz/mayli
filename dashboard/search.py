"""
dashboard/search.py — Global topbar qidiruv: registr + rolga mos qidiruv xizmati.

Topbar qidiruvi (`dashboard_search` view) shu modulni chaqiradi. Har model uchun qaysi
maydonlar qidiriladi, qaysi rollar ko'ra oladi va natija qaysi sahifaga olib borishini
`SEARCH_REGISTRY` belgilaydi. So'rov vaqtida registr foydalanuvchi roli bo'yicha
filtrlanadi — ya'ni xodim faqat o'ziga ruxsat berilgan modellardan natija oladi.

Tezlik: har model bo'yicha ko'pi bilan PER_MODEL_LIMIT ta natija; `phone` maydonlari
allaqachon db_index. Front (dashboard-search.js) debounce + min belgi bilan so'raydi.
"""

from dataclasses import dataclass
from typing import Callable, Sequence

from django.db.models import Q
from django.urls import reverse

from accounts.models import Role
from crm.models import Campaign, Customer
from menu.models import Dish
from notifications.models import ChatSession
from orders.models import Order
from website.models import ContactMessage

# Dashboard'ga kira oladigan asosiy rollar (CMSBaseMixin bilan bir xil).
CMS_ROLES = (Role.OWNER, Role.MANAGER, Role.ADMIN)

# Bitta so'rovda har model bo'yicha ko'pi bilan shuncha natija.
PER_MODEL_LIMIT = 5
# Qidiruv ishga tushishi uchun minimal belgilar soni.
MIN_QUERY_LEN = 2


@dataclass(frozen=True)
class SearchEntry:
    label: str                              # guruh sarlavhasi (UI)
    icon: str                               # Tabler ikon klassi, masalan "ti ti-shopping-cart"
    model: type                             # qidiriladigan model
    fields: Sequence[str]                   # icontains qidiriladigan maydonlar
    roles: Sequence[str]                    # shu natijani ko'ra oladigan rollar
    url_name: str                           # detail/edit URL nomi (namespace'siz)
    title: Callable                         # obj -> sarlavha matni
    subtitle: Callable = lambda obj: ''     # obj -> ikkilamchi matn
    search_id: bool = False                 # raqamli so'rovda pk bo'yicha ham qidirish
    distinct: bool = False                  # teskari FK/M2M qidiruvida takrorni olib tashlash

    def get_queryset(self, query, limit):
        q = Q()
        for f in self.fields:
            q |= Q(**{f'{f}__icontains': query})
        if self.search_id:
            digits = query.lstrip('#').strip()
            if digits.isdigit():
                q |= Q(pk=int(digits))
        qs = self.model.objects.filter(q)
        if self.distinct:
            qs = qs.distinct()
        return qs[:limit]


SEARCH_REGISTRY = [
    SearchEntry(
        label='Buyurtmalar', icon='ti ti-shopping-cart',
        model=Order, fields=['customer_name', 'phone'],
        roles=CMS_ROLES, url_name='dashboard_order_detail',
        title=lambda o: f'#{o.pk} — {o.customer_name}',
        subtitle=lambda o: f'{o.phone} · {o.get_status_display()}',
        search_id=True,
    ),
    SearchEntry(
        label='Mijozlar', icon='ti ti-users',
        model=Customer, fields=['first_name', 'last_name', 'phone'],
        roles=CMS_ROLES, url_name='dashboard_customer_detail',
        title=lambda c: c.full_name or c.phone,
        subtitle=lambda c: c.phone,
    ),
    SearchEntry(
        label='Taomlar', icon='ti ti-tools-kitchen-2',
        model=Dish, fields=['name'],
        roles=CMS_ROLES, url_name='dashboard_dish_edit',
        title=lambda d: d.name,
        subtitle=lambda d: f'{d.price:g} so\'m',
    ),
    SearchEntry(
        label='Kampaniyalar', icon='ti ti-speakerphone',
        model=Campaign, fields=['name'],
        roles=CMS_ROLES, url_name='dashboard_campaign_detail',
        title=lambda c: c.name,
        subtitle=lambda c: c.get_channel_display(),
    ),
    SearchEntry(
        label='Murojaatlar', icon='ti ti-mail',
        model=ContactMessage, fields=['name', 'phone', 'message'],
        roles=CMS_ROLES, url_name='dashboard_contact_detail',
        title=lambda m: m.name,
        subtitle=lambda m: (m.message or '')[:60],
    ),
    SearchEntry(
        label='Chat', icon='ti ti-message-2',
        model=ChatSession, fields=['messages__text'],
        roles=CMS_ROLES, url_name='dashboard_chat_detail',
        title=lambda s: f'Chat {s.visitor_id[:8]}',
        subtitle=lambda s: '',
        distinct=True,
    ),
]


def global_search(user, query, per_model=PER_MODEL_LIMIT):
    """Foydalanuvchi roli bo'yicha ruxsat berilgan modellarda qidiradi.

    Natija: guruhlangan ro'yxat — [{'label', 'icon', 'items': [{'title','subtitle','url'}]}].
    Bo'sh yoki juda qisqa so'rov → [].
    """
    query = (query or '').strip()
    if len(query) < MIN_QUERY_LEN:
        return []

    role = getattr(user, 'role', '')
    results = []
    for entry in SEARCH_REGISTRY:
        if role not in entry.roles:
            continue                                   # ← RUXSAT FILTRI
        items = []
        for obj in entry.get_queryset(query, per_model):
            items.append({
                'title': entry.title(obj),
                'subtitle': entry.subtitle(obj),
                'url': reverse(entry.url_name, args=[obj.pk]),
            })
        if items:
            results.append({'label': entry.label, 'icon': entry.icon, 'items': items})
    return results
