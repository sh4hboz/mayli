from django.test import TestCase, Client, override_settings
from django.urls import reverse

from website.models import SiteSettings, Feature, StatItem


# ════════════════════════════════════════════════════════════════════
# Context processor testlari
# ════════════════════════════════════════════════════════════════════
class ContextProcessorTests(TestCase):

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        SiteSettings.objects.filter(pk=1).delete()

    def test_site_in_context(self):
        resp = self.client.get(reverse('website:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('site', resp.context)
        self.assertIsInstance(resp.context['site'], SiteSettings)

    def test_why_us_features_in_context(self):
        Feature.objects.create(icon='fa-leaf', title='Test xususiyat', order=0, is_active=True)
        resp = self.client.get(reverse('website:home'))
        self.assertIn('why_us_features', resp.context)
        self.assertEqual(resp.context['why_us_features'].count(), 1)

    def test_inactive_features_excluded(self):
        Feature.objects.create(icon='fa-leaf', title='Faol', order=0, is_active=True)
        Feature.objects.create(icon='fa-trophy', title='Nofaol', order=1, is_active=False)
        resp = self.client.get(reverse('website:home'))
        self.assertEqual(resp.context['why_us_features'].count(), 1)

    def test_hero_stats_in_context(self):
        StatItem.objects.create(value='5+', label='Yil tajriba', placement='hero', order=0, is_active=True)
        StatItem.objects.create(value='200+', label='Taom turi', placement='both', order=1, is_active=True)
        StatItem.objects.create(value='24/7', label='Xizmat', placement='stats', order=2, is_active=True)
        resp = self.client.get(reverse('website:home'))
        self.assertIn('hero_stats', resp.context)
        hero_vals = list(resp.context['hero_stats'].values_list('value', flat=True))
        self.assertIn('5+', hero_vals)
        self.assertIn('200+', hero_vals)
        self.assertNotIn('24/7', hero_vals)

    def test_section_stats_in_context(self):
        StatItem.objects.create(value='5+', label='Yil', placement='hero', order=0, is_active=True)
        StatItem.objects.create(value='24/7', label='Xizmat', placement='stats', order=1, is_active=True)
        StatItem.objects.create(value='200+', label='Taom', placement='both', order=2, is_active=True)
        resp = self.client.get(reverse('website:home'))
        self.assertIn('section_stats', resp.context)
        stats_vals = list(resp.context['section_stats'].values_list('value', flat=True))
        self.assertNotIn('5+', stats_vals)
        self.assertIn('24/7', stats_vals)
        self.assertIn('200+', stats_vals)

    def test_inactive_stats_excluded(self):
        StatItem.objects.create(value='5+', label='Faol', placement='both', order=0, is_active=True)
        StatItem.objects.create(value='999', label='Nofaol', placement='both', order=1, is_active=False)
        resp = self.client.get(reverse('website:home'))
        hero_vals = list(resp.context['hero_stats'].values_list('value', flat=True))
        self.assertNotIn('999', hero_vals)

    def test_features_ordered_by_order_field(self):
        Feature.objects.create(icon='fa-leaf', title='Uchinchi', order=3, is_active=True)
        Feature.objects.create(icon='fa-trophy', title='Birinchi', order=1, is_active=True)
        Feature.objects.create(icon='fa-smile-o', title='Ikkinchi', order=2, is_active=True)
        resp = self.client.get(reverse('website:home'))
        titles = list(resp.context['why_us_features'].values_list('title', flat=True))
        self.assertEqual(titles, ['Birinchi', 'Ikkinchi', 'Uchinchi'])


# ════════════════════════════════════════════════════════════════════
# Sayt sahifalari render testlari
# ════════════════════════════════════════════════════════════════════
class WebsiteRenderTests(TestCase):

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        SiteSettings.objects.filter(pk=1).delete()

    def test_home_renders(self):
        resp = self.client.get(reverse('website:home'))
        self.assertEqual(resp.status_code, 200)

    def test_about_renders(self):
        resp = self.client.get(reverse('website:about'))
        self.assertEqual(resp.status_code, 200)

    def test_menu_renders(self):
        resp = self.client.get(reverse('website:menu'))
        self.assertEqual(resp.status_code, 200)

    def test_news_list_renders(self):
        resp = self.client.get(reverse('website:news_list'))
        self.assertEqual(resp.status_code, 200)


# ════════════════════════════════════════════════════════════════════
# Template DB qiymatlari testlari — DB'dagi matnlar sahifada ko'rinadimi
# ════════════════════════════════════════════════════════════════════
class TemplateDBValuesTests(TestCase):

    def setUp(self):
        self.client = Client(SERVER_NAME='localhost')
        SiteSettings.objects.filter(pk=1).delete()

    def _site(self, **kwargs):
        site = SiteSettings.get()
        for k, v in kwargs.items():
            setattr(site, k, v)
        site.save()
        return site

    # --- Hero ---
    def test_hero_title_from_db(self):
        self._site(hero_title_uz='Maxsus sarlavha')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Maxsus sarlavha')

    def test_hero_accent_from_db(self):
        self._site(hero_title_accent_uz='Oltin qism')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Oltin qism')

    def test_hero_subtitle_from_db(self):
        self._site(hero_subtitle_uz='Maxsus tavsif matni')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Maxsus tavsif matni')

    def test_hero_stats_from_db_in_hero(self):
        StatItem.objects.create(value='999+', label='Test stat', placement='hero', order=0, is_active=True)
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, '999+')
        self.assertContains(resp, 'Test stat')

    def test_hero_stats_fallback_when_empty(self):
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, '5+')

    # --- Why us ---
    def test_why_us_title_from_db(self):
        self._site(why_us_title_uz='Nima uchun bizni tanlash kerak?')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Nima uchun bizni tanlash kerak?')

    def test_why_us_features_from_db(self):
        Feature.objects.create(icon='fa-leaf', title='DB xususiyat', text='DB tavsif', order=0, is_active=True)
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'DB xususiyat')
        self.assertContains(resp, 'DB tavsif')

    def test_why_us_fallback_when_no_features(self):
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Yangi ingredientlar')

    # --- Stats section ---
    def test_stats_section_from_db(self):
        StatItem.objects.create(value='777', label='Test raqam', placement='stats', order=0, is_active=True)
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, '777')

    def test_stats_section_fallback_when_empty(self):
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, "Qo'llab-quvvatlash")

    # --- About teaser ---
    def test_about_title_from_db(self):
        self._site(about_title_uz='Maxsus about sarlavha')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Maxsus about sarlavha')

    def test_about_badge_from_db(self):
        self._site(about_badge_value='20+', about_badge_label_uz='Yillik tajriba')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, '20+')
        self.assertContains(resp, 'Yillik tajriba')

    def test_about_features_from_db_splitlines(self):
        self._site(about_features_uz='Birinchi qator\nIkkinchi qator\nUchinchi qator')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Birinchi qator')
        self.assertContains(resp, 'Ikkinchi qator')
        self.assertContains(resp, 'Uchinchi qator')

    def test_about_features_fallback_when_empty(self):
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Halol va sifatli taomlar')

    # --- Booking CTA ---
    def test_booking_cta_title_from_db(self):
        self._site(booking_cta_title_uz='Joyni hoziroq band qiling')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Joyni hoziroq band qiling')

    def test_booking_cta_desc_from_db(self):
        self._site(booking_cta_desc_uz='Tez va oson bron qiling.')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Tez va oson bron qiling.')

    # --- About page hero ---
    def test_about_page_badge_from_db(self):
        self._site(about_page_badge_uz='Bizning hikoyamiz')
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, 'Bizning hikoyamiz')

    def test_about_page_title_from_db(self):
        self._site(about_page_title_uz='Mayli Restobar tarixi')
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, 'Mayli Restobar tarixi')

    # --- SEO matnlar ---
    def test_home_seo_body_from_db(self):
        self._site(home_seo_body_uz='<h3>SEO sarlavha</h3><p>SEO matn noyob</p>')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'SEO matn noyob')

    def test_home_seo_body_rendered_as_html(self):
        self._site(home_seo_body_uz='<h3>HTML sarlavha</h3>')
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, '<h3>HTML sarlavha</h3>', html=False)

    def test_home_seo_fallback_when_empty(self):
        resp = self.client.get(reverse('website:home'))
        self.assertContains(resp, 'Mayli Restobar')

    def test_about_seo_title_from_db(self):
        self._site(about_seo_title_uz='Noyob about SEO sarlavha')
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, 'Noyob about SEO sarlavha')

    def test_about_seo_body_from_db(self):
        self._site(about_seo_body_uz='<p>About sahifasi noyob matn</p>')
        resp = self.client.get(reverse('website:about'))
        self.assertContains(resp, 'About sahifasi noyob matn')


