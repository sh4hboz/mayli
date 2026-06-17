from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Role, StaffProfile

User = get_user_model()


class LoginViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='manager1', password='secret123',
            role=Role.MANAGER, full_name='Menejer',
        )

    def test_login_page_renders(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

    def test_login_valid_credentials(self):
        resp = self.client.post(reverse('login'), {
            'username': 'manager1', 'password': 'secret123',
        })
        self.assertRedirects(resp, reverse('dashboard_home'), fetch_redirect_response=False)

    def test_login_invalid_password(self):
        resp = self.client.post(reverse('login'), {
            'username': 'manager1', 'password': 'wrong',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Login yoki parol")

    def test_login_empty_fields(self):
        resp = self.client.post(reverse('login'), {'username': '', 'password': ''})
        self.assertEqual(resp.status_code, 200)

    def test_login_remember_me(self):
        resp = self.client.post(reverse('login'), {
            'username': 'manager1', 'password': 'secret123', 'remember': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        # 30 kun ~ 2.5M soniya — sessiya muddati uzaytirilgan
        self.assertGreater(self.client.session.get_expiry_age(), 24 * 60 * 60)


class StaffManagementTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner1', password='pass12345', role=Role.OWNER, full_name='Ega',
        )
        self.waiter = User.objects.create_user(
            username='waiter1', password='pass12345', role=Role.WAITER, full_name='Ofitsiant',
        )

    def test_owner_sees_staff_page(self):
        self.client.force_login(self.owner)
        resp = self.client.get(reverse('staff_management'))
        self.assertEqual(resp.status_code, 200)

    def test_non_owner_redirected(self):
        self.client.force_login(self.waiter)
        resp = self.client.get(reverse('staff_management'))
        self.assertRedirects(resp, reverse('dashboard_home'), fetch_redirect_response=False)

    def test_create_staff(self):
        self.client.force_login(self.owner)
        resp = self.client.post(reverse('staff_management'), {
            'username': 'barmen1', 'role': Role.BARMAN, 'password': 'parol123',
        })
        self.assertEqual(resp.status_code, 200)
        new = User.objects.filter(username='barmen1').first()
        self.assertIsNotNone(new)
        self.assertTrue(new.check_password('parol123'))
        self.assertTrue(StaffProfile.objects.filter(user=new).exists())

    def test_create_staff_duplicate_username(self):
        self.client.force_login(self.owner)
        resp = self.client.post(reverse('staff_management'), {
            'username': 'waiter1', 'role': Role.WAITER, 'password': 'parol123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(username='waiter1').count(), 1)

    def test_create_staff_short_password(self):
        self.client.force_login(self.owner)
        resp = self.client.post(reverse('staff_management'), {
            'username': 'yangi1', 'role': Role.MANAGER, 'password': '123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='yangi1').exists())


class UnlockScreenTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner1', password='pass12345', role=Role.OWNER, full_name='Ega',
        )
        self.client.force_login(self.user)

    def test_unlock_correct_password(self):
        resp = self.client.post(reverse('dashboard_unlock_screen'), {'password': 'pass12345'})
        self.assertRedirects(resp, reverse('dashboard_home'), fetch_redirect_response=False)

    def test_unlock_wrong_password(self):
        resp = self.client.post(reverse('dashboard_unlock_screen'), {'password': 'wrong'})
        self.assertRedirects(resp, reverse('dashboard_lock_screen'), fetch_redirect_response=False)
