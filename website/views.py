from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.cache import cache
from menu.models import Dish, Category
from .models import News, Promotion, GalleryItem, Partner, Vacancy, JobApplication, ContactMessage, Testimonial
from notifications.telegram import notify_contact_form, notify_job_application, notify_chat_message
from notifications.models import ChatSession, ChatMessage

# Admin shu vaqt ichida javob yozmasa, mehmonga avto-javob ko'rsatiladi.
CHAT_AUTO_REPLY_DELAY = 30  # soniya


# ─── Xavfsizlik yordamchilari ───────────────────────────────────────────────
# Maydon uzunligi cheklovlari (server tomonda — modeldan tashqari himoya).
MAX_NAME_LEN = 120
MAX_PHONE_LEN = 20
MAX_MESSAGE_LEN = 2000
MAX_CHAT_LEN = 1000

# Bir IP'dan maksimal yuborishlar (oddiy rate-limit, cache asosida).
SUBMIT_LIMIT = 6
SUBMIT_WINDOW = 600  # 10 daqiqa (soniya)
# Chat ko'proq xabar yuborishi mumkin — alohida, kengroq limit.
CHAT_LIMIT = 15
CHAT_WINDOW = 600


def _client_ip(request):
    """Foydalanuvchi IP manzilini (proxy'ni hisobga olib) qaytaradi."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _is_rate_limited(request, prefix='form_submit', limit=SUBMIT_LIMIT, window=SUBMIT_WINDOW):
    """IP bo'yicha yuborishlar sonini cheklaydi. True — limit oshgan."""
    ip = _client_ip(request) or 'unknown'
    key = f'{prefix}:{ip}'
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, window)
    return False


def _is_bot(request):
    """Honeypot maydoni to'ldirilgan bo'lsa — bot deb hisoblaymiz."""
    return bool(request.POST.get('website', '').strip())


def _ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def home(request):
    context = {
        'featured_dishes': Dish.objects.filter(is_active=True, is_available=True)[:8],
        'promotions': Promotion.objects.filter(is_active=True)[:3],
        'latest_news': News.objects.filter(is_active=True)[:3],
        'gallery_items': GalleryItem.objects.filter(is_active=True)[:8],
        'testimonials': Testimonial.objects.filter(is_active=True)[:6],
        'partners': Partner.objects.filter(is_active=True),
    }
    return render(request, 'website/home.html', context)


def _form_response(request, success, message='', error=''):
    """AJAX bo'lsa JSON, aks holda messages + redirect qaytaradi."""
    if _ajax(request):
        if success:
            return JsonResponse({'success': True, 'message': message})
        return JsonResponse({'success': False, 'error': error})
    if success:
        messages.success(request, message)
    else:
        messages.error(request, error)
    return redirect('website:about')