# ════════════════════════════════════════════════════════════════════
# Model testlari
# ════════════════════════════════════════════════════════════════════
class FeatureModelTests(TestCase):

    def test_str(self):
        f = Feature(title='Test xususiyat', icon='fa-leaf')
        self.assertEqual(str(f), 'Test xususiyat')

    def test_default_icon(self):
        f = Feature.objects.create(title='X', order=0)
        self.assertEqual(f.icon, 'fa-check-circle')

    def test_is_active_default_true(self):
        f = Feature.objects.create(title='X', order=0)
        self.assertTrue(f.is_active)

    def test_ordering_by_order(self):
        Feature.objects.create(title='B', order=2, icon='fa-b')
        Feature.objects.create(title='A', order=1, icon='fa-a')
        first = Feature.objects.first()
        self.assertEqual(first.title, 'A')


class StatItemModelTests(TestCase):

    def test_str(self):
        s = StatItem(value='5+', label='Yil tajriba')
        self.assertIn('5+', str(s))
        self.assertIn('Yil tajriba', str(s))

    def test_placement_choices(self):
        s = StatItem.objects.create(value='5+', label='X', placement='hero', order=0)
        self.assertEqual(s.placement, StatItem.PLACEMENT_HERO)

    def test_default_placement_both(self):
        s = StatItem.objects.create(value='5+', label='X', order=0)
        self.assertEqual(s.placement, 'both')

    def test_is_active_default_true(self):
        s = StatItem.objects.create(value='5+', label='X', order=0)
        self.assertTrue(s.is_active)

    def test_ordering_by_order(self):
        StatItem.objects.create(value='B', label='B', placement='both', order=2)
        StatItem.objects.create(value='A', label='A', placement='both', order=1)
        first = StatItem.objects.first()
        self.assertEqual(first.value, 'A')


class SiteSettingsModelTests(TestCase):

    def setUp(self):
        SiteSettings.objects.filter(pk=1).delete()

    def test_get_creates_singleton(self):
        site = SiteSettings.get()
        self.assertEqual(site.pk, 1)
        site2 = SiteSettings.get()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(site.pk, site2.pk)

    def test_about_features_splitlines(self):
        site = SiteSettings.get()
        site.about_features_uz = 'Birinchi\nIkkinchi\nUchinchi'
        site.save()
        site.refresh_from_db()
        lines = [l.strip() for l in site.about_features_uz.splitlines() if l.strip()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], 'Birinchi')
