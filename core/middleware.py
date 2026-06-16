"""
core/middleware.py

HostSeparationMiddleware — dashboard va admin'ni alohida subdomenga ajratadi.

Maqsad: `manage.maylirestobar.uz` (DASHBOARD_HOST) orqali dashboard/admin ochiladi;
ommaviy domen (maylirestobar.uz) da esa `/dashboard/` va maxfiy admin URL **404** qaytaradi
— ya'ni tashqaridan topib bo'lmaydi.

DASHBOARD_HOST bo'sh bo'lsa (masalan dev), middleware hech narsa qilmaydi (no-op).
"""

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect


class HostSeparationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.dashboard_host = getattr(settings, 'DASHBOARD_HOST', '') or ''
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')
        # '/admin/' ko'rinishidagi prefiks (boshida slash, oxirida slash)
        self.admin_prefix = '/' + admin_url.lstrip('/')

    def _is_staff_path(self, path):
        return path.startswith('/dashboard/') or path.startswith(self.admin_prefix)

    def __call__(self, request):
        if self.dashboard_host:
            host = request.get_host().split(':')[0].lower()
            on_dashboard_host = (host == self.dashboard_host.lower())

            # Ommaviy domende dashboard/admin yashirin — 404.
            if not on_dashboard_host and self._is_staff_path(request.path):
                raise Http404()

            # manage subdomeniga kirilganda ildiz → to'g'ridan-to'g'ri dashboard.
            if on_dashboard_host and request.path == '/':
                return redirect('/dashboard/')

        return self.get_response(request)
