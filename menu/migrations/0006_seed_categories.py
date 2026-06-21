# Menyu kategoriyalarini (9 ta, 3 tilda) bir marta seed qiladi.
# Ilgari deploy'da har safar `python manage.py sync_menu_categories` ishlatilardi;
# endi shu mantiq migratsiyada — `migrate` uni aynan bir marta qo'llaydi.
# Kategoriya ro'yxati keyin o'zgarsa, yangi migratsiya yoziladi (yoki qo'lda
# `sync_menu_categories` buyrug'i ishlatiladi).

from django.db import migrations

# (slug, uz, ru, en, order) — bosma menyu tartibida
CATEGORIES = [
    ('shorvalar',      "Sho'rvalar",     'Супы',             'Soups',       1),
    ('salatlar',       'Salatlar',       'Салаты',           'Salads',      2),
    ('issiq-gazaklar', 'Issiq gazaklar', 'Горячие закуски',  'Hot Snacks',  3),
    ('yaxna-gazaklar', 'Yaxna gazaklar', 'Холодные закуски', 'Cold Snacks', 4),
    ('issiq-taomlar',  'Issiq taomlar',  'Горячие блюда',    'Hot Dishes',  5),
    ('gosht',          "Go'sht",         'Мясо',             'Meat',        6),
    ('garnir',         'Garnir',         'Гарнир',           'Garnish',     7),
    ('yevropa',        'Yevropa',        'Европа',           'Europe',      8),
    ('shashlik',       'Shashlik',       'Шашлык',           'Kebab',       9),
]

# O'chiriladigan ortiqcha umumiy kategoriyalar (taomlar o'chmaydi, faqat bog'lanish uziladi)
DELETE_SLUGS = ['food', 'dessert']

# Saqlanadigan kategoriyalarni oxiriga surish (slug -> order)
REORDER = {'drink': 10, 'kalyan': 11}


def seed_categories(apps, schema_editor):
    Category = apps.get_model('menu', 'Category')

    for slug, uz, ru, en, order in CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                'name': uz, 'name_uz': uz, 'name_ru': ru, 'name_en': en,
                'order': order, 'is_active': True,
            },
        )

    Category.objects.filter(slug__in=DELETE_SLUGS).delete()

    for slug, order in REORDER.items():
        Category.objects.filter(slug=slug).exclude(order=order).update(order=order)


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0005_alter_dish_options_remove_dish_category'),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
