from django.core.management.base import BaseCommand
from website.models import SiteSettings, Vacancy, GalleryItem


class Command(BaseCommand):
    help = 'Boshlangich sayt ma\'lumotlarini yaratadi'

    def handle(self, *args, **options):
        site, created = SiteSettings.objects.get_or_create(pk=1)
        site.name = 'Mayli Restobar'
        site.tagline = 'Termizning eng shinam maskanida mazali ta\'mlar'
        site.tagline_ru = 'Вкусные блюда в самом уютном месте Термеза'
        site.tagline_en = 'Delicious flavors in the coziest place in Termez'
        site.phone_main = '+998 (93) 200-80-00'
        site.phone_secondary = '+998 (93) 200-80-01'
        site.address = 'Termiz sh., Katta Ipak Yo\'li ko\'ch., 15'
        site.address_ru = 'г. Термез, ул. Большой шёлковый путь, 15'
        site.address_en = '15 Great Silk Road St., Termez city'
        site.city = 'Termiz'
        site.working_hours = 'Har kuni: 24/7'
        site.working_hours_ru = 'Ежедневно: 24/7'
        site.working_hours_en = 'Daily: 24/7'
        site.instagram_url = 'https://instagram.com/maylirestobar'
        site.telegram_channel_url = 'https://t.me/MayliRestobar'
        site.telegram_bot_url = 'https://t.me/MayliRestobarBot'
        site.latitude = 37.2240
        site.longitude = 67.2780
        site.about_text = (
            'Termiz shahrida joylashgan "Mayli Restobar" — bu nafaqat restoran, '
            'balki har bir mehmon uchun alohida tajriba. '
            'Premium taomlar, ajoyib atmosfera va iliq xizmat bilan sizni kutamiz.'
        )
        site.about_text_ru = (
            '"Mayli Restobar" в Термезе — это не просто ресторан, '
            'а особый опыт для каждого гостя. '
            'Ждём вас с премиальными блюдами, атмосферой и тёплым сервисом.'
        )
        site.about_text_en = (
            '"Mayli Restobar" in Termez is not just a restaurant — '
            'it is a unique experience for every guest. '
            'Premium cuisine, warm atmosphere and excellent service await you.'
        )
        site.save()
        self.stdout.write(self.style.SUCCESS('SiteSettings yaratildi/yangilandi'))

        if not Vacancy.objects.exists():
            Vacancy.objects.create(
                title='Ofitsiant',
                title_ru='Официант',
                title_en='Waiter',
                description='Mehmondo\'st va energik ofitsiant izlaymiz.',
                description_ru='Ищем гостеприимного и энергичного официанта.',
                description_en='We are looking for a hospitable and energetic waiter.',
                salary='3,000,000 – 5,000,000 so\'m',
                salary_ru='3 000 000 – 5 000 000 сум',
                salary_en='3,000,000 – 5,000,000 UZS',
            )
            Vacancy.objects.create(
                title='Oshpaz',
                title_ru='Повар',
                title_en='Chef',
                description='Tajribali oshpaz izlaymiz.',
                description_ru='Ищем опытного повара.',
                description_en='We are looking for an experienced chef.',
                salary='5,000,000 – 8,000,000 so\'m',
                salary_ru='5 000 000 – 8 000 000 сум',
                salary_en='5,000,000 – 8,000,000 UZS',
            )
            self.stdout.write(self.style.SUCCESS('Vakansiyalar yaratildi'))
