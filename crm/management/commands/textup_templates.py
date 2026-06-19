"""
Django management command: textup_templates

TextUp kabinetidagi shablonlar ro'yxatini (templateId bilan) chiqaradi.
Dashboard templateId'ni ko'rsatmaydi — bu buyruq API orqali oladi.

Ishlatish (serverda, .env da TEXTUP_EMAIL/TEXTUP_PASSWORD bo'lishi shart):
    python manage.py textup_templates              # barcha shablonlar
    python manage.py textup_templates --active      # faqat tasdiqlangan (status=active)
"""

from django.core.management.base import BaseCommand
from crm.integrations.textup import TextUpClient, TextUpError


class Command(BaseCommand):
    help = "TextUp shablonlarini (templateId bilan) ro'yxatlaydi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--active', action='store_true',
            help="Faqat status=active (tasdiqlangan) shablonlar",
        )

    def handle(self, *args, **options):
        client = TextUpClient()
        try:
            templates = client.list_templates()
        except TextUpError as e:
            self.stderr.write(self.style.ERROR(f"TextUp xatosi: {e}"))
            return

        if options['active']:
            templates = [t for t in templates if (t.get('status') or '').lower() == 'active']

        if not templates:
            self.stdout.write("Shablon topilmadi.")
            return

        self.stdout.write(self.style.SUCCESS(f"Jami: {len(templates)} ta shablon\n"))
        for t in templates:
            self.stdout.write("-" * 60)
            self.stdout.write(f"templateId : {t.get('id')}")
            self.stdout.write(f"Nomi       : {t.get('name')}")
            self.stdout.write(f"Holat      : {t.get('status')}")
            self.stdout.write(f"Matn       : {t.get('content')}")
        self.stdout.write("─" * 60)
