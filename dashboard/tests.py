import tempfile
from io import BytesIO
from datetime import date

from django.test import TestCase, RequestFactory, override_settings, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied

from accounts.models import Role, StaffProfile
from dashboard.views import NewsListView, NewsCreateView
from restobar.views import staff_permissions_view

from website.models import (
    News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage,
    SiteSettings, Feature, StatItem,
)
from menu.models import Category, Dish
from crm.models import Customer, Campaign
from notifications.models import ChatSession, ChatMessage
from orders.models import Order

User = get_user_model()

from PIL import Image

MEDIA = tempfile.mkdtemp(prefix='mayli-test-media-')


def _img(name='t.png'):
    """Kichik haqiqiy PNG — ImageField testlari uchun."""
    buf = BytesIO()
    Image.new('RGB', (10, 10), (234, 105, 0)).save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


# ════════════════════════════════════════════════════════════════════
# Mavjud: CMS ruxsat (permission) testlari
# ════════════════════════════════════════════════════════════════════
class CMSPermissionsTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.superadmin = User.objects.create_user(
            username='owner1', password='password123',
            role=Role.OWNER, full_name='Owner Super',
        )
        self.waiter = User.objects.create_user(
            username='waiter1', password='password123',
            role=Role.WAITER, full_name='Ali Waiter',
        )
        StaffProfile.objects.create(user=self.waiter, role=Role.WAITER)
        self.accountant = User.objects.create_user(
            username='accountant1', password='password123',
            role=Role.ACCOUNTANT, full_name='Vali Accountant',
        )
        StaffProfile.objects.create(user=self.accountant, role=Role.ACCOUNTANT)

    def test_waiter_cannot_access_cms(self):
        """Ofitsiant CMS bo'limlariga kira olmasligi (PermissionDenied)."""
        request = self.factory.get('/dashboard/website/news/')
        request.user = self.waiter
        with self.assertRaises(PermissionDenied):
            NewsListView.as_view()(request)

    def test_superadmin_can_manage_staff_permissions(self):
        view_news_perm = Permission.objects.get(codename='view_news', content_type__app_label='website')
        request = self.factory.post(
            f'/staff/{self.waiter.id}/permissions/',
            {'permissions': [view_news_perm.id]},
        )
        request.user = self.superadmin
        response = staff_permissions_view(request, user_id=self.waiter.id)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(id=self.waiter.id).has_perm('website.view_news'))


