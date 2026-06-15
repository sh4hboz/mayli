from django.db import models
from django.utils.text import slugify
from core.models import TimeStampedModel


class SiteSettings(models.Model):
    name = models.CharField(max_length=100, default='Mayli Restobar')
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    logo_dark = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    hero_bg_image = models.ImageField(upload_to='site/', blank=True, null=True)

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

    google_verify = models.CharField(max_length=200, blank=True)
    yandex_verify = models.CharField(max_length=200, blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    yandex_metrica_id = models.CharField(max_length=20, blank=True)

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
            self.slug = slugify(self.title)
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
