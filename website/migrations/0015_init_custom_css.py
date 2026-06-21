# media/css/ ichidagi tahrirlanadigan custom CSS fayllarini bir marta tayyorlaydi
# (yo'q bo'lsa repo seed'idan ko'chiradi). Ilgari deploy'da har safar
# `python manage.py init_custom_css` ishlatilardi; endi `migrate` buni bir marta
# bajaradi. Fayl mavjud bo'lsa tegmaydi (foydalanuvchi tahrirlarini saqlaydi).
# Qayta seed kerak bo'lsa: `python manage.py init_custom_css --force`.

import os

from django.conf import settings
from django.db import migrations

FILES = ['site.css', 'dashboard.css']


def init_custom_css(apps, schema_editor):
    seed_dir = os.path.join(settings.BASE_DIR, 'dashboard', 'css_seeds')
    target_dir = os.path.join(settings.MEDIA_ROOT, 'css')
    os.makedirs(target_dir, exist_ok=True)

    for name in FILES:
        target = os.path.join(target_dir, name)
        if os.path.exists(target):
            continue
        content = ''
        seed = os.path.join(seed_dir, name)
        if os.path.exists(seed):
            with open(seed, encoding='utf-8') as f:
                content = f.read()
        with open(target, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0014_remove_sitesettings_dashboard_custom_css'),
    ]

    operations = [
        migrations.RunPython(init_custom_css, migrations.RunPython.noop),
    ]