# ════════════════════════════════════════════════════════════════════
# Sahifa render (smoke) testlari — barcha GET sahifalari 200 qaytaradimi
# ════════════════════════════════════════════════════════════════════
@override_settings(MEDIA_ROOT=MEDIA)
class DashboardRenderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='render_owner', password='pass12345',
            role=Role.OWNER, full_name='Render Owner',
        )
        cls.news = News.objects.create(title='Test yangilik', body='Matn')
        cls.promo = Promotion.objects.create(title='Test aksiya')
        cls.gallery = GalleryItem.objects.create(image=_img('g.png'), caption='galereya')
        cls.vacancy = Vacancy.objects.create(title='Ofitsiant', description='tavsif')
        cls.application = JobApplication.objects.create(
            vacancy=cls.vacancy, full_name='Ali Valiyev', phone='+998901112233',
        )
        cls.contact = ContactMessage.objects.create(
            name='Mehmon', phone='+998901112244', message='Salom', kind='message',
        )
        cls.category = Category.objects.create(name='Issiq taomlar', slug='test-issiq-taomlar')
        cls.dish = Dish.objects.create(name='Lag\'mon', price=30000)
        cls.dish.categories.add(cls.category)
        cls.customer = Customer.objects.create(first_name='Dilshod', phone='+998901112255')
        cls.campaign = Campaign.objects.create(
            name='Bayram', channel='sms', template='Salom {{first_name}}',
        )
        cls.feature = Feature.objects.create(
            icon='fa-leaf', title='Yangi ingredientlar', text='Tavsif', order=0,
        )
        cls.statitem = StatItem.objects.create(
            value='5+', label='Yil tajriba', placement='both', order=0,
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_all_get_pages_render(self):
        routes = [
            ('dashboard_home', {}),
            ('dashboard_settings_website', {}),
            ('dashboard_settings_location', {}),
            ('dashboard_settings_hero', {}),
            ('dashboard_settings_home', {}),
            ('dashboard_settings_seo', {}),
            ('dashboard_custom_css', {}),
            ('dashboard_news_list', {}),
            ('dashboard_news_create', {}),
            ('dashboard_news_edit', {'pk': self.news.pk}),
            ('dashboard_promotion_list', {}),
            ('dashboard_promotion_create', {}),
            ('dashboard_promotion_edit', {'pk': self.promo.pk}),
            ('dashboard_gallery_list', {}),
            ('dashboard_gallery_create', {}),
            ('dashboard_partner_list', {}),
            ('dashboard_partner_create', {}),
            ('dashboard_vacancy_list', {}),
            ('dashboard_vacancy_create', {}),
            ('dashboard_vacancy_edit', {'pk': self.vacancy.pk}),
            ('dashboard_application_list', {}),
            ('dashboard_application_detail', {'pk': self.application.pk}),
            ('dashboard_contact_list', {}),
            ('dashboard_contact_detail', {'pk': self.contact.pk}),
            ('dashboard_category_list', {}),
            ('dashboard_category_create', {}),
            ('dashboard_category_edit', {'pk': self.category.pk}),
            ('dashboard_dish_list', {}),
            ('dashboard_dish_create', {}),
            ('dashboard_dish_edit', {'pk': self.dish.pk}),
            ('dashboard_customer_list', {}),
            ('dashboard_customer_create', {}),
            ('dashboard_customer_detail', {'pk': self.customer.pk}),
            ('dashboard_customer_edit', {'pk': self.customer.pk}),
            ('dashboard_campaign_list', {}),
            ('dashboard_campaign_create', {}),
            ('dashboard_campaign_detail', {'pk': self.campaign.pk}),
            ('dashboard_campaign_edit', {'pk': self.campaign.pk}),
            ('dashboard_feature_list', {}),
            ('dashboard_feature_create', {}),
            ('dashboard_feature_edit', {'pk': self.feature.pk}),
            ('dashboard_statitem_list', {}),
            ('dashboard_statitem_create', {}),
            ('dashboard_statitem_edit', {'pk': self.statitem.pk}),
            ('dashboard_lock_screen', {}),
        ]
        for name, kwargs in routes:
            with self.subTest(route=name):
                resp = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(resp.status_code, 200, f'{name} -> {resp.status_code}')

    def test_customer_list_filters(self):
        url = reverse('dashboard_customer_list')
        resp = self.client.get(url, {'q': 'Dilshod', 'gender': 'male', 'birth_month': '5'})
        self.assertEqual(resp.status_code, 200)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse('dashboard_news_list'))
        self.assertEqual(resp.status_code, 302)  # login'ga redirect


