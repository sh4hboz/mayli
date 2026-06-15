from django.test import TestCase

from .models import Customer


class CustomerModelTest(TestCase):
    def test_full_name_and_str(self):
        c = Customer.objects.create(first_name="Ali", last_name="Valiyev", phone="+998901112233")
        self.assertEqual(c.full_name, "Ali Valiyev")
        self.assertEqual(str(c), "Ali Valiyev")

    def test_str_falls_back_to_phone(self):
        c = Customer.objects.create(first_name="", phone="+998900000000")
        self.assertEqual(str(c), "+998900000000")
