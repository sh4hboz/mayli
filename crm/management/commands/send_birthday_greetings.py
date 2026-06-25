"""
Django management command: send_birthday_greetings

Bugun tug'ilgan kuni bo'lgan mijozlarga avtomatik SMS tabrik yuboradi
(BirthdayService — bir yilda bir marta, faqat sms_consent=True bo'lganlarga).

Cron / systemd timer orqali har kuni ertalab bir marta ishlatish uchun:
    python manage.py send_birthday_greetings

`--dry-run` — hech narsa yubormay, bugun nechta mijoz tabriklanishini ko'rsatadi.
"""

from django.core.management.base import BaseCommand
from crm.services import BirthdayService


class Command(BaseCommand):
    help = "Bugungi tug'ilgan kunlik mijozlarga SMS tabrik yuboradi (cron uchun)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Yubormay, faqat bugungi tabriklanadiganlar sonini ko\'rsatadi',
        )

    def handle(self, *args, **options):
        if options.get('dry_run'):
            pending = BirthdayService.todays_pending()
            self.stdout.write(f"Bugun tabriklanadigan mijozlar: {pending.count()}")
            for c in pending:
                self.stdout.write(f"  - {c.full_name or c.phone} ({c.phone})")
            return

        result = BirthdayService.congratulate()
        sent, failed = result.get('sent', 0), result.get('failed', 0)

        if not sent and not failed:
            self.stdout.write(self.style.WARNING("Bugun tabriklanadigan mijoz yo'q."))
            return

        self.stdout.write(self.style.SUCCESS(f"✓ Yuborildi: {sent} ta, xato: {failed} ta"))
        for error in result.get('errors', [])[:10]:
            self.stdout.write(self.style.WARNING(f"  - {error}"))
