from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from menu.models import Dish
from orders.models import Order, OrderSettings, OrderStatus, OtpCode, PaymentMethod
from orders.services import OrderError, OrderService, OtpService

PHONE = '998901112233'
NORM = '+998901112233'


@override_settings(DEBUG=True)
class OtpServiceTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_request_creates_code(self):
        r = OtpService.request(PHONE)
        self.assertTrue(r['success'])
        self.assertIn('dev_code', r)
        otp = OtpCode.objects.get(phone=NORM)
        self.assertEqual(otp.code, r['dev_code'])

    def test_request_invalid_phone(self):
        r = OtpService.request('123')
        self.assertFalse(r['success'])

    def test_verify_success(self):
        code = OtpService.request(PHONE)['dev_code']
        v = OtpService.verify(PHONE, code)
        self.assertTrue(v['verified'])
        self.assertTrue(OtpCode.objects.get(phone=NORM).is_verified)

    def test_verify_wrong_code(self):
        code = OtpService.request(PHONE)['dev_code']
        wrong = '000000' if code != '000000' else '111111'
        v = OtpService.verify(PHONE, wrong)
        self.assertFalse(v['verified'])

    def test_verify_expired(self):
        OtpCode.objects.create(
            phone=NORM, code='123456', purpose='order',
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        v = OtpService.verify(PHONE, '123456')
        self.assertFalse(v['verified'])

    def test_max_attempts(self):
        code = OtpService.request(PHONE)['dev_code']
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(5):
            OtpService.verify(PHONE, wrong)
        # 6-urinishda — bloklanadi (to'g'ri kod bo'lsa ham)
        v = OtpService.verify(PHONE, code)
        self.assertFalse(v['verified'])


class OrderServiceTest(TestCase):
    def setUp(self):
        self.dish = Dish.objects.create(name='Lagman', price=Decimal('25000'))
        OrderSettings.objects.update_or_create(
            pk=1, defaults={'is_open': True, 'min_order_amount': Decimal('0')})

    def _verified_otp(self):
        return OtpCode.objects.create(
            phone=NORM, code='123456', purpose='order', is_verified=True,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

    def test_requires_verified_otp(self):
        with self.assertRaises(OrderError):
            OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 2}])

    def test_total_computed_from_db(self):
        self._verified_otp()
        order = OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 2}])
        self.assertEqual(order.total_amount, Decimal('50000'))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.phone, NORM)
        item = order.items.first()
        self.assertEqual(item.dish_name, 'Lagman')
        self.assertEqual(item.unit_price, Decimal('25000'))

    def test_price_tampering_ignored(self):
        self._verified_otp()
        # Frontend narx yubormaydi — faqat id+qty; baribir DB narxi ishlatiladi.
        order = OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1, 'price': 1}])
        self.assertEqual(order.total_amount, Decimal('25000'))

    def test_otp_consumed_after_order(self):
        otp = self._verified_otp()
        OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}])
        otp.refresh_from_db()
        self.assertTrue(otp.consumed)

    def test_min_amount_enforced(self):
        OrderSettings.objects.filter(pk=1).update(min_order_amount=Decimal('100000'))
        self._verified_otp()
        with self.assertRaises(OrderError):
            OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}])

    def test_closed_rejected(self):
        OrderSettings.objects.filter(pk=1).update(is_open=False)
        self._verified_otp()
        with self.assertRaises(OrderError):
            OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}])

    def test_empty_cart_rejected(self):
        self._verified_otp()
        with self.assertRaises(OrderError):
            OrderService.create('Ali', PHONE, [])

    def test_inactive_dish_excluded(self):
        self._verified_otp()
        inactive = Dish.objects.create(name='Yopiq', price=Decimal('9000'), is_active=False)
        order = OrderService.create('Ali', PHONE, [
            {'id': self.dish.id, 'qty': 1}, {'id': inactive.id, 'qty': 5},
        ])
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('25000'))

    def test_payment_method_stored(self):
        self._verified_otp()
        order = OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}],
                                    payment_method='card')
        self.assertEqual(order.payment_method, PaymentMethod.CARD)

    def test_invalid_payment_method_defaults_cash(self):
        self._verified_otp()
        order = OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}],
                                    payment_method='bitcoin')
        self.assertEqual(order.payment_method, PaymentMethod.CASH)

    def test_customer_upserted_and_linked(self):
        from crm.models import Customer
        self._verified_otp()
        order = OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}])
        self.assertTrue(Customer.objects.filter(phone=NORM).exists())
        self.assertIsNotNone(order.customer)
        self.assertEqual(order.customer.first_name, 'Ali')


