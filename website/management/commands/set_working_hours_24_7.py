from django.core.management.base import BaseCommand
from website.models import SiteSettings


class Command(BaseCommand):
    help = 'Ish vaqtini 24/7 qiladi'

    def handle(self, *args, **options):
        site = SiteSettings.get()
        site.working_hours = 'Har kuni: 24/7'
        site.working_hours_ru = 'Ежедневно: 24/7'
        site.working_hours_en = 'Daily: 24/7'
        site.save()
        self.stdout.write(
            self.style.SUCCESS(f'SiteSettings yangilandi: {site.working_hours}')
        )
