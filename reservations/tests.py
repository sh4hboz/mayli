from datetime import time, timedelta

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from reservations.models import (
    BookingSettings,
    OtpCode,
    Reservation,
    ReservationStatus,
    Table,
    Zone,
)
from reservations.services import (
    AvailabilityService,
    OtpService,
    ReservationError,
    ReservationService,
)

PHONE = '998901112233'
NORM = '+998901112233'


def _future_date(days=2):
    return timezone.localdate() + timedelta(days=days)


@override_settings(DEBUG=True)
class OtpServiceTest(TestCase):
    def setUp(self):
        cache.clear()

    def test_request_creates_code(self):
        r = OtpService.request(PHONE)
        self.assertTrue(r['success'])
        self.assertIn('dev_code', r)
        self.assertEqual(OtpCode.objects.get(phone=NORM).code, r['dev_code'])

    def test_request_invalid_phone(self):
        self.assertFalse(OtpService.request('123')['success'])

    def test_verify_success(self):
        code = OtpService.request(PHONE)['dev_code']
        self.assertTrue(OtpService.verify(PHONE, code)['verified'])
        self.assertTrue(OtpCode.objects.get(phone=NORM).is_verified)

    def test_verify_wrong_code(self):
        code = OtpService.request(PHONE)['dev_code']
        wrong = '000000' if code != '000000' else '111111'
        self.assertFalse(OtpService.verify(PHONE, wrong)['verified'])

    def test_verify_expired(self):
        OtpCode.objects.create(phone=NORM, code='123456',
                               expires_at=timezone.now() - timedelta(minutes=1))
        self.assertFalse(OtpService.verify(PHONE, '123456')['verified'])

    def test_max_attempts(self):
        code = OtpService.request(PHONE)['dev_code']
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(5):
            OtpService.verify(PHONE, wrong)
        self.assertFalse(OtpService.verify(PHONE, code)['verified'])


class ReservationBaseTest(TestCase):
    def setUp(self):
        cache.clear()
        BookingSettings.objects.update_or_create(
            pk=1, defaults={'is_open': True, 'conflict_window': 120,
                            'open_time': time(10, 0), 'close_time': time(23, 0),
                            'advance_days': 30})
        self.zone = Zone.objects.create(name='Ichki')
        self.table = Table.objects.create(zone=self.zone, number='1', capacity=4)

    def _verified_otp(self):
        return OtpCode.objects.create(
            phone=NORM, code='123456', is_verified=True,
            expires_at=timezone.now() + timedelta(minutes=5))

    def _create(self, **kw):
        defaults = dict(name='Ali', phone=PHONE, table_id=self.table.id,
                        date=_future_date(), time='19:00', guests=2)
        defaults.update(kw)
        return ReservationService.create(**defaults)


