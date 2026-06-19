"""
core/middleware.py

HostSeparationMiddleware — dashboard va admin'ni alohida subdomenga ajratadi.

`manage.maylirestobar.uz` (DASHBOARD_HOST) hostida dashboard **ildizda** (`/`) ochiladi
(alohida `config.urls_manage` URLconf'i orqali) — URL'da `/dashboard/` bo'lagi yo'q.
Ommaviy domen (maylirestobar.uz) esa odatdagi `config.urls` ni ishlatadi — u yerda
dashboard/admin umuman yo'q, ya'ni tashqaridan topib bo'lmaydi (tabiiy 404).

DASHBOARD_HOST bo'sh bo'lsa (masalan dev), middleware hech narsa qilmaydi (no-op) —
hammasi bitta `config.urls` da, dashboard `/dashboard/` da.
"""

from django.conf import settings


class HostSeparationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.dashboard_host = (getattr(settings, 'DASHBOARD_HOST', '') or '').lower()

    def __call__(self, request):
        if self.dashboard_host:
            host = request.get_host().split(':')[0].lower()
            if host == self.dashboard_host:
                # Bu host uchun dashboard ildizdagi alohida URLconf.
                request.urlconf = 'config.urls_manage'
        return self.get_response(request)
