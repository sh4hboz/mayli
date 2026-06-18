from django import forms
from website.models import SiteSettings, News, Promotion, GalleryItem, Vacancy, Feature, StatItem
from menu.models import Category, Dish
from crm.models import Customer, Campaign
from .image_utils import convert_image_to_webp


class BootstrapModelForm(forms.ModelForm):
    """
    Barcha maydonlarga Bootstrap class'larini avtomatik qo'shadigan tayanch ModelForm.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                # Checkbox/radio ro'yxati — Bootstrap class kerak emas (template form-check ishlatadi).
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, (forms.FileInput, forms.ClearableFileInput)):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

            # Add is-invalid class if field has errors
            if field_name in self.errors:
                current_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{current_class} is-invalid'


class WebPModelForm(BootstrapModelForm):
    """Rasm maydonli formalar uchun ixtiyoriy WebP siqish.

    `convert_webp` — declared (sinf darajasidagi) checkbox; belgilansa, yangi
    yuklangan rasmni saqlashdan oldin WebP'ga aylantiradi va faqat asl rasmdan
    kichikroq bo'lsa almashtiradi. Natija `self.webp_report`da (view ko'rsatadi).
    Mavjud (saqlangan) rasmlarga tegmaydi.
    """
    convert_webp = forms.BooleanField(
        required=False,
        initial=True,
        label="Rasmni WebP'ga siqish (kichikroq bo'lsa)",
        help_text="Yangi yuklangan rasm WebP'ga aylantiriladi; faqat asl rasmdan kichik bo'lsa almashtiriladi.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, **kwargs):
        # BootstrapModelForm.__init__ self.errors'ga murojaat qiladi → full_clean
        # (clean) __init__ ichida ishga tushadi, shuning uchun report'ni oldin yaratamiz.
        self.webp_report = []
        super().__init__(*args, **kwargs)

    def _webp_image_fields(self):
        return [n for n, f in self.fields.items() if isinstance(f, forms.ImageField)]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('convert_webp'):
            for name in self._webp_image_fields():
                f = cleaned.get(name)
                # Faqat yangi yuklangan fayl (UploadedFile'da content_type bor) —
                # mavjud saqlangan rasm (FieldFile) yoki bo'sh qiymatga tegmaymiz.
                if f and hasattr(f, 'content_type'):
                    result = convert_image_to_webp(f)
                    cleaned[name] = result['file']
                    result['label'] = self.fields[name].label or name
                    self.webp_report.append(result)
        return cleaned


class SiteSettingsForm(BootstrapModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'name', 'tagline_uz', 'tagline_ru', 'tagline_en',
            'logo', 'logo_dark', 'favicon', 'about_image',
            'hero_bg_image', 'hero_video',
            'hero_title_uz', 'hero_title_ru', 'hero_title_en',
            'hero_title_accent_uz', 'hero_title_accent_ru', 'hero_title_accent_en',
            'hero_subtitle_uz', 'hero_subtitle_ru', 'hero_subtitle_en',
            'why_us_title_uz', 'why_us_title_ru', 'why_us_title_en',
            'phone_main', 'phone_secondary', 'email',
            'address_uz', 'address_ru', 'address_en', 'city',
            'working_hours_uz', 'working_hours_ru', 'working_hours_en',
            'instagram_url', 'telegram_channel_url', 'telegram_bot_url',
            'latitude', 'longitude', 'map_embed_code',
            'about_text_uz', 'about_text_ru', 'about_text_en',
            'about_title_uz', 'about_title_ru', 'about_title_en',
            'about_badge_value',
            'about_badge_label_uz', 'about_badge_label_ru', 'about_badge_label_en',
            'about_features_uz', 'about_features_ru', 'about_features_en',
            'booking_cta_title_uz', 'booking_cta_title_ru', 'booking_cta_title_en',
            'booking_cta_desc_uz', 'booking_cta_desc_ru', 'booking_cta_desc_en',
            'about_page_badge_uz', 'about_page_badge_ru', 'about_page_badge_en',
            'about_page_title_uz', 'about_page_title_ru', 'about_page_title_en',
            'home_seo_body_uz', 'home_seo_body_ru', 'home_seo_body_en',
            'about_seo_title_uz', 'about_seo_title_ru', 'about_seo_title_en',
            'about_seo_body_uz', 'about_seo_body_ru', 'about_seo_body_en',
            'google_verify', 'yandex_verify', 'google_analytics_id'
        ]
        widgets = {
            'map_embed_code': forms.Textarea(attrs={'rows': 3}),
            'about_text_uz': forms.Textarea(attrs={'rows': 4}),
            'about_text_ru': forms.Textarea(attrs={'rows': 4}),
            'about_text_en': forms.Textarea(attrs={'rows': 4}),
            'hero_subtitle_uz': forms.Textarea(attrs={'rows': 2}),
            'hero_subtitle_ru': forms.Textarea(attrs={'rows': 2}),
            'hero_subtitle_en': forms.Textarea(attrs={'rows': 2}),
            'hero_video': forms.ClearableFileInput(attrs={'accept': 'video/mp4,video/webm'}),
            'home_seo_body_uz': forms.Textarea(attrs={'rows': 12}),
            'home_seo_body_ru': forms.Textarea(attrs={'rows': 12}),
            'home_seo_body_en': forms.Textarea(attrs={'rows': 12}),
            'about_seo_body_uz': forms.Textarea(attrs={'rows': 12}),
            'about_seo_body_ru': forms.Textarea(attrs={'rows': 12}),
            'about_seo_body_en': forms.Textarea(attrs={'rows': 12}),
            'about_features_uz': forms.Textarea(attrs={'rows': 5}),
            'about_features_ru': forms.Textarea(attrs={'rows': 5}),
            'about_features_en': forms.Textarea(attrs={'rows': 5}),
            'booking_cta_desc_uz': forms.Textarea(attrs={'rows': 2}),
            'booking_cta_desc_ru': forms.Textarea(attrs={'rows': 2}),
            'booking_cta_desc_en': forms.Textarea(attrs={'rows': 2}),
        }

class NewsForm(WebPModelForm):
    class Meta:
        model = News
        fields = [
            'title_uz', 'title_ru', 'title_en',
            'body_uz', 'body_ru', 'body_en',
            'image', 'is_active'
        ]
        widgets = {
            'body_uz': forms.Textarea(attrs={'rows': 5}),
            'body_ru': forms.Textarea(attrs={'rows': 5}),
            'body_en': forms.Textarea(attrs={'rows': 5}),
        }

class PromotionForm(WebPModelForm):
    class Meta:
        model = Promotion
        fields = [
            'title_uz', 'title_ru', 'title_en',
            'description_uz', 'description_ru', 'description_en',
            'image', 'valid_until', 'is_active'
        ]
        widgets = {
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
            'description_uz': forms.Textarea(attrs={'rows': 4}),
            'description_ru': forms.Textarea(attrs={'rows': 4}),
            'description_en': forms.Textarea(attrs={'rows': 4}),
        }

class GalleryItemForm(WebPModelForm):
    class Meta:
        model = GalleryItem
        fields = ['image', 'caption_uz', 'caption_ru', 'caption_en', 'order', 'is_active']

class VacancyForm(BootstrapModelForm):
    class Meta:
        model = Vacancy
        fields = [
            'title_uz', 'title_ru', 'title_en',
            'description_uz', 'description_ru', 'description_en',
            'requirements_uz', 'requirements_ru', 'requirements_en',
            'salary_uz', 'salary_ru', 'salary_en',
            'is_active'
        ]
        widgets = {
            'description_uz': forms.Textarea(attrs={'rows': 4}),
            'description_ru': forms.Textarea(attrs={'rows': 4}),
            'description_en': forms.Textarea(attrs={'rows': 4}),
            'requirements_uz': forms.Textarea(attrs={'rows': 4}),
            'requirements_ru': forms.Textarea(attrs={'rows': 4}),
            'requirements_en': forms.Textarea(attrs={'rows': 4}),
        }

class CategoryForm(BootstrapModelForm):
    class Meta:
        model = Category
        fields = ['name_uz', 'name_ru', 'name_en', 'order', 'is_active']

class DishForm(WebPModelForm):
    class Meta:
        model = Dish
        fields = [
            'categories', 'name_uz', 'name_ru', 'name_en',
            'description_uz', 'description_ru', 'description_en',
            'price', 'image', 'is_available', 'is_active', 'prep_time'
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'description_uz': forms.Textarea(attrs={'rows': 3}),
            'description_ru': forms.Textarea(attrs={'rows': 3}),
            'description_en': forms.Textarea(attrs={'rows': 3}),
        }


class CustomerForm(BootstrapModelForm):
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'phone', 'birth_date', 'gender',
            'email', 'telegram_username',
            'source', 'tags',
            'sms_consent', 'email_consent', 'telegram_consent',
            'notes', 'is_active',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class CampaignForm(BootstrapModelForm):
    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'channel', 'template', 'sms_template_id',
            'tags', 'status', 'scheduled_at',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'template': forms.Textarea(attrs={'rows': 5}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        help_texts = {
            'template': 'Shablon: {{first_name}}, {{full_name}}, {{phone}} ishlatish mumkin',
            'sms_template_id': 'Faqat SMS uchun: TextUp kabinetidagi tasdiqlangan shablonning templateId\'si.',
        }


class StatItemForm(BootstrapModelForm):
    class Meta:
        model = StatItem
        fields = [
            'value',
            'label_uz', 'label_ru', 'label_en',
            'placement', 'order', 'is_active',
        ]
        help_texts = {
            'value': 'Raqam qiymati (masalan: 5+, 200+, 10 000+, 24/7)',
            'placement': 'Qayerda ko\'rsatilsin',
        }


class FeatureForm(BootstrapModelForm):
    class Meta:
        model = Feature
        fields = [
            'icon',
            'title_uz', 'title_ru', 'title_en',
            'text_uz', 'text_ru', 'text_en',
            'order', 'is_active',
        ]
        widgets = {
            'text_uz': forms.Textarea(attrs={'rows': 3}),
            'text_ru': forms.Textarea(attrs={'rows': 3}),
            'text_en': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={'placeholder': 'fa-leaf'}),
        }
        help_texts = {
            'icon': 'Font Awesome icon class (masalan: fa-leaf, fa-trophy, fa-smile-o, fa-music)',
        }

