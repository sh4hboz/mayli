from django.shortcuts import redirect
from django.urls import reverse


class LockScreenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.session.get('screen_locked', False):
            # Aktiv URLconf'ga moslab yo'llarni hisoblaymiz (manage hostda ildizda,
            # dev'da /dashboard/ ostida). request.urlconf'ni HostSeparationMiddleware o'rnatadi.
            urlconf = getattr(request, 'urlconf', None)
            allowed = (
                reverse('dashboard_unlock_screen', urlconf=urlconf),
                reverse('dashboard_lock_screen', urlconf=urlconf),
                reverse('logout', urlconf=urlconf),
            )
            if not any(request.path.startswith(p) for p in allowed):
                return redirect('dashboard_lock_screen')
        return self.get_response(request)
