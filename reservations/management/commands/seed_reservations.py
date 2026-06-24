"""Bron tizimi uchun namunaviy zonalar + stollar seed qiladi (DEV/test uchun).

Idempotent: qayta ishga tushirsa zonalarni yangilaydi, stollarni (zona+raqam
bo'yicha) yaratadi yoki koordinata/sig'imini yangilaydi. **Stol holatini
(free/occupied) qayta ishga tushirishda TEGMAYDI** — manager belgilab qo'ygan
holat saqlanadi.

pos_x/pos_y — abstrakt 1000x640 kanvas (Bosqich 2 ning 2D SVG sxemasi shu
koordinatalardan foydalanadi; Bosqich 3 da admin drag-drop bilan o'zgartiradi).

    python manage.py seed_reservations
    python manage.py seed_reservations --dry-run
"""
from django.core.management.base import BaseCommand

from reservations.models import BookingSettings, Table, TableShape, Zone

# (uz, ru, en, order, shape, [sig'imlar], raqam_prefiks, boshlanish_raqami)
ZONES = [
    ("Hovli",            "Двор",       "Courtyard",  1, TableShape.ROUND,  [2, 2, 4, 4, 6, 6],          'H',    1),
    ("Ayvon",            "Терраса",    "Terrace",    2, TableShape.SQUARE, [4, 4, 4, 6, 6],             'A',    1),
    ("Ichki 1-qavat",    "1-й этаж",   "1st floor",  3, TableShape.SQUARE, [2, 2, 4, 4, 4, 6, 6, 8],    '',   101),
    ("Ichki 2-qavat",    "2-й этаж",   "2nd floor",  4, TableShape.SQUARE, [4, 4, 4, 6, 6, 8],          '',   201),
    ("Maxsus kabinalar", "VIP кабины", "VIP cabins", 5, TableShape.RECT,   [8, 10, 12, 15],             'VIP-', 1),
]


class Command(BaseCommand):
    help = "Namunaviy bron zonalari va stollarini yaratadi (dev/test)"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Hech narsa yozmasdan ko'rsatadi")

    def handle(self, *args, **opts):
        dry = opts['dry_run']

        if not dry:
            BookingSettings.get()  # singleton sozlamalar yaratilsin

        total_tables = 0
        for uz, ru, en, order, shape, caps, prefix, start in ZONES:
            if dry:
                self.stdout.write(f"  Zona: {uz} / {ru} / {en} — {len(caps)} stol")
                total_tables += len(caps)
                continue

            zone, _ = Zone.objects.update_or_create(
                name_uz=uz,
                defaults={'name': uz, 'name_ru': ru, 'name_en': en,
                          'order': order, 'is_active': True},
            )

            # Joylashuv: VIP kabinalar kattaroq → 2 ustun; qolganlari 4 ustun.
            if shape == TableShape.RECT:
                cols, dx, dy, w, h = 2, 360, 180, 150, 90
            else:
                cols, dx, dy, w, h = 4, 210, 160, 72, 72

            created_n = updated_n = 0
            for i, cap in enumerate(caps):
                row, col = divmod(i, cols)
                pos_x = 130 + col * dx
                pos_y = 130 + row * dy
                number = f"{prefix}{start + i}"

                geometry = {
                    'capacity': cap, 'shape': shape,
                    'pos_x': pos_x, 'pos_y': pos_y, 'width': w, 'height': h,
                }
                table, created = Table.objects.get_or_create(
                    zone=zone, number=number,
                    defaults={**geometry, 'is_active': True},
                )
                if created:
                    created_n += 1
                else:
                    # Holatni TEGMAYMIZ — faqat geometriya/sig'imni yangilaymiz.
                    for k, v in geometry.items():
                        setattr(table, k, v)
                    table.save(update_fields=list(geometry.keys()))
                    updated_n += 1

            total_tables += len(caps)
            self.stdout.write(self.style.SUCCESS(
                f"  [OK] {uz}: {len(caps)} stol ({created_n} yangi, {updated_n} yangilandi)"))

        self.stdout.write("")
        if dry:
            self.stdout.write(self.style.SUCCESS(
                f"Dry-run: {len(ZONES)} zona, {total_tables} stol yaratilardi."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Tugadi: {Zone.objects.count()} zona, {Table.objects.count()} stol."))
