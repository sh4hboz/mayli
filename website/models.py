import secrets

from django.db import models
from core.models import TimeStampedModel

# Chalkash belgilarsiz alfavit (0/o, 1/l/i kabilarsiz) — qisqa random slug uchun
_SLUG_ALPHABET = 'abcdefghijkmnpqrstuvwxyz23456789'


def random_news_slug():
    """Qisqa, noyob random slug: masalan 'k7p2-x9m'."""
    pick = lambda n: ''.join(secrets.choice(_SLUG_ALPHABET) for _ in range(n))
    return f"{pick(4)}-{pick(3)}"


class SiteSettings(models.Model):
    name = models.CharField(max_length=100, default='Mayli Restobar')
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    logo_dark = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    hero_bg_image = models.ImageField(upload_to='site/', blank=True, null=True)
    # Hero video (mp4): sahifa to'liq yuklangach rasm o'rniga auto-play bo'ladi.
    # Bo'sh bo'lsa — faqat hero_bg_image (rasm) ko'rinadi.
    hero_video = models.FileField(upload_to='site/', blank=True, null=True)
    # Hero matnlari (uch tilli — modeltranslation). Bo'sh bo'lsa template default'i ishlaydi.
    hero_title = models.CharField(max_length=200, blank=True)
    hero_title_accent = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.TextField(blank=True)
    why_us_title = models.CharField(max_length=200, blank=True)

    phone_main = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, default='Termiz')
    working_hours = models.CharField(max_length=200, blank=True)

    instagram_url = models.URLField(blank=True)
    instagram_title = models.CharField(max_length=100, blank=True, default='Instagram')
    instagram_active = models.BooleanField(default=True)

    telegram_channel_url = models.URLField(blank=True)
    telegram_channel_title = models.CharField(max_length=100, blank=True, default='Telegram Channel')
    telegram_channel_active = models.BooleanField(default=True)

    telegram_bot_url = models.URLField(blank=True)
    telegram_bot_title = models.CharField(max_length=100, blank=True, default='Telegram Bot')
    telegram_bot_active = models.BooleanField(default=True)

    latitude = models.FloatField(default=37.224)
    longitude = models.FloatField(default=67.278)
    map_embed_code = models.TextField(blank=True)

    about_text = models.TextField(blank=True)
    about_image = models.ImageField(upload_to='site/', blank=True, null=True)
    about_title = models.CharField(max_length=200, blank=True)
    about_badge_value = models.CharField(max_length=20, blank=True)
    about_badge_label = models.CharField(max_length=100, blank=True)
    about_features = models.TextField(
        blank=True,
        help_text='Har qator bitta xususiyat (checkmark qatori). Bo\'sh qoldirilsa — default 4 ta qator.'
    )
    booking_cta_title = models.CharField(max_length=200, blank=True)
    booking_cta_desc = models.TextField(blank=True)
    about_page_badge = models.CharField(max_length=100, blank=True)
    about_page_title = models.CharField(max_length=200, blank=True)
    home_seo_body = models.TextField(blank=True)
    about_seo_title = models.CharField(max_length=300, blank=True)
    about_seo_body = models.TextField(blank=True)

    google_verify = models.CharField(max_length=200, blank=True)
    yandex_verify = models.CharField(max_length=200, blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    yandex_metrica_id = models.CharField(max_length=20, blank=True)

    # Dashboard ko'rinishini sozlash uchun custom CSS (dashboard sahifalariga <style> sifatida qo'shiladi)
    dashboard_custom_css = models.TextField('Dashboard custom CSS', blank=True)

    class Meta:
        verbose_name = 'Sayt sozlamalari'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return self.name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class News(TimeStampedModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Yangilik'
        verbose_name_plural = 'Yangiliklar'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = random_news_slug()
            while News.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = random_news_slug()
            self.slug = slug
        super().save(*args, **kwargs)


class Promotion(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='promotions/', blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Aksiya'
        verbose_name_plural = 'Aksiyalar'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class GalleryItem(TimeStampedModel):
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Galereya'
        verbose_name_plural = 'Galereya'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.caption or f'Rasm #{self.pk}'


class Partner(TimeStampedModel):
    name = models.CharField('Nomi', max_length=120, blank=True)
    logo = models.ImageField('Logo', upload_to='partners/')
    url = models.URLField('Sayt havolasi', blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Hamkor'
        verbose_name_plural = 'Hamkorlar'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.name or f'Hamkor #{self.pk}'


class TeamMember(TimeStampedModel):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Jamoa a\'zosi'
        verbose_name_plural = 'Jamoa'
        ordering = ['order']

    def __str__(self):
        return self.name


class Testimonial(TimeStampedModel):
    author = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author} — {self.rating}★'


class Vacancy(TimeStampedModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    salary = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Vakansiya'
        verbose_name_plural = 'Vakansiyalar'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class JobApplication(TimeStampedModel):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='applications')
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ariza'
        verbose_name_plural = 'Arizalar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} — {self.phone}'


class StatItem(TimeStampedModel):
    PLACEMENT_HERO = 'hero'
    PLACEMENT_STATS = 'stats'
    PLACEMENT_BOTH = 'both'
    PLACEMENT_CHOICES = [
        (PLACEMENT_HERO, 'Faqat Hero (bosh ekran)'),
        (PLACEMENT_STATS, 'Faqat Statistika seksiyasi'),
        (PLACEMENT_BOTH, 'Ikkalasida ham'),
    ]

    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    placement = models.CharField(max_length=10, choices=PLACEMENT_CHOICES, default=PLACEMENT_BOTH)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Statistika'
        verbose_name_plural = 'Statistikalar'
        ordering = ['order']

    def __str__(self):
        return f'{self.value} — {self.label}'


class Feature(TimeStampedModel):
    icon = models.CharField(
        max_length=100, default='fa-check-circle',
        help_text='Font Awesome icon class (masalan: fa-leaf, fa-trophy)'
    )
    title = models.CharField(max_length=200)
    text = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Xususiyat (Nega biz?)'
        verbose_name_plural = 'Xususiyatlar (Nega biz?)'
        ordering = ['order']

    def __str__(self):
        return self.title


class ContactMessage(TimeStampedModel):
    KIND_MESSAGE = 'message'
    KIND_BOOKING = 'booking'
    KIND_CHOICES = [
        (KIND_MESSAGE, 'Murojaat'),
        (KIND_BOOKING, 'Bron so\'rovi'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_MESSAGE)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Xabar'
        verbose_name_plural = 'Xabarlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.message[:60]}'