def about(request):
    if request.method == 'POST':
        # Honeypot: bot to'ldirsa — jim qabul qilgandek ko'rsatamiz (limitni tejaymiz).
        if _is_bot(request):
            return _form_response(request, True, message=_('Yuborildi.'))

        # Rate-limit: bir IP'dan haddan ziyod yuborish.
        if _is_rate_limited(request):
            return _form_response(
                request, False,
                error=_('Juda ko\'p urinish. Birozdan so\'ng qayta urinib ko\'ring.'),
            )

        # Maydonlarni o'qish va uzunlik bo'yicha kesish (server himoyasi).
        phone = request.POST.get('phone', '').strip()[:MAX_PHONE_LEN]
        message_text = request.POST.get('message', '').strip()[:MAX_MESSAGE_LEN]

        # Ariza topshirish (vakansiya formasi)
        if 'full_name' in request.POST:
            full_name = request.POST.get('full_name', '').strip()[:MAX_NAME_LEN]
            vacancy_id = request.POST.get('vacancy_id')
            vacancy = None
            if vacancy_id:
                try:
                    vacancy = Vacancy.objects.get(pk=vacancy_id, is_active=True)
                except (Vacancy.DoesNotExist, ValueError):
                    pass
            if full_name and phone:
                JobApplication.objects.create(
                    full_name=full_name, phone=phone,
                    message=message_text, vacancy=vacancy
                )
                notify_job_application(
                    full_name=full_name,
                    phone=phone,
                    vacancy_title=vacancy.title if vacancy else '',
                )
                return _form_response(
                    request, True,
                    message=_('Arizangiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.'),
                )
            return _form_response(
                request, False, error=_('Ism va telefon raqam majburiy!'),
            )

        # Aloqa xabari yoki bron so'rovi (bir model — ContactMessage)
        name = request.POST.get('name', '').strip()[:MAX_NAME_LEN]
        kind = request.POST.get('kind', ContactMessage.KIND_MESSAGE)
        if kind not in (ContactMessage.KIND_MESSAGE, ContactMessage.KIND_BOOKING):
            kind = ContactMessage.KIND_MESSAGE
        is_booking = kind == ContactMessage.KIND_BOOKING

        # Bron: ism+telefon majburiy; murojaat: ism+xabar majburiy.
        valid = (name and phone) if is_booking else (name and message_text)
        if valid:
            ContactMessage.objects.create(
                name=name, phone=phone, message=message_text, kind=kind,
            )
            notify_contact_form(name=name, phone=phone, message=message_text, is_booking=is_booking)
            if is_booking:
                msg = _('Bron so\'rovingiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.')
            else:
                msg = _('Xabaringiz yuborildi! Tez orada javob beramiz.')
            return _form_response(request, True, message=msg)

        if is_booking:
            err = _('Ism va telefon raqam majburiy!')
        else:
            err = _('Ism va xabar majburiy!')
        return _form_response(request, False, error=err)

    context = {
        'vacancies': Vacancy.objects.filter(is_active=True)
    }
    return render(request, 'website/about.html', context)


MENU_PAGE_SIZE = 6


def _menu_queryset(cat):
    """Faol/mavjud taomlar; kategoriya slug berilsa — filtrlanadi."""
    qs = (
        Dish.objects.filter(is_active=True, is_available=True)
        .prefetch_related('categories')
    )
    if cat:
        qs = qs.filter(categories__slug=cat, categories__is_active=True)
    return qs.distinct()


def menu(request):
    """Menyu sahifasi — birinchi porsiya server'dan (SEO + JS'siz fallback)."""
    categories = Category.objects.filter(is_active=True)
    page_obj = Paginator(_menu_queryset(''), MENU_PAGE_SIZE).get_page(1)
    return render(request, 'website/menu.html', {
        'categories': categories,
        'dishes': page_obj.object_list,
        'has_more': page_obj.has_next(),
    })


def menu_items(request):
    """AJAX: kategoriya + sahifa bo'yicha taom kartalarini (HTML) qaytaradi."""
    cat = request.GET.get('cat', '').strip()
    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    page_obj = Paginator(_menu_queryset(cat), MENU_PAGE_SIZE).get_page(page)
    html = render_to_string(
        'website/partials/_dish_cards.html',
        {'dishes': page_obj.object_list},
        request=request,
    )
    return JsonResponse({'html': html, 'has_more': page_obj.has_next()})


def dish_detail(request, pk):
    """Bitta taom uchun alohida sahifa (URL = taom id raqami)."""
    dish = get_object_or_404(
        Dish.objects.prefetch_related('categories'),
        pk=pk, is_active=True, is_available=True,
    )
    related = (
        Dish.objects.filter(is_active=True, is_available=True,
                            categories__in=dish.categories.all())
        .exclude(pk=dish.pk)
        .distinct()[:4]
    )
    return render(request, 'website/dish_detail.html', {
        'dish': dish,
        'related': related,
    })


