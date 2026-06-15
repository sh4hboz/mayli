"""
Django management command: send_campaigns

Rejalashtirylgan kampaniyalarni jo'natish.

Ishlatish:
    python manage.py send_campaigns          # Barcha rejalashtirylgan
    python manage.py send_campaigns 1        # ID bo'yicha kampaniya
    python manage.py send_campaigns --test   # Test mode (bitta mijozga)
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from crm.models import Campaign, CampaignStatus
from crm.services import CampaignSendService


class Command(BaseCommand):
    help = 'Rejalashtirylgan kampaniyalarni jo\'natish'

    def add_arguments(self, parser):
        parser.add_argument(
            'campaign_id',
            nargs='?',
            type=int,
            help='Campaign ID (bo\'lmasa — barcha rejalashtirylgan)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode — bitta mijozga jo\'natish',
        )
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Test mode uchun customer ID',
        )

    def handle(self, *args, **options):
        campaign_id = options.get('campaign_id')
        test_mode = options.get('test', False)
        customer_id = options.get('customer_id')

        if test_mode:
            self._test_send(campaign_id, customer_id)
        elif campaign_id:
            self._send_single(campaign_id)
        else:
            self._send_scheduled()

    def _send_single(self, campaign_id):
        """Bitta kampaniyani jo'natish."""
        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError(f'Kampaniya topilmadi: {campaign_id}')

        self.stdout.write(f"Kampaniya jo'natilyapti: {campaign.name} ({campaign.get_channel_display()})")

        result = CampaignSendService.send_campaign(campaign_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Tugallandi: {result['sent']} yuborildi, {result['failed']} xato"
            )
        )

        if result['errors']:
            self.stdout.write(self.style.WARNING("\nXatolar:"))
            for error in result['errors'][:10]:  # Birinchi 10 ta xato
                self.stdout.write(f"  - {error}")

    def _send_scheduled(self):
        """Barcha rejalashtirylgan kampaniyalarni jo'natish."""
        now = timezone.now()
        campaigns = Campaign.objects.filter(
            status=CampaignStatus.SCHEDULED,
            scheduled_at__lte=now,
        )

        if not campaigns.exists():
            self.stdout.write(self.style.WARNING("Rejalashtirylgan kampaniyalar topilmadi"))
            return

        self.stdout.write(f"Kampaniyalar topildi: {campaigns.count()}")

        for campaign in campaigns:
            self.stdout.write(f"\nKampaniya jo'natilyapti: {campaign.name}")

            result = CampaignSendService.send_campaign(campaign.id)

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ {result['sent']} yuborildi, {result['failed']} xato"
                )
            )

    def _test_send(self, campaign_id, customer_id):
        """Test mode — bitta mijozga jo'natish."""
        if not campaign_id:
            raise CommandError('Test mode uchun campaign_id kerak')

        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError(f'Kampaniya topilmadi: {campaign_id}')

        self.stdout.write(f"Test mode: {campaign.name} ({campaign.get_channel_display()})")

        result = CampaignSendService.test_send(campaign_id, customer_id)

        if result['success']:
            self.stdout.write(self.style.SUCCESS("✓ Test muvaffaqiyatli"))
            self.stdout.write(f"Mijoz: {result['customer']}")
            self.stdout.write(f"Xabar: {result['message']}")
        else:
            self.stdout.write(self.style.ERROR(f"✗ Xato: {result['message']}"))
