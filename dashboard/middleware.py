from django.shortcuts import redirect
from django.urls import reverse


class LockScreenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.session.get('screen_locked', False):
                if not request.path.startswith('/dashboard/unlock/') and not request.path.startswith('/dashboard/lock/') and not request.path.startswith('/logout/'):
                    return redirect('dashboard_lock_screen')
        response = self.get_response(request)
        return response