# ════════════════════════════════════════════════════════════════════
# Forma yuborish (POST create) testlari — formalar to'g'ri ishlaydimi
# ════════════════════════════════════════════════════════════════════
@override_settings(MEDIA_ROOT=MEDIA)
class DashboardFormSubmitTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='submit_owner', password='pass12345',
            role=Role.OWNER, full_name='Submit Owner',
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_news(self):
        resp = self.client.post(reverse('dashboard_news_create'), {
            'title_uz': 'Yangi', 'body_uz': 'Tana matn', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(News.objects.filter(title='Yangi').exists())

    def test_create_promotion(self):
        resp = self.client.post(reverse('dashboard_promotion_create'), {
            'title_uz': 'Aksiya', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Promotion.objects.filter(title='Aksiya').exists())

    def test_create_gallery(self):
        resp = self.client.post(reverse('dashboard_gallery_create'), {
            'caption_uz': 'Rasm', 'order': '0', 'is_active': 'on', 'image': _img('new.png'),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(GalleryItem.objects.count(), 1)

    def test_save_custom_css(self):
        import os
        css_site = '.dish-card { border-radius: 16px; }'
        css_dash = '.dish-thumb { border-radius: 12px; }'
        with tempfile.TemporaryDirectory() as tmp:
            with override_settings(MEDIA_ROOT=tmp):
                resp = self.client.post(reverse('dashboard_custom_css'), {
                    'site_css': css_site, 'dashboard_css': css_dash,
                })
                self.assertEqual(resp.status_code, 302)
                # Fayllarga yozilgan bo'lishi kerak
                with open(os.path.join(tmp, 'css', 'site.css'), encoding='utf-8') as f:
                    self.assertEqual(f.read(), css_site)
                with open(os.path.join(tmp, 'css', 'dashboard.css'), encoding='utf-8') as f:
                    self.assertEqual(f.read(), css_dash)
                # Tahrirlash sahifasida qayta ko'rinishi kerak
                page = self.client.get(reverse('dashboard_custom_css'))
                self.assertContains(page, css_dash)

    def test_create_partner(self):
        from website.models import Partner
        resp = self.client.post(reverse('dashboard_partner_create'), {
            'name': 'ACME', 'url': '', 'order': '0', 'is_active': 'on', 'logo': _img('p.png'),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Partner.objects.count(), 1)

    def test_create_vacancy(self):
        resp = self.client.post(reverse('dashboard_vacancy_create'), {
            'title_uz': 'Barmen', 'description_uz': 'Tavsif', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Vacancy.objects.filter(title='Barmen').exists())

    def test_create_category(self):
        resp = self.client.post(reverse('dashboard_category_create'), {
            'name_uz': 'Mantilar', 'order': '0', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Category.objects.filter(name='Mantilar').exists())

    def test_create_dish(self):
        cat = Category.objects.create(name='Ichimliklar')
        resp = self.client.post(reverse('dashboard_dish_create'), {
            'name_uz': 'Choy', 'price': '8000', 'prep_time': '5',
            'categories': [cat.pk], 'is_available': 'on', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Dish.objects.filter(name='Choy').exists())

    def test_create_customer(self):
        resp = self.client.post(reverse('dashboard_customer_create'), {
            'first_name': 'Aziz', 'phone': '+998901230001', 'source': 'walk_in',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Customer.objects.filter(phone='+998901230001').exists())

    def test_create_campaign(self):
        # SMS yuborgich (yangi): nom + shablon + raqamlar + vaqt. "schedule" — yuborishni chaqirmaydi.
        resp = self.client.post(reverse('dashboard_campaign_create'), {
            'name': 'Yangi yil',
            'sms_template_id': 'tpl-123',
            'template': 'Tabriklaymiz!',
            'recipients_raw': '+998901112233',
            'when': 'schedule',
            'scheduled_at': '2030-01-01T09:00',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Campaign.objects.filter(name='Yangi yil').exists())

    def test_update_customer(self):
        c = Customer.objects.create(first_name='Old', phone='+998901230002')
        resp = self.client.post(reverse('dashboard_customer_edit', kwargs={'pk': c.pk}), {
            'first_name': 'New', 'phone': '+998901230002', 'source': 'walk_in', 'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.first_name, 'New')

    def test_delete_news_post(self):
        n = News.objects.create(title='O\'chiriladi', body='x')
        resp = self.client.post(reverse('dashboard_news_delete', kwargs={'pk': n.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(News.objects.filter(pk=n.pk).exists())

    def test_contact_toggle_read_ajax(self):
        m = ContactMessage.objects.create(name='X', message='y', is_read=False)
        resp = self.client.post(reverse('dashboard_contact_toggle_read', kwargs={'pk': m.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')

    def test_toggle_active_ajax(self):
        d = Dish.objects.create(name='Toggle', price=1000, is_active=True)
        url = reverse('dashboard_toggle_active', kwargs={
            'app_label': 'menu', 'model_name': 'dish', 'pk': d.pk,
        })
        resp = self.client.post(url + '?field=is_active')
        self.assertEqual(resp.status_code, 200)
        d.refresh_from_db()
        self.assertFalse(d.is_active)


# ════════════════════════════════════════════════════════════════════
# Kampaniya yuborish view'lari (TextUp SMS) — provider mock bilan
# ════════════════════════════════════════════════════════════════════
from unittest.mock import patch


class CampaignSendViewTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1', password='pass12345', role=Role.OWNER, full_name='Ega',
        )
        self.client.force_login(self.owner)
        self.customer = Customer.objects.create(
            first_name='Ali', phone='+998901112233', sms_consent=True, is_active=True,
        )
        self.campaign = Campaign.objects.create(
            name='SMS test', channel='sms', template='Salom {{first_name}}',
            send_to_all_customers=True,
        )

    @patch('crm.services.get_provider')
    def test_test_send_redirects_with_message(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': True, 'error': None}
        url = reverse('dashboard_campaign_test_send', kwargs={'pk': self.campaign.pk})
        resp = self.client.post(url)
        self.assertRedirects(
            resp, reverse('dashboard_campaign_detail', kwargs={'pk': self.campaign.pk}),
            fetch_redirect_response=False,
        )

    @patch('crm.services.get_provider')
    def test_send_all_creates_logs(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': True, 'error': None}
        url = reverse('dashboard_campaign_send', kwargs={'pk': self.campaign.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.sent_count, 1)

    def test_send_requires_post(self):
        url = reverse('dashboard_campaign_send', kwargs={'pk': self.campaign.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 405)


# ════════════════════════════════════════════════════════════════════
# Feature CRUD testlari
# ════════════════════════════════════════════════════════════════════
class FeatureCRUDTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='feat_owner', password='pass12345',
            role=Role.OWNER, full_name='Feature Owner',
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_feature(self):
        resp = self.client.post(reverse('dashboard_feature_create'), {
            'icon': 'fa-leaf',
            'title_uz': 'Yangi ingredientlar',
            'title_ru': 'Свежие ингредиенты',
            'title_en': 'Fresh ingredients',
            'text_uz': 'Tavsif matni',
            'order': '0',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('dashboard_feature_list'), fetch_redirect_response=False)
        self.assertTrue(Feature.objects.filter(title='Yangi ingredientlar').exists())

    def test_create_feature_invalid_missing_icon(self):
        resp = self.client.post(reverse('dashboard_feature_create'), {
            'icon': '',
            'title_uz': 'Sarlavha',
            'order': '0',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Feature.objects.exists())

    def test_update_feature(self):
        f = Feature.objects.create(icon='fa-leaf', title='Eski nom', order=0)
        resp = self.client.post(reverse('dashboard_feature_edit', kwargs={'pk': f.pk}), {
            'icon': 'fa-trophy',
            'title_uz': 'Yangi nom',
            'order': '1',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        f.refresh_from_db()
        self.assertEqual(f.title_uz, 'Yangi nom')
        self.assertEqual(f.icon, 'fa-trophy')
        self.assertEqual(f.order, 1)

    def test_delete_feature(self):
        f = Feature.objects.create(icon='fa-leaf', title='O\'chiriladi', order=0)
        resp = self.client.post(reverse('dashboard_feature_delete', kwargs={'pk': f.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Feature.objects.filter(pk=f.pk).exists())

    def test_toggle_active_feature(self):
        f = Feature.objects.create(icon='fa-leaf', title='Toggle', is_active=True, order=0)
        url = reverse('dashboard_toggle_active', kwargs={
            'app_label': 'website', 'model_name': 'feature', 'pk': f.pk,
        })
        resp = self.client.post(url + '?field=is_active')
        self.assertEqual(resp.status_code, 200)
        f.refresh_from_db()
        self.assertFalse(f.is_active)

    def test_feature_list_shows_items(self):
        Feature.objects.create(icon='fa-leaf', title_uz='Yangi xususiyat', order=0)
        resp = self.client.get(reverse('dashboard_feature_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Yangi xususiyat')

    def test_feature_order_preserved(self):
        Feature.objects.create(icon='fa-leaf', title='Birinchi', order=1)
        Feature.objects.create(icon='fa-trophy', title='Ikkinchi', order=2)
        Feature.objects.create(icon='fa-smile-o', title='Uchinchi', order=0)
        qs = list(Feature.objects.order_by('order').values_list('title', flat=True))
        self.assertEqual(qs[0], 'Uchinchi')

    def test_anon_redirected(self):
        self.client.logout()
        resp = self.client.get(reverse('dashboard_feature_list'))
        self.assertEqual(resp.status_code, 302)

    def test_waiter_cannot_access(self):
        waiter = User.objects.create_user(
            username='feat_waiter', password='pass', role=Role.WAITER,
        )
        self.client.force_login(waiter)
        from django.core.exceptions import PermissionDenied
        from dashboard.views import FeatureListView
        from django.test import RequestFactory
        factory = RequestFactory()
        req = factory.get('/dashboard/website/features/')
        req.user = waiter
        with self.assertRaises(PermissionDenied):
            FeatureListView.as_view()(req)


# ════════════════════════════════════════════════════════════════════
# StatItem CRUD testlari
# ════════════════════════════════════════════════════════════════════
class StatItemCRUDTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='stat_owner', password='pass12345',
            role=Role.OWNER, full_name='Stat Owner',
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_statitem(self):
        resp = self.client.post(reverse('dashboard_statitem_create'), {
            'value': '200+',
            'label_uz': 'Taom turi',
            'label_ru': 'Видов блюд',
            'label_en': 'Dish types',
            'placement': 'both',
            'order': '0',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('dashboard_statitem_list'), fetch_redirect_response=False)
        self.assertTrue(StatItem.objects.filter(value='200+').exists())

    def test_create_statitem_hero_only(self):
        resp = self.client.post(reverse('dashboard_statitem_create'), {
            'value': '100%',
            'label_uz': 'Sifat kafolati',
            'placement': 'hero',
            'order': '3',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        s = StatItem.objects.get(value='100%')
        self.assertEqual(s.placement, 'hero')

    def test_create_statitem_stats_only(self):
        resp = self.client.post(reverse('dashboard_statitem_create'), {
            'value': '24/7',
            'label_uz': 'Qo\'llab-quvvatlash',
            'placement': 'stats',
            'order': '3',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        s = StatItem.objects.get(value='24/7')
        self.assertEqual(s.placement, 'stats')

    def test_create_statitem_invalid_no_value(self):
        resp = self.client.post(reverse('dashboard_statitem_create'), {
            'label_uz': 'Yorliq',
            'placement': 'both',
            'order': '0',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(StatItem.objects.exists())

    def test_update_statitem(self):
        s = StatItem.objects.create(value='5+', label='Yil tajriba', placement='both', order=0)
        resp = self.client.post(reverse('dashboard_statitem_edit', kwargs={'pk': s.pk}), {
            'value': '10+',
            'label_uz': 'Yil tajriba',
            'placement': 'hero',
            'order': '0',
            'is_active': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.value, '10+')
        self.assertEqual(s.placement, 'hero')

    def test_delete_statitem(self):
        s = StatItem.objects.create(value='999', label='O\'chiriladi', placement='both', order=0)
        resp = self.client.post(reverse('dashboard_statitem_delete', kwargs={'pk': s.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(StatItem.objects.filter(pk=s.pk).exists())

    def test_toggle_active_statitem(self):
        s = StatItem.objects.create(value='5+', label='Yil tajriba', placement='both', is_active=True, order=0)
        url = reverse('dashboard_toggle_active', kwargs={
            'app_label': 'website', 'model_name': 'statitem', 'pk': s.pk,
        })
        resp = self.client.post(url + '?field=is_active')
        self.assertEqual(resp.status_code, 200)
        s.refresh_from_db()
        self.assertFalse(s.is_active)

    def test_statitem_list_shows_items(self):
        StatItem.objects.create(value='5+', label='Yil tajriba', placement='both', order=0)
        resp = self.client.get(reverse('dashboard_statitem_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '5+')
        self.assertContains(resp, 'Yil tajriba')

    def test_placement_badge_in_list(self):
        StatItem.objects.create(value='5+', label='Hero stat', placement='hero', order=0)
        StatItem.objects.create(value='24/7', label='Stats stat', placement='stats', order=1)
        StatItem.objects.create(value='200+', label='Both stat', placement='both', order=2)
        resp = self.client.get(reverse('dashboard_statitem_list'))
        self.assertContains(resp, 'Hero')
        self.assertContains(resp, 'Stats')
        self.assertContains(resp, 'Ikkalasi')


# ════════════════════════════════════════════════════════════════════
# SiteSettings yangi maydonlar testlari
# ════════════════════════════════════════════════════════════════════
class SiteSettingsNewFieldsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username='settings_owner', password='pass12345',
            role=Role.OWNER, full_name='Settings Owner',
        )

    def setUp(self):
        self.client.force_login(self.owner)
        SiteSettings.objects.filter(pk=1).delete()

    # Sozlamalar 5 ta alohida bo'limga bo'lingan — har test o'z bo'limiga POST qiladi.

    def test_general_settings_saved(self):
        # 1-bo'lim: Asosiy / Kontakt. `name` majburiy.
        resp = self.client.post(reverse('dashboard_settings_website'), {
            'name': 'Mayli Restobar',
            'email': 'info@mayli.uz',
            'phone_main': '+998 90 000 00 00',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.name, 'Mayli Restobar')
        self.assertEqual(site.email, 'info@mayli.uz')

    def test_location_settings_saved(self):
        # 2-bo'lim: Manzil. `city`, `latitude`, `longitude` majburiy.
        resp = self.client.post(reverse('dashboard_settings_location'), {
            'city': 'Termiz',
            'latitude': '37.224', 'longitude': '67.278',
            'address_uz': 'Termiz sh., Mustaqillik 1',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.city, 'Termiz')
        self.assertEqual(site.address_uz, 'Termiz sh., Mustaqillik 1')

    def test_location_city_required(self):
        # `city` bo'sh bo'lsa forma yiqiladi (300 emas, 200 qayta render).
        resp = self.client.post(reverse('dashboard_settings_location'), {
            'city': '',
            'latitude': '37.224', 'longitude': '67.278',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('city', resp.context['form'].errors)

    def test_hero_fields_saved(self):
        resp = self.client.post(reverse('dashboard_settings_hero'), {
            'hero_title_uz': 'Mazali ta\'mlar',
            'hero_title_accent_uz': 'Unutilmas lahzalar',
            'hero_subtitle_uz': 'Termiz shahridagi eng shinam maskan',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.hero_title_uz, 'Mazali ta\'mlar')
        self.assertEqual(site.hero_title_accent_uz, 'Unutilmas lahzalar')
        self.assertEqual(site.hero_subtitle_uz, 'Termiz shahridagi eng shinam maskan')

    def test_about_page_hero_fields_saved(self):
        # "Biz haqimizda" sahifasi hero endi Hero bo'limida.
        resp = self.client.post(reverse('dashboard_settings_hero'), {
            'about_page_badge_uz': 'Biz haqimizda',
            'about_page_title_uz': 'Mayli Restobar',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.about_page_badge_uz, 'Biz haqimizda')
        self.assertEqual(site.about_page_title_uz, 'Mayli Restobar')

    def test_why_us_title_saved(self):
        resp = self.client.post(reverse('dashboard_settings_home'), {
            'why_us_title_uz': 'Nima uchun biz?',
            'why_us_title_ru': 'Почему мы?',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.why_us_title_uz, 'Nima uchun biz?')
        self.assertEqual(site.why_us_title_ru, 'Почему мы?')

    def test_about_teaser_fields_saved(self):
        resp = self.client.post(reverse('dashboard_settings_home'), {
            'about_title_uz': 'Biz haqimizda',
            'about_badge_value': '10+',
            'about_badge_label_uz': 'Yil tajriba',
            'about_features_uz': 'Halol taomlar\nPremium kalyan\nXususiy zal',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.about_title_uz, 'Biz haqimizda')
        self.assertEqual(site.about_badge_value, '10+')
        self.assertEqual(site.about_badge_label_uz, 'Yil tajriba')
        self.assertIn('Halol taomlar', site.about_features_uz)

    def test_booking_cta_fields_saved(self):
        resp = self.client.post(reverse('dashboard_settings_home'), {
            'booking_cta_title_uz': 'Joyni band qiling',
            'booking_cta_desc_uz': 'Bir necha soniyada bron qiling.',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.booking_cta_title_uz, 'Joyni band qiling')
        self.assertEqual(site.booking_cta_desc_uz, 'Bir necha soniyada bron qiling.')

    def test_seo_content_fields_saved(self):
        seo_body = '<h3>Sarlavha</h3><p>Matn</p>'
        resp = self.client.post(reverse('dashboard_settings_seo'), {
            'home_seo_body_uz': seo_body,
            'about_seo_title_uz': 'About SEO sarlavha',
            'about_seo_body_uz': '<p>About matni</p>',
        })
        self.assertEqual(resp.status_code, 302)
        site = SiteSettings.get()
        self.assertEqual(site.home_seo_body_uz, seo_body)
        self.assertEqual(site.about_seo_title_uz, 'About SEO sarlavha')
        self.assertEqual(site.about_seo_body_uz, '<p>About matni</p>')


# ════════════════════════════════════════════════════════════════════
# Sayt chat — dashboarddan javob berish
# ════════════════════════════════════════════════════════════════════
class ChatDashboardTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='chatowner', password='pw12345',
            role=Role.OWNER, full_name='Chat Owner',
        )
        self.client.login(username='chatowner', password='pw12345')
        self.session = ChatSession.objects.create(visitor_id='visitor-xyz', lang='uz')
        ChatMessage.objects.create(
            session=self.session, direction=ChatMessage.IN, text='Salom, stol bormi?',
        )

    def test_chat_list_and_detail_open(self):
        self.assertEqual(self.client.get(reverse('dashboard_chat_list')).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('dashboard_chat_detail', args=[self.session.pk])).status_code, 200,
        )

    def test_reply_creates_outbound_message(self):
        resp = self.client.post(
            reverse('dashboard_chat_reply', args=[self.session.pk]), {'text': 'Ha, bor!'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            self.session.messages.filter(direction=ChatMessage.OUT, text='Ha, bor!').exists()
        )

    def test_customer_poll_receives_dashboard_reply(self):
        """Dashboarddan yozilgan javobni mijozning /chat/poll/ si oladi."""
        self.client.post(reverse('dashboard_chat_reply', args=[self.session.pk]), {'text': 'Javob matni'})
        resp = Client().get(reverse('website:chat_poll'), {'visitor_id': 'visitor-xyz', 'after': 0})
        texts = [m['text'] for m in resp.json().get('messages', [])]
        self.assertIn('Javob matni', texts)

    def test_messages_poll_json(self):
        resp = self.client.get(reverse('dashboard_chat_messages', args=[self.session.pk]), {'after': 0})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['direction'], 'in')

    def test_waiter_cannot_reply(self):
        User.objects.create_user(
            username='chatwaiter', password='pw12345', role=Role.WAITER, full_name='W',
        )
        c = Client()
        c.login(username='chatwaiter', password='pw12345')
        # PermissionDenied → Django 403 javob (Client exception'ni 403 ga aylantiradi).
        resp = c.post(reverse('dashboard_chat_reply', args=[self.session.pk]), {'text': 'x'})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(self.session.messages.filter(direction=ChatMessage.OUT).exists())


# ════════════════════════════════════════════════════════════════════
# Topbar global qidiruv (dashboard/search.py + dashboard_search view)
# ════════════════════════════════════════════════════════════════════
class GlobalSearchTests(TestCase):
    """Topilish (telefon/ism/#id/matn), rol filtri, limit va auth."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='search_owner', password='pw12345', role=Role.OWNER, full_name='Owner S',
        )
        self.waiter = User.objects.create_user(
            username='search_waiter', password='pw12345', role=Role.WAITER, full_name='Waiter S',
        )
        self.url = reverse('dashboard_search')

        self.order = Order.objects.create(
            customer_name='Alisher Karimov', phone='+998901234567', total_amount=50000,
        )
        Customer.objects.create(first_name='Bobur', last_name='Aliyev', phone='+998901112233')
        Dish.objects.create(name='Osh palov', price=30000)
        Campaign.objects.create(name='Yangi yil aksiya', channel='sms', template='Salom')
        ContactMessage.objects.create(
            name='Sardor Test', phone='+998905556677', message='Salom murojaat',
        )
        session = ChatSession.objects.create(visitor_id='visitor-abc-123')
        ChatMessage.objects.create(
            session=session, direction=ChatMessage.IN, text='qachon ochiqsiz',
        )

    def _login_owner(self):
        self.client.login(username='search_owner', password='pw12345')

    def _labels(self, resp):
        return [g['label'] for g in resp.json()['results']]

    def test_requires_login(self):
        """Login'siz → 302/403."""
        resp = self.client.get(self.url, {'q': 'Ali'})
        self.assertIn(resp.status_code, (302, 403))

    def test_waiter_forbidden(self):
        """Ruxsatsiz rol (ofitsiant) → 403."""
        self.client.login(username='search_waiter', password='pw12345')
        resp = self.client.get(self.url, {'q': 'Ali'})
        self.assertEqual(resp.status_code, 403)

    def test_phone_finds_order(self):
        self._login_owner()
        resp = self.client.get(self.url, {'q': '9012345'})
        self.assertIn('Buyurtmalar', self._labels(resp))

    def test_name_finds_customer_and_dish(self):
        self._login_owner()
        self.assertIn('Mijozlar', self._labels(self.client.get(self.url, {'q': 'Bobur'})))
        self.assertIn('Taomlar', self._labels(self.client.get(self.url, {'q': 'palov'})))

    def test_contact_and_chat(self):
        self._login_owner()
        self.assertIn('Murojaatlar', self._labels(self.client.get(self.url, {'q': 'murojaat'})))
        self.assertIn('Chat', self._labels(self.client.get(self.url, {'q': 'qachon'})))

    def test_search_by_id(self):
        self._login_owner()
        resp = self.client.get(self.url, {'q': '#%d' % self.order.pk})
        groups = {g['label']: g for g in resp.json()['results']}
        self.assertIn('Buyurtmalar', groups)
        urls = [it['url'] for it in groups['Buyurtmalar']['items']]
        self.assertIn(reverse('dashboard_order_detail', args=[self.order.pk]), urls)

    def test_short_query_returns_empty(self):
        self._login_owner()
        resp = self.client.get(self.url, {'q': 'a'})
        self.assertEqual(resp.json()['results'], [])

    def test_limit_per_model(self):
        for i in range(8):
            Order.objects.create(
                customer_name='LimitTest case %d' % i,
                phone='+9989000000%02d' % i, total_amount=1,
            )
        self._login_owner()
        resp = self.client.get(self.url, {'q': 'LimitTest'})
        groups = {g['label']: g for g in resp.json()['results']}
        self.assertIn('Buyurtmalar', groups)
        self.assertLessEqual(len(groups['Buyurtmalar']['items']), 5)
