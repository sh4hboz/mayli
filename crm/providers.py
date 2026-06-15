"""
crm/providers.py — Marketing provider'lar (SMS, Email, Telegram).
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class MarketingProvider(ABC):
    """Barcha provider'lar uchun tayanch sinf."""

    @abstractmethod
    def send(self, customer, message_text):
        """
        Xabar jo'natish.

        Args:
            customer: Customer instance
            message_text: Jo'natiladigan xabar matn

        Returns:
            dict: {'success': bool, 'error': str or None}
        """
        pass


class SMSProvider(MarketingProvider):
    """SMS provider (Eskiz.uz)."""

    def send(self, customer, message_text):
        """Eskiz API orqali SMS jo'natish."""
        if not customer.phone:
            return {'success': False, 'error': 'Telefon raqami yo\'q'}

        try:
            # TODO: Eskiz.uz API integratsiyasi
            # from crm.integrations.eskiz import send_sms
            # result = send_sms(customer.phone, message_text)

            # Hozircha stub
            logger.info(f"SMS jo'natish (stub): {customer.phone} → {message_text[:50]}...")
            return {'success': True, 'error': None}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SMS xatosi: {error_msg}")
            return {'success': False, 'error': error_msg}


class EmailProvider(MarketingProvider):
    """Email provider (Django email backend)."""

    def send(self, customer, message_text):
        """Django email orqali jo'natish."""
        if not customer.email:
            return {'success': False, 'error': 'Email manzili yo\'q'}

        try:
            from django.core.mail import send_mail
            from django.conf import settings

            send_mail(
                subject='Mayli Restobar — Xabar',
                message=message_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[customer.email],
                fail_silently=False,
            )
            logger.info(f"Email jo'natish: {customer.email}")
            return {'success': True, 'error': None}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Email xatosi: {error_msg}")
            return {'success': False, 'error': error_msg}


class TelegramProvider(MarketingProvider):
    """Telegram provider (notifications.telegram orqali)."""

    def send(self, customer, message_text):
        """Telegram orqali jo'natish."""
        if not customer.telegram_user_id:
            return {'success': False, 'error': 'Telegram user ID yo\'q'}

        try:
            from notifications.telegram import send_direct_message

            send_direct_message(
                user_id=int(customer.telegram_user_id),
                text=message_text,
            )
            logger.info(f"Telegram jo'natish: {customer.telegram_user_id}")
            return {'success': True, 'error': None}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Telegram xatosi: {error_msg}")
            return {'success': False, 'error': error_msg}


def get_provider(channel):
    """Kanal bo'yicha provider qaytarish."""
    providers = {
        'sms': SMSProvider(),
        'email': EmailProvider(),
        'telegram': TelegramProvider(),
    }
    return providers.get(channel)


def render_template(template_str, customer):
    """
    Shablon variable'larini customer ma'lumotlari bilan almashtirish.

    {{first_name}}, {{full_name}}, {{phone}} qo'llash mumkin
    """
    context = {
        'first_name': customer.first_name,
        'full_name': customer.full_name,
        'phone': customer.phone,
    }

    result = template_str
    for key, value in context.items():
        result = result.replace('{{' + key + '}}', str(value or ''))

    return result
