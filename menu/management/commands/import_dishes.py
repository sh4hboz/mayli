"""Rasmlar papkasidan taomlarni ommaviy import qilish.

Raqamlangan rasmlardan (1.JPG ... 90.JPG) placeholder nom va narx bilan
Dish yozuvlarini yaratadi. Keyin ofitsiant dashboard orqali har biriga
to'g'ri nom va narxni yozib chiqadi.

Misol:
    python manage.py import_dishes --dir /srv/menu --start 23 --end 90
"""
import os

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from dashboard.image_utils import convert_image_to_webp
from menu.models import Dish

# Bir xil raqam uchun ko'rib chiqiladigan kengaytmalar (tartib muhim)
EXTENSIONS = ['.JPG', '.jpg', '.jpeg', '.JPEG', '.png', '.PNG']


class Command(BaseCommand):
    help = "Raqamlangan rasmlar papkasidan taomlarni placeholder bilan import qiladi"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir', required=True,
            help="Rasmlar joylashgan papka (masalan /srv/menu yoki D:\\menu)",
        )
        parser.add_argument('--start', type=int, default=23, help="Boshlang'ich raqam (standart 23)")
        parser.add_argument('--end', type=int, default=90, help="Oxirgi raqam (standart 90)")
        parser.add_argument(
            '--name-prefix', default='Taom',
            help="Placeholder nom prefiksi (standart 'Taom' -> 'Taom 23')",
        )
        parser.add_argument(
            '--price', default='0',
            help="Placeholder narx (standart 0)",
        )
        parser.add_argument(
            '--no-webp', action='store_true',
            help="Rasmlarni WebP'ga aylantirmaslik (asl JPG holatida saqlash)",
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Hech narsa yozmasdan nima qilinishini ko'rsatadi",
        )

    def handle(self, *args, **opts):
        directory = opts['dir']
        start, end = opts['start'], opts['end']
        prefix = opts['name_prefix']
        price = opts['price']
        use_webp = not opts['no_webp']
        dry = opts['dry_run']

        if not os.path.isdir(directory):
            raise CommandError(f"Papka topilmadi: {directory}")

        created, skipped, missing = 0, 0, []

        for n in range(start, end + 1):
            path = self._find_image(directory, n)
            if not path:
                missing.append(n)
                self.stdout.write(self.style.WARNING(f"  #{n}: rasm topilmadi, o'tkazib yuborildi"))
                continue

            name = f"{prefix} {n}"
            if Dish.objects.filter(name=name).exists():
                skipped += 1
                self.stdout.write(f"  #{n}: '{name}' allaqachon mavjud, o'tkazib yuborildi")
                continue

            filename = os.path.basename(path)
            if dry:
                self.stdout.write(f"  #{n}: '{name}' yaratiladi <- {filename}")
                created += 1
                continue

            dish = Dish(name=name, price=price, is_available=False, is_active=False)
            with open(path, 'rb') as fh:
                src = File(fh, name=filename)
                if use_webp:
                    result = convert_image_to_webp(src)
                    out_file, save_name = result['file'], result['file'].name
                    if result['used_webp']:
                        note = f"webp (-{result['saved_pct']}%)"
                    else:
                        note = f"asl ({result['reason']})"
                else:
                    out_file, save_name, note = src, filename, "asl"
                dish.image.save(save_name, out_file, save=False)
            dish.save()
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  #{n}: '{name}' yaratildi <- {filename} [{note}]"))

        self.stdout.write("")
        verb = "yaratiladi" if dry else "yaratildi"
        self.stdout.write(self.style.SUCCESS(f"Jami {created} ta taom {verb}."))
        if skipped:
            self.stdout.write(f"{skipped} ta allaqachon mavjud edi (o'tkazib yuborildi).")
        if missing:
            self.stdout.write(self.style.WARNING(f"Rasmi topilmaganlar: {missing}"))

    @staticmethod
    def _find_image(directory, n):
        for ext in EXTENSIONS:
            candidate = os.path.join(directory, f"{n}{ext}")
            if os.path.isfile(candidate):
                return candidate
        return None