class ReservationServiceTest(ReservationBaseTest):
    def test_requires_verified_otp(self):
        with self.assertRaises(ReservationError):
            self._create()

    def test_create_success(self):
        self._verified_otp()
        r = self._create()
        self.assertEqual(r.status, ReservationStatus.PENDING)
        self.assertEqual(r.customer_phone, NORM)
        self.assertTrue(r.otp_verified)

    def test_otp_consumed(self):
        otp = self._verified_otp()
        self._create()
        otp.refresh_from_db()
        self.assertTrue(otp.consumed)

    def test_conflict_within_window_rejected(self):
        self._verified_otp()
        self._create(time='19:00')
        # 60 daqiqa keyin — 120 daqiqalik oyna ichida → band
        OtpCode.objects.create(phone=NORM, code='1', is_verified=True,
                               expires_at=timezone.now() + timedelta(minutes=5))
        with self.assertRaises(ReservationError):
            self._create(time='20:00')

    def test_no_conflict_outside_window_ok(self):
        self._verified_otp()
        self._create(time='19:00')
        OtpCode.objects.create(phone=NORM, code='1', is_verified=True,
                               expires_at=timezone.now() + timedelta(minutes=5))
        r = self._create(time='21:30')  # 150 daq > 120 → bo'sh
        self.assertEqual(r.status, ReservationStatus.PENDING)

    def test_cancelled_does_not_block(self):
        self._verified_otp()
        first = self._create(time='19:00')
        first.status = ReservationStatus.CANCELLED
        first.save(update_fields=['status'])
        OtpCode.objects.create(phone=NORM, code='1', is_verified=True,
                               expires_at=timezone.now() + timedelta(minutes=5))
        r = self._create(time='19:00')  # bekor qilingan bron to'smaydi
        self.assertEqual(r.status, ReservationStatus.PENDING)

    def test_capacity_too_small(self):
        self._verified_otp()
        with self.assertRaises(ReservationError):
            self._create(guests=10)

    def test_closed_rejected(self):
        BookingSettings.objects.filter(pk=1).update(is_open=False)
        self._verified_otp()
        with self.assertRaises(ReservationError):
            self._create()

    def test_past_date_rejected(self):
        self._verified_otp()
        with self.assertRaises(ReservationError):
            self._create(date=timezone.localdate() - timedelta(days=1))

    def test_outside_hours_rejected(self):
        self._verified_otp()
        with self.assertRaises(ReservationError):
            self._create(time='09:00')

    def test_too_far_ahead_rejected(self):
        self._verified_otp()
        with self.assertRaises(ReservationError):
            self._create(date=timezone.localdate() + timedelta(days=60))


class AvailabilityServiceTest(ReservationBaseTest):
    def test_free_when_no_reservation(self):
        tables = AvailabilityService.for_query(_future_date(), '19:00', 2)
        self.assertEqual(tables[0]['state'], 'free')

    def test_small_when_capacity_low(self):
        tables = AvailabilityService.for_query(_future_date(), '19:00', 10)
        self.assertEqual(tables[0]['state'], 'small')

    def test_busy_when_conflict(self):
        self._verified_otp()
        self._create(time='19:00')
        tables = AvailabilityService.for_query(_future_date(), '19:30', 2)
        self.assertEqual(tables[0]['state'], 'busy')

    def test_occupied_table_busy(self):
        Table.objects.filter(pk=self.table.pk).update(status='occupied')
        tables = AvailabilityService.for_query(_future_date(), '19:00', 2)
        self.assertEqual(tables[0]['state'], 'busy')


class ReservationEndpointTest(ReservationBaseTest):
    def test_create_without_otp_400(self):
        resp = self.client.post(
            reverse('booking_create'),
            data={'name': 'Ali', 'phone': PHONE, 'table_id': self.table.id,
                  'date': str(_future_date()), 'time': '19:00', 'guests': 2},
            content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_availability_endpoint(self):
        r = self.client.get(reverse('booking_availability'),
                            {'date': str(_future_date()), 'time': '19:00', 'guests': 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['tables']), 1)

    @override_settings(DEBUG=True)
    def test_full_flow(self):
        r = self.client.post(reverse('booking_otp_request'),
                             data={'phone': PHONE}, content_type='application/json')
        code = r.json()['dev_code']
        v = self.client.post(reverse('booking_otp_verify'),
                             data={'phone': PHONE, 'code': code}, content_type='application/json')
        self.assertTrue(v.json()['verified'])
        c = self.client.post(reverse('booking_create'),
                             data={'name': 'Ali', 'phone': PHONE, 'table_id': self.table.id,
                                   'date': str(_future_date()), 'time': '19:00', 'guests': 2},
                             content_type='application/json')
        self.assertTrue(c.json()['success'])
        self.assertEqual(Reservation.objects.count(), 1)


# BookingPageTest olib tashlandi — public /bron/ (website:booking) sahifasi
# hozircha frontdan olib tashlandi (2D/3D bron muzlatildi). reservations backend
# (API + modellar) joyida; bron qaytarilganda sahifa va bu test ham tiklanadi.
