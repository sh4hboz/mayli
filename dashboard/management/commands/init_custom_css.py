"""media/css/ ichidagi tahrirlanadigan custom CSS fayllarini tayyorlaydi.

Fayl mavjud bo'lmasa — repo'dagi seed (dashboard/css_seeds/) dan nusxa oladi.
Mavjud bo'lsa tegmaydi (foydalanuvchi tahrirlarini saqlaydi), --force bilan
qayta yozadi. Deploy'da ishga tushiriladi.

    python manage.py init_custom_css
    python manage.py init_custom_css --force
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

FILES = ['dashboard.css', 'site.css']
SEED_DIR = os.path.join(settings.BASE_DIR, 'dashboard', 'css_seeds')


class Command(BaseCommand):
    help = "media/css/ custom CSS fayllarini seed'dan tayyorlaydi (yo'q bo'lsa)"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help="Mavjud bo'lsa ham seed bilan qayta yozadi")

    def handle(self, *args, **opts):
        target_dir = os.path.join(settings.MEDIA_ROOT, 'css')
        os.makedirs(target_dir, exist_ok=True)

        for name in FILES:
            target = os.path.join(target_dir, name)
            if os.path.exists(target) and not opts['force']:
                self.stdout.write(f"  {name}: mavjud, o'tkazib yuborildi")
                continue
            seed = os.path.join(SEED_DIR, name)
            content = ''
            if os.path.exists(seed):
                with open(seed, encoding='utf-8') as f:
                    content = f.read()
            with open(target, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            self.stdout.write(self.style.SUCCESS(f"  {name}: yaratildi ({target})"))

        self.stdout.write(self.style.SUCCESS("Tugadi."))
