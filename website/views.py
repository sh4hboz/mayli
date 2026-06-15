from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.cache import cache
from menu.models import Dish
from .models import News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage, Testimonial
from notifications.telegram import notify_contact_form, notify_job_application


# ─── Xavfsizlik yordamchilari ───────────────────────────────────────────────
# Maydon uzunligi cheklovlari (server tomonda — modeldan tashqari himoya).
MAX_NAME_LEN = 120
MAX_PHONE_LEN = 20
MAX_MESSAGE_LEN = 2000

# Bir IP'dan maksimal yuborishlar (oddiy rate-limit, cache asosida).
SUBMIT_LIMIT = 6
SUBMIT_WINDOW = 600  # 10 daqiqa (soniya)


def _client_ip(request):
    """Foydalanuvchi IP manzilini (proxy'ni hisobga olib) qaytaradi."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _is_rate_limited(request):
    """IP bo'yicha yuborishlar sonini cheklaydi. True — limit oshgan."""
    ip = _client_ip(request) or 'unknown'
    key = f'form_submit:{ip}'
    count = cache.get(key, 0)
    if count >= SUBMIT_LIMIT:
        return True
    cache.set(key, count + 1, SUBMIT_WINDOW)
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
