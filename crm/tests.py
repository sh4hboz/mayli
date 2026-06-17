from unittest.mock import patch

from django.test import TestCase, override_settings

from .models import Customer, Tag, Campaign, CampaignLog, CampaignLogStatus, CampaignStatus
from .providers import (
    get_provider, render_template, SMSProvider, EmailProvider, TelegramProvider,
)
from .services import CampaignSendService, BirthdayService
from .integrations.textup import TextUpClient, normalize_phone, TextUpError


class CustomerModelTest(TestCase):
    def test_full_name_and_str(self):
        c = Customer.objects.create(first_name="Ali", last_name="Valiyev", phone="+998901112233")
        self.assertEqual(c.full_name, "Ali Valiyev")
        self.assertEqual(str(c), "Ali Valiyev")

    def test_str_falls_back_to_phone(self):
        c = Customer.objects.create(first_name="", phone="+998900000000")
        self.assertEqual(str(c), "+998900000000")


class ProviderTests(TestCase):

    def test_render_template_substitutes_variables(self):
        c = Customer.objects.create(first_name="Ali", last_name="Valiyev", phone="+998901112233")
        out = render_template("Salom {{first_name}} ({{full_name}}) — {{phone}}", c)
        self.assertEqual(out, "Salom Ali (Ali Valiyev) — +998901112233")

    def test_render_template_empty_value(self):
        c = Customer.objects.create(first_name="Ali", phone="+998901112234")
        out = render_template("{{first_name}} {{last_name_unknown}}", c)
        self.assertIn("Ali", out)

    def test_get_provider_mapping(self):
        self.assertIsInstance(get_provider('sms'), SMSProvider)
        self.assertIsInstance(get_provider('email'), EmailProvider)
        self.assertIsInstance(get_provider('telegram'), TelegramProvider)
        self.assertIsNone(get_provider('unknown'))

    def test_sms_provider_no_phone(self):
        c = Customer(first_name="X", phone="")
        result = SMSProvider().send(c, "test")
        self.assertFalse(result['success'])

    @patch('crm.integrations.textup.TextUpClient.send_sms')
    def test_sms_provider_calls_textup(self, mock_send):
        mock_send.return_value = {'success': True, 'error': None, 'sms_id': 'X1'}
        c = Customer(first_name="Ali", phone="908201004")
        result = SMSProvider().send(c, "salom")
        self.assertTrue(result['success'])
        # Telefon E.164 ga normalizatsiya qilinib uzatiladi
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], ['+998908201004'])


class TextUpClientTests(TestCase):

    def setUp(self):
        # Modul darajasidagi token keshini har test oldidan tozalaymiz
        from crm.integrations import textup
        textup._token_cache['token'] = None
        textup._token_cache['user_id'] = None

    def test_normalize_phone(self):
        self.assertEqual(normalize_phone('+998 (90) 820-10-04'), '+998908201004')
        self.assertEqual(normalize_phone('908201004'), '+998908201004')
        self.assertEqual(normalize_phone('998908201004'), '+998908201004')
        self.assertIsNone(normalize_phone('12345'))
        self.assertIsNone(normalize_phone(''))

    @override_settings(TEXTUP_EMAIL='e@x.uz', TEXTUP_PASSWORD='pw')
    @patch('crm.integrations.textup.TextUpClient._request')
    def test_send_sms_success(self, mock_request):
        # 1-chi chaqiruv: login javobi; 2-chi: SMS javobi
        mock_request.side_effect = [
            {'accessToken': 'TKN', 'user': {'id': 42}},
            {'smsId': 'sms-1'},
        ]
        out = TextUpClient().send_sms(['908201004'], 'salom', name='Mayli')
        self.assertTrue(out['success'])
        self.assertEqual(out['sms_id'], 'sms-1')
        # SMS so'rovida userId va normalizatsiyalangan raqam bo'lishi kerak
        sms_payload = mock_request.call_args_list[1].args[1]
        self.assertEqual(sms_payload['userId'], 42)
        self.assertEqual(sms_payload['recipients'], ['+998908201004'])

    @override_settings(TEXTUP_EMAIL='e@x.uz', TEXTUP_PASSWORD='pw')
    @patch('crm.integrations.textup.TextUpClient._request')
    def test_send_sms_with_template_id(self, mock_request):
        mock_request.side_effect = [
            {'accessToken': 'TKN', 'user': {'id': 42}},
            {'smsId': 'sms-2'},
        ]
        out = TextUpClient().send_sms(['908201004'], 'salom', template_id='tpl-123')
        self.assertTrue(out['success'])
        sms_payload = mock_request.call_args_list[1].args[1]
        self.assertEqual(sms_payload['templateId'], 'tpl-123')

    @override_settings(TEXTUP_EMAIL='e@x.uz', TEXTUP_PASSWORD='pw')
    @patch('crm.integrations.textup.TextUpClient._request')
    def test_send_sms_without_template_id_omits_key(self, mock_request):
        mock_request.side_effect = [
            {'accessToken': 'TKN', 'user': {'id': 42}},
            {'smsId': 'sms-3'},
        ]
        TextUpClient().send_sms(['908201004'], 'salom')
        sms_payload = mock_request.call_args_list[1].args[1]
        self.assertNotIn('templateId', sms_payload)

    @override_settings(TEXTUP_EMAIL='', TEXTUP_PASSWORD='')
    def test_send_sms_no_credentials(self):
        out = TextUpClient().send_sms(['908201004'], 'salom')
        self.assertFalse(out['success'])
        self.assertIn('sozlanmagan', out['error'])

    def test_send_sms_invalid_phone(self):
        out = TextUpClient(email='e', password='p').send_sms(['12345'], 'salom')
        self.assertFalse(out['success'])


