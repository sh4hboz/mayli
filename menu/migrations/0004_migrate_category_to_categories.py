# Eski yakka `category` FK qiymatlarini yangi `categories` M2M ga ko'chiradi.

from django.db import migrations


def copy_category_to_categories(apps, schema_editor):
    Dish = apps.get_model('menu', 'Dish')
    for dish in Dish.objects.all():
        if dish.category_id:
            dish.categories.add(dish.category_id)


def reverse_copy(apps, schema_editor):
    Dish = apps.get_model('menu', 'Dish')
    for dish in Dish.objects.all():
        first = dish.categories.first()
        if first and not dish.category_id:
            dish.category_id = first.id
            dish.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0003_dish_categories_alter_dish_category'),
    ]

    operations = [
        migrations.RunPython(copy_category_to_categories, reverse_copy),
    ]
