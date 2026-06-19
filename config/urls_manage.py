"""
config/urls_manage.py

manage.<domen> (DASHBOARD_HOST) hosti uchun ALOHIDA URLconf.

Bu yerda dashboard **ildizda** (`/`) ochiladi — URL'da `/dashboard/` bo'lagi yo'q.
HostSeparationMiddleware host == DASHBOARD_HOST bo'lganda `request.urlconf` ni shu
faylga o'rnatadi. Sayt (website) sahifalari bu hostda yo'q (tabiiy 404).

Apex (ommaviy) domen uchun esa `config/urls.py` ishlatiladi — u yerda dashboard/admin yo'q.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    # Maxfiy admin (ADMIN_URL .env orqali).
    path(settings.ADMIN_URL, admin.site.urls),

    # Til almashtirish (login sahifasi uchun, ixtiyoriy).
    path('i18n/', include('django.conf.urls.i18n')),

    # Xodimlar autentifikatsiyasi + xodimlarni boshqarish (login/logout/staff).
    path('', include('restobar.urls')),

    # Dashboard — ILDIZDA (`/`), `/dashboard/` prefiksisiz.
    path('', include('dashboard.urls')),
]
