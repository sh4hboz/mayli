from django.urls import path
from django.http import HttpResponse

from .models import SiteSettings


def robots_txt(request):
    host = request.get_host()
    scheme = request.scheme
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /dashboard/',
        'Disallow: /api/',
        '',
        f'Sitemap: {scheme}://{host}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def llms_txt(request):
    """GEO (Generative Engine Optimization) — AI qidiruv tizimlari uchun /llms.txt."""
    site = SiteSettings.get()
    host = request.get_host()
    scheme = request.scheme
    base = f'{scheme}://{host}'

    lines = [
        f'# {site.name}',
        '',
        '> Termizdagi premium restoran va restobar. Milliy va Yevropa taomlari, '
        'ichimliklar, kalyan va unutilmas atmosfera. Oilaviy va do\'stona dam olish, '
        'tadbirlar uchun bron qilish imkoniyati.',
        '',
        '## Asosiy ma\'lumot',
        f'- Nomi: {site.name}',
        f'- Shahar: {site.city}',
    ]
    if site.address:
        lines.append(f'- Manzil: {site.address}')
    if site.phone_main:
        lines.append(f'- Telefon: {site.phone_main}')
    if site.working_hours:
        lines.append(f'- Ish vaqti: {site.working_hours}')
    if site.instagram_url:
        lines.append(f'- Instagram: {site.instagram_url}')

    lines += [
        '',
        '## Sahifalar',
        f'- [Bosh sahifa]({base}/): restoran haqida umumiy ma\'lumot, aksiyalar, galereya',
        f'- [Menyu]({base}/menu/): taomlar va ichimliklar ro\'yxati',
        f'- [Biz haqimizda]({base}/about/): restoran tarixi, atmosfera, aloqa',
        f'- [Yangiliklar]({base}/news/): tadbirlar va e\'lonlar',
        '',
        '## Xizmatlar',
        '- Stol bron qilish',
        '- Milliy va Yevropa oshxonasi',
        '- Ichimliklar va kalyan',
        '- Tadbirlar va bazmlar uchun zal',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


urlpatterns = [
    path('', robots_txt),
]