class CampaignServiceTests(TestCase):

    def setUp(self):
        self.tag_vip = Tag.objects.create(name='VIP')
        # Target mijoz (sms rozilik, faol, telefon bor)
        self.c1 = Customer.objects.create(
            first_name='Target', phone='+998901110001', sms_consent=True, is_active=True,
        )
        self.c1.tags.add(self.tag_vip)
        # Rozilik yo'q -> chiqarib tashlanadi
        Customer.objects.create(
            first_name='NoConsent', phone='+998901110002', sms_consent=False, is_active=True,
        )
        # Faol emas -> chiqarib tashlanadi
        Customer.objects.create(
            first_name='Inactive', phone='+998901110003', sms_consent=True, is_active=False,
        )
        self.campaign = Campaign.objects.create(
            name='Test SMS', channel='sms', template='Salom {{first_name}}',
        )

    def test_target_customers_filtered(self):
        targets = CampaignSendService._get_target_customers(self.campaign)
        self.assertEqual(targets.count(), 1)
        self.assertEqual(targets.first(), self.c1)

    @patch('crm.services.get_provider')
    def test_send_campaign_success(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': True, 'error': None}
        result = CampaignSendService.send_campaign(self.campaign.pk)
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        log = CampaignLog.objects.get(campaign=self.campaign, customer=self.c1)
        self.assertEqual(log.status, CampaignLogStatus.SENT)
        self.assertEqual(log.message_text, 'Salom Target')
        self.assertIsNotNone(log.sent_at)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.sent_count, 1)
        self.assertEqual(self.campaign.status, CampaignStatus.SENT)

    @patch('crm.services.get_provider')
    def test_send_campaign_failure(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': False, 'error': 'API xato'}
        result = CampaignSendService.send_campaign(self.campaign.pk)
        self.assertEqual(result['sent'], 0)
        self.assertEqual(result['failed'], 1)
        log = CampaignLog.objects.get(campaign=self.campaign, customer=self.c1)
        self.assertEqual(log.status, CampaignLogStatus.FAILED)
        self.assertEqual(log.error_message, 'API xato')

    @patch('crm.services.get_provider')
    def test_tag_filter_limits_recipients(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': True, 'error': None}
        # Tegsiz, lekin target shartlarga mos boshqa mijoz
        Customer.objects.create(
            first_name='NoTag', phone='+998901110009', sms_consent=True, is_active=True,
        )
        self.campaign.tags.add(self.tag_vip)
        result = CampaignSendService.send_campaign(self.campaign.pk)
        self.assertEqual(result['sent'], 1)  # faqat VIP tegli c1

    @patch('crm.services.get_provider')
    def test_test_send_single(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': True, 'error': None}
        result = CampaignSendService.test_send(self.campaign.pk, customer_id=self.c1.pk)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Salom Target')


class BirthdayServiceTests(TestCase):

    def setUp(self):
        from django.utils import timezone
        self.today = timezone.localdate()
        # Bugun tug'ilgan kun — target
        self.bday = Customer.objects.create(
            first_name='Ali', phone='+998901110001', sms_consent=True, is_active=True,
            birth_date=self.today.replace(year=1990),
        )
        # Bugun, lekin rozilik yo'q
        Customer.objects.create(
            first_name='NoConsent', phone='+998901110002', sms_consent=False, is_active=True,
            birth_date=self.today.replace(year=1991),
        )
        # Boshqa kun
        other = self.today.replace(year=1992) + __import__('datetime').timedelta(days=1)
        Customer.objects.create(
            first_name='Other', phone='+998901110003', sms_consent=True, is_active=True,
            birth_date=other,
        )

    def test_todays_pending_filters(self):
        pending = list(BirthdayService.todays_pending())
        self.assertEqual(pending, [self.bday])

    @override_settings(BIRTHDAY_SMS_TEXT='Tabrik {{first_name}}', BIRTHDAY_SMS_TEMPLATE_ID='tpl-x')
    @patch('crm.services.get_provider')
    def test_congratulate_success_marks_year(self, mock_get_provider):
        mock_send = mock_get_provider.return_value.send
        mock_send.return_value = {'success': True, 'error': None}
        result = BirthdayService.congratulate()
        self.assertEqual(result['sent'], 1)
        self.assertEqual(result['failed'], 0)
        # template_id va matn uzatilgan
        args, kwargs = mock_send.call_args
        self.assertEqual(args[1], 'Tabrik Ali')
        self.assertEqual(kwargs['template_id'], 'tpl-x')
        # Yil belgilandi -> qayta tabriklanmaydi
        self.bday.refresh_from_db()
        self.assertEqual(self.bday.birthday_sms_sent_year, self.today.year)
        self.assertEqual(list(BirthdayService.todays_pending()), [])

    @patch('crm.services.get_provider')
    def test_congratulate_failure_keeps_pending(self, mock_get_provider):
        mock_get_provider.return_value.send.return_value = {'success': False, 'error': 'xato'}
        result = BirthdayService.congratulate()
        self.assertEqual(result['sent'], 0)
        self.assertEqual(result['failed'], 1)
        self.bday.refresh_from_db()
        self.assertIsNone(self.bday.birthday_sms_sent_year)
        # Hali pending — keyin qayta urinish mumkin
        self.assertEqual(list(BirthdayService.todays_pending()), [self.bday])