class MyOrdersTest(TestCase):
    def setUp(self):
        cache.clear()
        self.dish = Dish.objects.create(name='Lagman', price=Decimal('25000'))

    def _make_order(self):
        OtpCode.objects.create(phone=NORM, code='123456', purpose='order',
                               is_verified=True, expires_at=timezone.now() + timedelta(minutes=5))
        return OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 2}])

    def test_my_orders_by_phone(self):
        o = self._make_order()
        r = self.client.get(reverse('order_my'), {'phone': PHONE})
        data = r.json()
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['orders'][0]['id'], o.id)
        self.assertTrue(data['orders'][0]['is_active'])

    def test_my_orders_no_phone(self):
        self.assertEqual(self.client.get(reverse('order_my')).json()['orders'], [])

    def test_my_orders_other_phone_empty(self):
        self._make_order()
        r = self.client.get(reverse('order_my'), {'phone': '998905550000'})
        self.assertEqual(r.json()['orders'], [])


class TelegramCallbackTest(TestCase):
    def setUp(self):
        cache.clear()
        self.dish = Dish.objects.create(name='Lagman', price=Decimal('25000'))

    def _make_order(self):
        OtpCode.objects.create(phone=NORM, code='123456', purpose='order',
                               is_verified=True, expires_at=timezone.now() + timedelta(minutes=5))
        return OrderService.create('Ali', PHONE, [{'id': self.dish.id, 'qty': 1}])

    def _callback(self, action, pk):
        from notifications.views import _handle_order_callback
        _handle_order_callback({
            'id': 'cb1', 'data': f'{action}:{pk}',
            'from': {'first_name': 'Boss'},
            'message': {'chat': {'id': 1}, 'message_id': 2},
        })

    def test_accept_via_callback(self):
        o = self._make_order()
        self._callback('order_accept', o.id)
        o.refresh_from_db()
        self.assertEqual(o.status, OrderStatus.ACCEPTED)
        self.assertIsNotNone(o.accepted_at)

    def test_reject_via_callback(self):
        o = self._make_order()
        self._callback('order_reject', o.id)
        o.refresh_from_db()
        self.assertEqual(o.status, OrderStatus.REJECTED)
        self.assertTrue(o.reject_reason)

    def test_callback_idempotent(self):
        o = self._make_order()
        self._callback('order_accept', o.id)
        self._callback('order_reject', o.id)  # allaqachon accepted — o'zgarmaydi
        o.refresh_from_db()
        self.assertEqual(o.status, OrderStatus.ACCEPTED)


class OrderEndpointTest(TestCase):
    def setUp(self):
        cache.clear()
        self.dish = Dish.objects.create(name='Lagman', price=Decimal('25000'))

    def test_create_without_otp_returns_400(self):
        resp = self.client.post(
            reverse('order_create'),
            data={'name': 'Ali', 'phone': PHONE, 'items': [{'id': self.dish.id, 'qty': 1}]},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    @override_settings(DEBUG=True)
    def test_full_flow(self):
        r = self.client.post(reverse('order_otp_request'),
                             data={'phone': PHONE}, content_type='application/json')
        self.assertEqual(r.status_code, 200)
        code = r.json()['dev_code']
        v = self.client.post(reverse('order_otp_verify'),
                             data={'phone': PHONE, 'code': code}, content_type='application/json')
        self.assertTrue(v.json()['verified'])
        c = self.client.post(reverse('order_create'),
                             data={'name': 'Ali', 'phone': PHONE, 'payment_method': 'cash',
                                   'items': [{'id': self.dish.id, 'qty': 2}]},
                             content_type='application/json')
        self.assertTrue(c.json()['success'])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().total_amount, Decimal('50000'))
