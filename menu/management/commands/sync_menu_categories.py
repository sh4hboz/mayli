"""Menyu kategoriyalarini bosma menyu matniga moslash (UZ/RU/EN).

9 ta aniq kategoriyani yaratadi/yangilaydi (slug bo'yicha), ortiqcha umumiy
kategoriyalarni (Taomlar=food, Gazaklar=dessert) o'chiradi. Ichimliklar va
Kalyan tegmaydi.

    python manage.py sync_menu_categories
    python manage.py sync_menu_categories --dry-run
"""
from django.core.management.base import BaseCommand

from menu.models import Category

# (slug, uz, ru, en, order) — bosma menyu tartibida
CATEGORIES = [
    ('shorvalar',     "Sho'rvalar",     'Супы',             'Soups',      1),
    ('salatlar',      'Salatlar',       'Салаты',           'Salads',     2),
    ('issiq-gazaklar', 'Issiq gazaklar', 'Горячие закуски',  'Hot Snacks', 3),
    ('yaxna-gazaklar', 'Yaxna gazaklar', 'Холодные закуски', 'Cold Snacks', 4),
    ('issiq-taomlar', 'Issiq taomlar',  'Горячие блюда',    'Hot Dishes', 5),
    ('gosht',         "Go'sht",         'Мясо',             'Meat',       6),
    ('garnir',        'Garnir',         'Гарнир',           'Garnish',    7),
    ('yevropa',       'Yevropa',        'Европа',           'Europe',     8),
    ('shashlik',      'Shashlik',       'Шашлык',           'Kebab',      9),
]

# O'chiriladigan ortiqcha umumiy kategoriyalar (slug)
DELETE_SLUGS = ['food', 'dessert']

# Saqlanadigan kategoriyalarni oxiriga surish (slug -> order)
REORDER = {'drink': 10, 'kalyan': 11}


class Command(BaseCommand):
    help = "Menyu kategoriyalarini 3 tilda yaratadi/yangilaydi"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Hech narsa yozmasdan ko'rsatadi")

    def handle(self, *args, **opts):
        dry = opts['dry_run']

        for slug, uz, ru, en, order in CATEGORIES:
            existing = Category.objects.filter(slug=slug).first()
            if dry:
                action = 'yangilanadi' if existing else 'yaratiladi'
                self.stdout.write(f"  {slug}: {uz} / {ru} / {en} — {action}")
                continue
            Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': uz, 'name_uz': uz, 'name_ru': ru, 'name_en': en,
                    'order': order, 'is_active': True,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"  [OK] {slug}: {uz} / {ru} / {en}"))

        # Ortiqcha kategoriyalarni o'chirish
        for slug in DELETE_SLUGS:
            cat = Category.objects.filter(slug=slug).first()
            if not cat:
                continue
            n = cat.dishes.count()
            if dry:
                self.stdout.write(self.style.WARNING(
                    f"  '{cat.name_uz}' (slug={slug}) o'chiriladi — {n} ta taom bog'lanishi uziladi (taomlar o'chmaydi)"))
                continue
            cat.delete()
            self.stdout.write(self.style.WARNING(
                f"  '{slug}' o'chirildi ({n} ta taom bog'lanishi uzildi, taomlar saqlandi)"))

        # Saqlanadigan kategoriyalarni oxiriga surish
        for slug, order in REORDER.items():
            cat = Category.objects.filter(slug=slug).first()
            if not cat:
                continue
            if dry:
                self.stdout.write(f"  '{slug}' tartibi {order} ga o'rnatiladi")
                continue
            if cat.order != order:
                cat.order = order
                cat.save(update_fields=['order'])
                self.stdout.write(f"  '{slug}' tartibi {order} ga o'rnatildi")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Tugadi." if not dry else "Dry-run tugadi."))
