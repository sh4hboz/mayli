"""
python manage.py set_webhook https://maylirestobar.uz
Telegram botga webhook URL ni ro'yxatdan o'tkazadi.
"""

import json
import urllib.request
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Telegram webhook URL ni botga o'rnatadi"

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='Sayt domain (masalan: https://maylirestobar.uz)',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Webhookni o\'chirish',
        )

    def handle(self, *args, **options):
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        secret = getattr(settings, 'TELEGRAM_WEBHOOK_SECRET', 'changeme')

        if not token:
            self.stderr.write(self.style.ERROR('TELEGRAM_BOT_TOKEN .env da yo\'q!'))
            return

        base = f"https://api.telegram.org/bot{token}"

        if options['delete']:
            url = f"{base}/deleteWebhook"
            payload = {}
            action_msg = "o'chirildi"
        else:
            domain = options['domain'].rstrip('/')
            webhook_url = f"{domain}/telegram/webhook/{secret}/"
            url = f"{base}/setWebhook"
            payload = {
                'url': webhook_url,
                'allowed_updates': ['message', 'callback_query'],
                'drop_pending_updates': True,
                # Telegram har webhook so'rovida shu token'ni header sifatida yuboradi
                # (X-Telegram-Bot-Api-Secret-Token) — view'da tekshiriladi.
                'secret_token': secret,
            }
            action_msg = f"o'rnatildi: {webhook_url}"

        body = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            if data.get('ok'):
                self.stdout.write(self.style.SUCCESS(f'Webhook {action_msg}'))
            else:
                self.stderr.write(self.style.ERROR(f"Telegram xatosi: {data.get('description')}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'So\'rov xatosi: {e}'))
