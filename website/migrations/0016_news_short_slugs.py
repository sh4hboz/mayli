# Mavjud yangiliklarning eski uzun sarlavha-sluglarini qisqa random slug'ga
# o'tkazadi (masalan 'jonli-musiqa-oqshomlari' -> 'k7p2-x9m'). Yangi yangiliklar
# allaqachon save() da random slug oladi. Bir marta `migrate` orqali bajariladi.
# Random format'ga mos sluglarga tegmaydi (idempotent).

import re
import secrets

from django.db import migrations

# website.models._SLUG_ALPHABET ning muzlatilgan nusxasi (migratsiya barqaror bo'lsin)
_SLUG_ALPHABET = 'abcdefghijkmnpqrstuvwxyz23456789'
_SHORT_RE = re.compile(r'^[%s]{4}-[%s]{3}$' % (_SLUG_ALPHABET, _SLUG_ALPHABET))


def _random_slug():
    pick = lambda n: ''.join(secrets.choice(_SLUG_ALPHABET) for _ in range(n))
    return f"{pick(4)}-{pick(3)}"


def shorten_news_slugs(apps, schema_editor):
    News = apps.get_model('website', 'News')
    used = set(News.objects.values_list('slug', flat=True))

    for news in News.objects.all():
        if _SHORT_RE.match(news.slug or ''):
            continue  # allaqachon qisqa random
        used.discard(news.slug)
        slug = _random_slug()
        while slug in used:
            slug = _random_slug()
        used.add(slug)
        news.slug = slug
        news.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0015_init_custom_css'),
    ]

    operations = [
        migrations.RunPython(shorten_news_slugs, migrations.RunPython.noop),
    ]
