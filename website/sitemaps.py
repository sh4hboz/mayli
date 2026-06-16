from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import News


class StaticViewSitemap(Sitemap):
    """Asosiy statik sahifalar (i18n — har til uchun alohida URL)."""
    i18n = True

    # Sahifaga qarab muhimlik/yangilanish chastotasi
    _config = {
        'website:home': (1.0, 'daily'),
        'website:menu': (0.9, 'weekly'),
        'website:about': (0.7, 'monthly'),
        'website:news_list': (0.8, 'daily'),
        'website:privacy_policy': (0.3, 'yearly'),
        'website:terms_conditions': (0.3, 'yearly'),
    }

    def items(self):
        return list(self._config.keys())

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self._config.get(item, (0.5, 'weekly'))[0]

    def changefreq(self, item):
        return self._config.get(item, (0.5, 'weekly'))[1]


class NewsSitemap(Sitemap):
    """Har bir faol yangilik maqolasi alohida URL sifatida."""
    changefreq = 'monthly'
    priority = 0.6
    i18n = True

    def items(self):
        return News.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('website:news_detail', kwargs={'slug': obj.slug})
