from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.views.decorators.http import require_POST
import json
from decimal import Decimal
from menu.models import Dish, Category
from orders.models import Order, OrderItem, OrderType
from .models import News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage, Testimonial
from notifications.telegram import notify_contact_form, notify_job_application, notify_new_order


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

def order_page(request):
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'dishes'
    )
    categories_with_dishes = [
        (cat, list(cat.dishes.filter(is_active=True, is_available=True)))
        for cat in categories
    ]
    categories_with_dishes = [(c, d) for c, d in categories_with_dishes if d]
    return render(request, 'website/order.html', {
        'categories_with_dishes': categories_with_dishes,
    })


@require_POST
def order_create(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Noto\'g\'ri so\'rov formati.'}, status=400)

    order_type = data.get('order_type', '')
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    delivery_address = data.get('delivery_address', '').strip()
    delivery_lat = data.get('delivery_lat') or None
    delivery_lng = data.get('delivery_lng') or None
    pickup_time = data.get('pickup_time', '').strip()
    notes = data.get('notes', '').strip()
    marketing_consent = bool(data.get('marketing_consent', False))
    items = data.get('items', [])

    # Validatsiya
    if order_type not in ('delivery', 'takeaway'):
        return JsonResponse({'success': False, 'error': 'Noto\'g\'ri buyurtma turi.'}, status=400)
    if not customer_name:
        return JsonResponse({'success': False, 'error': 'Ism majburiy.'}, status=400)
    if not customer_phone:
        return JsonResponse({'success': False, 'error': 'Telefon raqam majburiy.'}, status=400)
    
    if order_type == 'delivery':
        if not delivery_address:
            return JsonResponse({'success': False, 'error': 'Yetkazib berish manzili majburiy.'}, status=400)
        # Koordinata bo'yicha yetkazib berish zonasi tekshiruvi
        if delivery_lat is not None and delivery_lng is not None:
            try:
                lat_f = float(delivery_lat)
                lng_f = float(delivery_lng)
                from orders.utils import is_in_delivery_zone
                if not is_in_delivery_zone(lat_f, lng_f):
                    return JsonResponse({
                        'success': False,
                        'error': 'Kechirasiz, tanlangan manzil yetkazib berish hududimizga kirmaydi.'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Noto\'g\'ri koordinatalar formati.'}, status=400)
                
    if not items:
        return JsonResponse({'success': False, 'error': 'Savat bo\'sh.'}, status=400)

    # Taomlarni tekshirish
    dish_ids = [item.get('id') for item in items if item.get('id')]
    dishes_map = {d.id: d for d in Dish.objects.filter(
        id__in=dish_ids, is_active=True, is_available=True
    )}

    if len(dishes_map) == 0:
        return JsonResponse({'success': False, 'error': 'Taomlar topilmadi.'}, status=400)

    # Buyurtma yaratish — daily_id race-condition himoya bilan
    from django.db import transaction
    from orders.utils import assign_daily_ids

    with transaction.atomic():
        order = Order.objects.create(
            order_type=order_type,
            customer_name=customer_name,
            customer_phone=customer_phone,
            delivery_address=delivery_address if order_type == 'delivery' else '',
            delivery_lat=delivery_lat if order_type == 'delivery' else None,
            delivery_lng=delivery_lng if order_type == 'delivery' else None,
            pickup_time=pickup_time if order_type == 'takeaway' else '',
            notes=notes,
            marketing_consent=marketing_consent,
        )

        total = Decimal('0')
        for item in items:
            dish_id = item.get('id')
            qty = max(1, int(item.get('qty', 1)))
            dish = dishes_map.get(dish_id)
            if not dish:
                continue
            OrderItem.objects.create(
                order=order,
                dish=dish,
                qty=qty,
                unit_price=dish.price,
            )
            total += dish.price * qty

        order.subtotal = total
        order.total = total
        order.save()

    assign_daily_ids(order)

    # Telegram bildirishnoma
    notify_new_order(order)

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'message': f'Buyurtmangiz qabul qilindi! Buyurtma raqami: #{order.id}',
    })


def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status_labels = {
        'pending': 'Qabul qilindi ✅',
        'cooking': 'Tayyorlanmoqda 👨‍🍳',
        'delivering': "Yo'lda 🚚",
        'preparing': 'Tayyorlanmoqda 👨‍🍳',
        'ready': 'Tayyor 🎉',
        'delivered': 'Yetkazildi ✅',
        'completed': 'Yakunlandi ✅',
        'cancelled': 'Bekor qilindi ❌',
    }
    return JsonResponse({
        'order_id': order.id,
        'status': order.status,
        'status_label': status_labels.get(order.status, order.get_status_display()),
        'order_type': order.order_type,
        'total': str(order.total),
    })


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
