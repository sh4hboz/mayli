from django.test import TestCase, Client
from django.urls import reverse
from orders.utils import is_in_delivery_zone
from menu.models import Dish, Category
import json

class DeliveryZoneTestCase(TestCase):
    def test_point_inside_zone(self):
        # Termiz shahar markaziy nuqtasi zona ichida bo'lishi kerak
        self.assertTrue(is_in_delivery_zone(37.224, 67.278))

    def test_point_outside_zone(self):
        # Toshkent shahri koordinatalari Termiz zonasidan tashqarida bo'lishi kerak
        self.assertFalse(is_in_delivery_zone(41.311081, 69.240562))
        
        # Dunyoning boshqa chekkasi
        self.assertFalse(is_in_delivery_zone(0, 0))

class OrderCreateAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Shashliklar", slug="shashliklar")
        self.dish = Dish.objects.create(
            category=self.category,
            name="Qiyma Shashlik",
            price=15000.00,
            is_active=True,
            is_available=True
        )
        self.url = reverse('website:order_create')

    def test_order_creation_inside_delivery_zone(self):
        data = {
            'order_type': 'delivery',
            'customer_name': 'Mijoz 1',
            'customer_phone': '+998901234567',
            'delivery_address': 'Termiz shahar, Alisher Navoiy ko\'chasi',
            'delivery_lat': 37.224,
            'delivery_lng': 67.278,
            'items': [{'id': self.dish.id, 'qty': 2}]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data['success'])
        self.assertIn('order_id', res_data)

    def test_order_creation_outside_delivery_zone(self):
        data = {
            'order_type': 'delivery',
            'customer_name': 'Mijoz 2',
            'customer_phone': '+998907654321',
            'delivery_address': 'Toshkent shahar, Chilonzor',
            'delivery_lat': 41.311081,
            'delivery_lng': 69.240562,
            'items': [{'id': self.dish.id, 'qty': 1}]
        }
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        res_data = response.json()
        self.assertFalse(res_data['success'])
        self.assertIn('hududimizga kirmaydi', res_data['error'])
