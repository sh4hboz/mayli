from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from accounts.models import Role, StaffProfile
from dashboard.views import NewsListView, NewsCreateView
from restobar.views import staff_permissions_view

User = get_user_model()

class CMSPermissionsTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        
        # 1. Superadmin (Owner) yaratish
        self.superadmin = User.objects.create_user(
            phone='+998991111111',
            password='password123',
            role=Role.OWNER,
            full_name='Owner Super'
        )
        
        # 2. Ofitsiant (Waiter) yaratish
        self.waiter = User.objects.create_user(
            phone='+998992222222',
            password='password123',
            role=Role.WAITER,
            full_name='Ali Waiter'
        )
        StaffProfile.objects.create(user=self.waiter, role=Role.WAITER)

        # 3. Bugalter (Accountant) yaratish
        self.accountant = User.objects.create_user(
            phone='+998993333333',
            password='password123',
            role=Role.ACCOUNTANT,
            full_name='Vali Accountant'
        )
        StaffProfile.objects.create(user=self.accountant, role=Role.ACCOUNTANT)

    def test_waiter_cannot_access_cms(self):
        """Ofitsiant ruxsatnomasi yo'qligi sababli CMS bo'limlariga kira olmasligini tekshirish (403)"""
        request = self.factory.get('/dashboard/website/news/')
        request.user = self.waiter
        
        view = NewsListView.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_waiter_with_permission_can_access(self):
        """Ofitsiantga maxsus permission berilganda u o'sha CMS sahifasiga kira olishini tekshirish"""
        view_news_perm = Permission.objects.get(codename='view_news', content_type__app_label='website')
        self.waiter.user_permissions.add(view_news_perm)
        self.waiter.save()
        
        request = self.factory.get('/dashboard/website/news/')
        request.user = self.waiter
        
        view = NewsListView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        # Lekin boshqa ruxsatsiz bo'limga (sozlamalarga) kira olmaydi
        request_settings = self.factory.get('/dashboard/settings/website/')
        request_settings.user = self.waiter
        from dashboard.views import SiteSettingsUpdateView
        view_settings = SiteSettingsUpdateView.as_view()
        with self.assertRaises(PermissionDenied):
            view_settings(request_settings)

    def test_accountant_read_only_restriction(self):
        """Bugalter (Accountant) ma'lumotlarni ko'ra olishi, lekin yozish (POST) so'rovlari 403 qaytarishini tekshirish"""
        view_news_perm = Permission.objects.get(codename='view_news', content_type__app_label='website')
        add_news_perm = Permission.objects.get(codename='add_news', content_type__app_label='website')
        self.accountant.user_permissions.add(view_news_perm, add_news_perm)
        self.accountant.save()
        
        # GET so'rovi ishlashi kerak (200)
        request = self.factory.get('/dashboard/website/news/')
        request.user = self.accountant
        view = NewsListView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        # POST so'rovi (yangi yangilik qo'shish) Bugalter uchun bloklanishi kerak (403/PermissionDenied)
        request = self.factory.post('/dashboard/website/news/add/', {
            'title_uz': 'Test title',
            'body_uz': 'Test body',
            'is_published': True
        })
        request.user = self.accountant
        view = NewsCreateView.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_superadmin_can_manage_staff_permissions(self):
        """Superadmin xodimlarning ruxsatnomalarini (permissions) split select orqali tahrirlay olishini tekshirish"""
        view_news_perm = Permission.objects.get(codename='view_news', content_type__app_label='website')
        
        # Avval xodimda permission yo'q
        self.assertFalse(self.waiter.has_perm('website.view_news'))
        
        request = self.factory.post(f'/dashboard/staff/{self.waiter.id}/permissions/', {
            'permissions': [view_news_perm.id]
        })
        request.user = self.superadmin
        
        response = staff_permissions_view(request, user_id=self.waiter.id)
        self.assertEqual(response.status_code, 302) # Redirect
        
        # Ruxsat saqlanganini tekshirish
        updated_waiter = User.objects.get(id=self.waiter.id)
        self.assertTrue(updated_waiter.has_perm('website.view_news'))
