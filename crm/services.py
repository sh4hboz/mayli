"""
crm/services.py — Campaign send logic.
"""

from datetime import datetime
from django.db import transaction
from django.utils import timezone

from .models import Campaign, CampaignLog, CampaignLogStatus, CampaignStatus, Customer
from .providers import get_provider, render_template

import logging

logger = logging.getLogger(__name__)


class CampaignSendService:
    """Kampaniyalarni jo'natish logic'i."""

    @staticmethod
    def send_campaign(campaign_id):
        """
        Kampaniyani barcha mijozlarga jo'natish.

        Args:
            campaign_id: Campaign PK

        Returns:
            dict: {'sent': int, 'failed': int, 'errors': []}
        """
        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            logger.error(f"Kampaniya topilmadi: {campaign_id}")
            return {'sent': 0, 'failed': 0, 'errors': ['Kampaniya topilmadi']}

        # Mijozlarni filtrlash
        customers = CampaignSendService._get_target_customers(campaign)

        if not customers.exists():
            logger.warning(f"Kampaniya {campaign.id} uchun mijozlar topilmadi")
            return {'sent': 0, 'failed': 0, 'errors': ['Mijozlar topilmadi']}

        # Provider qo'lga olish
        provider = get_provider(campaign.channel)
        if not provider:
            logger.error(f"Provider topilmadi: {campaign.channel}")
            return {'sent': 0, 'failed': 0, 'errors': [f'Kanal topilmadi: {campaign.channel}']}

        # Jo'natish logikasi
        sent_count = 0
        failed_count = 0
        errors = []

        for customer in customers:
            try:
                # Shablon variable'larini almashtirish
                message_text = render_template(campaign.template, customer)

                # Jo'natish
                result = provider.send(customer, message_text)

                # Log yaratish
                with transaction.atomic():
                    log = CampaignLog.objects.update_or_create(
                        campaign=campaign,
                        customer=customer,
                        defaults={
                            'status': CampaignLogStatus.SENT if result['success'] else CampaignLogStatus.FAILED,
                            'message_text': message_text,
                            'error_message': result.get('error', ''),
                            'sent_at': timezone.now() if result['success'] else None,
                        }
                    )

                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1
                    errors.append(f"{customer.phone}: {result.get('error', 'Noma\'lum xato')}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"Kampaniya jo'natish xatosi ({customer.phone}): {error_msg}")
                failed_count += 1
                errors.append(f"{customer.phone}: {error_msg}")

                # Log yaratish (xato uchun)
                with transaction.atomic():
                    CampaignLog.objects.update_or_create(
                        campaign=campaign,
                        customer=customer,
                        defaults={
                            'status': CampaignLogStatus.FAILED,
                            'error_message': error_msg,
                        }
                    )

        # Campaign statistika yangilash
        campaign.sent_count = sent_count
        campaign.failed_count = failed_count
        campaign.status = CampaignStatus.SENT
        campaign.save(update_fields=['sent_count', 'failed_count', 'status'])

        logger.info(
            f"Kampaniya {campaign.id} tugallandi: "
            f"yuborilan={sent_count}, xato={failed_count}"
        )

        return {
            'sent': sent_count,
            'failed': failed_count,
            'errors': errors,
            'campaign_id': campaign.id,
        }

    @staticmethod
    def _get_target_customers(campaign):
        """
        Kampaniya uchun target mijozlarni qidirish.

        Agar teg bo'lsa, faqat tegga ega mijozlar.
        Bo'lmasa, barcha faol mijozlar.
        """
        customers = Customer.objects.filter(is_active=True)

        # Kanal bo'yicha filtr
        if campaign.channel == 'sms':
            customers = customers.filter(sms_consent=True, phone__isnull=False).exclude(phone='')
        elif campaign.channel == 'email':
            customers = customers.filter(email_consent=True, email__isnull=False).exclude(email='')
        elif campaign.channel == 'telegram':
            customers = customers.filter(
                telegram_consent=True,
                telegram_user_id__isnull=False
            ).exclude(telegram_user_id='')

        # Teglar bo'yicha filtr
        if campaign.tags.exists():
            customers = customers.filter(tags__in=campaign.tags.all()).distinct()

        return customers.select_related()

    @staticmethod
    def test_send(campaign_id, customer_id=None):
        """
        Test jo'natish (bitta mijozga).

        Args:
            campaign_id: Campaign PK
            customer_id: Customer PK (bo'lmasa — random 1 ta)

        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            return {'success': False, 'message': 'Kampaniya topilmadi'}

        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                return {'success': False, 'message': 'Mijoz topilmadi'}
        else:
            # Random 1 ta mijoz
            customers = CampaignSendService._get_target_customers(campaign)
            customer = customers.first()
            if not customer:
                return {'success': False, 'message': 'Target mijozlar topilmadi'}

        provider = get_provider(campaign.channel)
        if not provider:
            return {'success': False, 'message': f'Kanal topilmadi: {campaign.channel}'}

        try:
            message_text = render_template(campaign.template, customer)
            result = provider.send(customer, message_text)

            return {
                'success': result['success'],
                'message': message_text,
                'customer': customer.full_name or customer.phone,
                'error': result.get('error'),
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
