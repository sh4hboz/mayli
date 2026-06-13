import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.signing import TimestampSigner

@require_POST
def get_visitor_token(request):
    """
    Mehmon uchun WebSocket ulanishida foydalaniladigan vaqtinchalik imzolangan token yaratish.
    """
    try:
        data = json.loads(request.body)
        visitor_id_str = data.get('visitor_id', '')
        # UUID to'g'riligini tekshirish
        visitor_id = uuid.UUID(visitor_id_str)
    except (ValueError, json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid visitor_id'}, status=400)
    
    signer = TimestampSigner()
    token = signer.sign(str(visitor_id))
    return JsonResponse({'token': token})
