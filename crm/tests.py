from unittest.mock import patch

from django.test import TestCase

from .models import Customer, Tag, Campaign, CampaignLog, CampaignLogStatus, CampaignStatus
from .providers import (
    get_provider, render_template, SMSProvider, EmailProvider, TelegramProvider,
)
from .services import CampaignSendService


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
