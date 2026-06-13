from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'
    i18n = True

    def items(self):
        return ['website:home', 'website:about']

    def location(self, item):
        return reverse(item)
