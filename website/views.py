from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from menu.models import Dish
from .models import News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage, Testimonial
from notifications.telegram import notify_contact_form, notify_job_application


def home(request):
    context = {
        'featured_dishes': Dish.objects.filter(is_active=True, is_available=True)[:8],
        'promotions': Promotion.objects.filter(is_active=True)[:3],
        'latest_news': News.objects.filter(is_active=True)[:3],
        'gallery_items': GalleryItem.objects.filter(is_active=True)[:8],
        'testimonials': Testimonial.objects.filter(is_active=True)[:6],
    }
    return render(request, 'website/home.html', context)


def about(request):
    if request.method == 'POST':
        # Ariza topshirish (vakansiya formasi)
        if 'full_name' in request.POST:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            message_text = request.POST.get('message', '').strip()
            vacancy_id = request.POST.get('vacancy_id')
            vacancy = None
            if vacancy_id:
                try:
                    vacancy = Vacancy.objects.get(pk=vacancy_id, is_active=True)
                except Vacancy.DoesNotExist:
                    pass
            if full_name and phone:
                JobApplication.objects.create(
                    full_name=full_name, phone=phone,
                    message=message_text, vacancy=vacancy
                )
                # Telegram bildirishnoma
                notify_job_application(
                    full_name=full_name,
                    phone=phone,
                    vacancy_title=vacancy.title if vacancy else '',
                )
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': _('Arizangiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.')})
                messages.success(request, _('Arizangiz qabul qilindi! Tez orada siz bilan bog\'lanamiz.'))
                return redirect('website:about')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': _('Ism va telefon raqam majburiy!')})
        # Oddiy aloqa xabari
        else:
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            message_text = request.POST.get('message', '').strip()
            if name and message_text:
                ContactMessage.objects.create(name=name, phone=phone, message=message_text)
                notify_contact_form(name=name, phone=phone, message=message_text)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': _('Xabaringiz yuborildi! Tez orada javob beramiz.')})
                messages.success(request, _('Xabaringiz yuborildi! Tez orada javob beramiz.'))
                return redirect('website:about')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': _('Ism va xabar majburiy!')})

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
