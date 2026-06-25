"""
crm/services.py — Campaign send logic.
"""

from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Campaign, CampaignLog, CampaignLogStatus, CampaignStatus, Customer,
    LoyaltySettings, LoyaltyTransaction, LoyaltyKind,
)
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
                result = provider.send(customer, message_text, template_id=campaign.sms_template_id)

                # Log yaratish
                with transaction.atomic():
                    log = CampaignLog.objects.update_or_create(
                        campaign=campaign,
                        customer=customer,
                        defaults={
                            'status': CampaignLogStatus.SENT if result['success'] else CampaignLogStatus.FAILED,
                            'message_text': message_text,
                            'error_message': result.get('error') or '',
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
            result = provider.send(customer, message_text, template_id=campaign.sms_template_id)

            return {
                'success': result['success'],
                'message': message_text,
                'customer': customer.full_name or customer.phone,
                'error': result.get('error'),
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class BirthdayService:
    """Bugun tug'ilgan kuni bo'lgan mijozlarga SMS tabrik (qisman avtomatik).

    Tizim aniqlaydi va topbarda bildiradi; xodim "SMS tabriklash" tugmasini bosadi.
    `birthday_sms_sent_year` orqali bir yilda ikki marta tabriklanmaydi.
    Hozircha faqat SMS kanali.
    """

    @staticmethod
    def todays_pending():
        """Bugun tug'ilgan kuni bo'lgan, shu yil hali tabriklanmagan, SMS yuborsa bo'ladigan mijozlar."""
        today = timezone.localdate()
        return (
            Customer.objects
            .filter(
                is_active=True,
                sms_consent=True,
                birth_date__month=today.month,
                birth_date__day=today.day,
            )
            .exclude(phone='')
            .exclude(birthday_sms_sent_year=today.year)
            .order_by('first_name')
        )

    @staticmethod
    def congratulate(customer_ids=None):
        """Bugungi tug'ilgan kunlik mijozlarga SMS tabrik yuboradi.

        Args:
            customer_ids: ixtiyoriy list — faqat shu mijozlarga (bo'lmasa hammasiga).

        Returns:
            dict: {'sent': int, 'failed': int, 'errors': list[str]}
        """
        today = timezone.localdate()
        qs = BirthdayService.todays_pending()
        if customer_ids:
            qs = qs.filter(pk__in=customer_ids)

        provider = get_provider('sms')
        template = getattr(settings, 'BIRTHDAY_SMS_TEXT', '') or ''
        template_id = getattr(settings, 'BIRTHDAY_SMS_TEMPLATE_ID', '') or ''

        sent = failed = 0
        errors = []
        for customer in qs:
            message_text = render_template(template, customer)
            try:
                result = provider.send(customer, message_text, template_id=template_id)
            except Exception as e:  # noqa: BLE001
                result = {'success': False, 'error': str(e)}

            if result.get('success'):
                sent += 1
                # Faqat muvaffaqiyatda belgilaymiz — xatolik bo'lsa keyin qayta urinish mumkin
                customer.birthday_sms_sent_year = today.year
                customer.save(update_fields=['birthday_sms_sent_year'])
            else:
                failed += 1
                errors.append(f"{customer.full_name or customer.phone}: {result.get('error', 'xato')}")

        logger.info("Tug'ilgan kun tabriklari: yuborildi=%s, xato=%s", sent, failed)
        return {'sent': sent, 'failed': failed, 'errors': errors}


class LoyaltyService:
    """Sodiqlik dasturi — ball to'plash / sarflash / qo'lda tuzatish.

    Ballar buyurtma "Yetkazildi" bo'lganda beriladi (idempotent — har buyurtma
    uchun bir marta). Umrlik ball (lifetime_points) faqat ball to'planganda oshadi
    va daraja shu bo'yicha hisoblanadi; sarflash/manfiy tuzatish darajani kamaytirmaydi.
    """

    @staticmethod
    @transaction.atomic
    def award_for_order(order):
        """Yetkazilgan buyurtma uchun ball beradi. Idempotent.

        Returns: yaratilgan LoyaltyTransaction yoki None (o'tkazib yuborilgan).
        """
        settings_obj = LoyaltySettings.get()
        if not settings_obj.is_enabled:
            return None
        if order is None or order.customer_id is None:
            return None
        # Faqat shu buyurtma uchun hali ball berilmagan bo'lsa.
        if LoyaltyTransaction.objects.filter(order=order, kind=LoyaltyKind.EARN).exists():
            return None

        points = settings_obj.points_for_amount(order.total_amount)
        if points <= 0:
            return None

        customer = Customer.objects.select_for_update().get(pk=order.customer_id)
        customer.loyalty_points += points
        customer.lifetime_points += points
        customer.save(update_fields=['loyalty_points', 'lifetime_points'])

        txn = LoyaltyTransaction.objects.create(
            customer=customer, order=order, kind=LoyaltyKind.EARN,
            points=points, balance_after=customer.loyalty_points,
            note=f"Buyurtma #{order.pk} uchun",
        )
        logger.info("Loyalty: mijoz=%s buyurtma=#%s +%s ball", customer.pk, order.pk, points)
        return txn

    @staticmethod
    @transaction.atomic
    def adjust(customer_id, points, note='', user=None):
        """Ballni qo'lda o'zgartiradi (+/-). Umrlik ballga TEGMAYDI (faqat balans).

        Balansdan ko'p ayirib bo'lmaydi (manfiyga tushmaydi).
        Returns: dict {'success': bool, 'error'/'balance'}.
        """
        points = int(points)
        if points == 0:
            return {'success': False, 'error': "Ball 0 bo'lishi mumkin emas."}

        customer = Customer.objects.select_for_update().get(pk=customer_id)
        if customer.loyalty_points + points < 0:
            return {'success': False, 'error': "Balansdan ko'p ball ayirib bo'lmaydi."}

        customer.loyalty_points += points
        customer.save(update_fields=['loyalty_points'])

        kind = LoyaltyKind.ADJUST if points > 0 else LoyaltyKind.REDEEM
        LoyaltyTransaction.objects.create(
            customer=customer, kind=kind, points=points,
            balance_after=customer.loyalty_points,
            note=(note or '')[:255], created_by=user,
        )
        return {'success': True, 'balance': customer.loyalty_points}