def chat_send(request):
    """Sayt chat xabarini saqlaydi va admin botiga uzatadi (ikki tomonlama chat).

    Javob (admin Reply yoki 30s avto-javob) `chat_poll` orqali olinadi.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST only'}, status=405)

    # Bot honeypot: 'website' maydoni to'lsa — jim qabul qilgandek ko'rsatamiz.
    if _is_bot(request):
        return JsonResponse({'success': True, 'reply': str(_('Rahmat!'))})

    if _is_rate_limited(request, prefix='chat_send', limit=CHAT_LIMIT, window=CHAT_WINDOW):
        return JsonResponse(
            {'success': False, 'error': str(_('Juda ko\'p xabar. Birozdan so\'ng urinib ko\'ring.'))},
            status=429,
        )

    message = request.POST.get('message', '').strip()[:MAX_CHAT_LEN]
    visitor_id = request.POST.get('visitor_id', '').strip()[:64]
    lang = request.POST.get('lang', '').strip()[:5]
    if not message:
        return JsonResponse({'success': False, 'error': str(_('Xabar bo\'sh.'))}, status=400)
    if not visitor_id:
        return JsonResponse({'success': False, 'error': str(_('Sessiya aniqlanmadi.'))}, status=400)

    # Sessiya + kiruvchi xabarni saqlaymiz (ikki tomonlama chat uchun).
    session, _created = ChatSession.objects.get_or_create(
        visitor_id=visitor_id, defaults={'lang': lang},
    )
    if lang and session.lang != lang:
        session.lang = lang
        session.save(update_fields=['lang', 'updated_at'])

    inbound = ChatMessage.objects.create(
        session=session, direction=ChatMessage.IN, text=message,
    )

    # Botga yuboramiz va bildirishnoma message_id'ni saqlaymiz (admin Reply'ini bog'lash uchun).
    tg_message_id = notify_chat_message(message, visitor_id=visitor_id, lang=lang)
    if tg_message_id:
        inbound.telegram_message_id = tg_message_id
        inbound.save(update_fields=['telegram_message_id'])

    # Avto-javob DARHOL emas — chat_poll'da 30s o'tib materializatsiya qilinadi.
    return JsonResponse({'success': True})


def chat_poll(request):
    """Sayt chat oynasi uchun yangi 'out' xabarlarni (admin javobi / avto-javob) qaytaradi.

    GET: visitor_id, after (oxirgi ko'rilgan ChatMessage id).
    30s avto-javob shu yerda lazy yaratiladi (fon vazifasi kerak emas).
    """
    visitor_id = request.GET.get('visitor_id', '').strip()[:64]
    try:
        after = int(request.GET.get('after', '0'))
    except (TypeError, ValueError):
        after = 0
    if not visitor_id:
        return JsonResponse({'messages': []})

    try:
        session = ChatSession.objects.get(visitor_id=visitor_id)
    except ChatSession.DoesNotExist:
        return JsonResponse({'messages': []})

    _maybe_create_auto_reply(session)

    out_qs = session.messages.filter(direction=ChatMessage.OUT, id__gt=after).order_by('id')
    new_ids = [m.id for m in out_qs]
    data = [{
        'id': m.id,
        'text': m.text,
        'time': timezone.localtime(m.created_at).strftime('%H:%M'),
        'is_auto': m.is_auto,
    } for m in out_qs]

    if new_ids:
        ChatMessage.objects.filter(id__in=new_ids).update(delivered=True)

    return JsonResponse({'messages': data})


def _maybe_create_auto_reply(session):
    """Oxirgi kiruvchi xabarga 30s ichida admin javobi bo'lmasa — avto-javob yaratadi."""
    last_in = session.messages.filter(direction=ChatMessage.IN).order_by('-id').first()
    if not last_in:
        return
    # Shu kiruvchi xabardan keyin biror 'out' (admin yoki avto) bormi?
    has_response = session.messages.filter(
        direction=ChatMessage.OUT, id__gt=last_in.id,
    ).exists()
    if has_response:
        return
    if timezone.now() - last_in.created_at < timedelta(seconds=CHAT_AUTO_REPLY_DELAY):
        return
    ChatMessage.objects.create(
        session=session,
        direction=ChatMessage.OUT,
        is_auto=True,
        text=str(_('Rahmat! Xabaringiz qabul qilindi. Tez orada javob beramiz yoki qo\'ng\'iroq qilamiz.')),
    )


def news_list(request):
    news = News.objects.filter(is_active=True)
    return render(request, 'website/news_list.html', {'news_list': news})


def news_detail(request, slug):
    article = get_object_or_404(News, slug=slug, is_active=True)
    related = News.objects.filter(is_active=True).exclude(pk=article.pk)[:3]
    return render(request, 'website/news_detail.html', {
        'article': article,
        'related': related,
    })


def privacy_policy(request):
    return render(request, 'website/privacy_policy.html')


def terms_conditions(request):
    return render(request, 'website/terms_conditions.html')
