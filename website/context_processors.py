from django.conf import settings as django_settings
from .models import SiteSettings


def site_settings(request):
    from website.models import ContactMessage
    unread_count = 0
    if request.user.is_authenticated and request.user.role != 'customer':
        try:
            unread_count = ContactMessage.objects.filter(is_read=False).count()
        except Exception:
            pass

    site = SiteSettings.get()

    # Prepare active social links
    social_links = {}
    if site.telegram_bot_active and site.telegram_bot_url:
        social_links['telegram_bot'] = {
            'url': site.telegram_bot_url,
            'title': site.telegram_bot_title or 'Telegram Bot',
        }
    if site.telegram_channel_active and site.telegram_channel_url:
        social_links['telegram_channel'] = {
            'url': site.telegram_channel_url,
            'title': site.telegram_channel_title or 'Telegram Channel',
        }
    if site.instagram_active and site.instagram_url:
        social_links['instagram'] = {
            'url': site.instagram_url,
            'title': site.instagram_title or 'Instagram',
        }

    # Add to site object
    site.social_links = social_links

    return {
        'site': site,
        'YANDEX_MAPS_API_KEY': getattr(django_settings, 'YANDEX_MAPS_API_KEY', ''),
        'unread_contacts_count': unread_count,
    }
