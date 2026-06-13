from django.urls import path
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /dashboard/',
        'Disallow: /api/',
        '',
        'Sitemap: https://maylirestobar.uz/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


urlpatterns = [
    path('', robots_txt),
]
