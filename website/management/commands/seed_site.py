from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from website.models import SiteSettings, Vacancy, GalleryItem, News


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

        if not News.objects.exists():
            news1 = News.objects.create(
                title='Yangi premium kalyan menyusi taqdimoti',
                body='Mayli Restobar mehmonlari uchun yangi premium kalyan kolleksiyasini taqdim etadi. Menyuga dunyoning mashhur tamaki brendlaridan tanlangan yangi ta\'mlar qo\'shildi. Endi mehmonlar klassik mevali aromatlar bilan bir qatorda eksklyuziv mualliflik mikslarini ham sinab ko\'rishlari mumkin.\n\nYangi menyu tajribali kalyan ustalari tomonidan ishlab chiqilgan bo\'lib, har bir kombinatsiya uzoq davom etuvchi va boy ta\'m hissiyotlarini taqdim etadi. Yangilikni har kuni soat 12:00 dan 02:00 gacha sinab ko\'rishingiz mumkin.',
                is_active=True,
            )
            News.objects.filter(pk=news1.pk).update(created_at=timezone.make_aware(datetime(2026, 6, 12, 12, 0, 0)))

            news2 = News.objects.create(
                title='Jonli musiqa oqshomlari boshlandi',
                body='Mayli Restobarda har juma va shanba kunlari jonli musiqa dasturlari o\'tkazilmoqda. Professional musiqachilar va xonandalar ijrosidagi mashhur kompozitsiyalar mehmonlarga unutilmas kayfiyat ulashadi.\n\nMazali taomlar, mualliflik ichimliklari va sifatli musiqa uyg\'unligi dam olish kunlarini yanada maroqli o\'tkazishga yordam beradi. Tadbirlar uchun oldindan stol band qilish tavsiya etiladi.',
                is_active=True,
            )
            News.objects.filter(pk=news2.pk).update(created_at=timezone.make_aware(datetime(2026, 5, 28, 18, 30, 0)))

            news3 = News.objects.create(
                title='Yangi yozgi menyu taqdim etildi',
                body='Yoz mavsumi munosabati bilan Mayli Restobar menyusi yangi taomlar bilan boyitildi. Oshpazlarimiz tomonidan tayyorlangan yengil salatlar, grilda pishirilgan taomlar va mavsumiy desertlar mehmonlar e\'tiboriga havola etiladi.\n\nYangi taomlar mahalliy va sifatli mahsulotlardan tayyorlanib, yozgi kayfiyatni aks ettiruvchi maxsus ta\'mlar bilan boyitilgan. Barcha yangiliklar bugundan boshlab buyurtma uchun mavjud.',
                is_active=True,
            )
            News.objects.filter(pk=news3.pk).update(created_at=timezone.make_aware(datetime(2026, 6, 3, 10, 15, 0)))

            self.stdout.write(self.style.SUCCESS('Yangiliklar yaratildi'))
