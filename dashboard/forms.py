from django import forms
from website.models import SiteSettings, News, Promotion, GalleryItem, Vacancy
from menu.models import Category, Dish

class BootstrapModelForm(forms.ModelForm):
    """
    Barcha maydonlarga Bootstrap class'larini avtomatik qo'shadigan tayanch ModelForm.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
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

class SiteSettingsForm(BootstrapModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'name', 'tagline_uz', 'tagline_ru', 'tagline_en',
            'logo', 'logo_dark', 'favicon', 'about_image',
            'phone_main', 'phone_secondary', 'email',
            'address_uz', 'address_ru', 'address_en', 'city',
            'working_hours_uz', 'working_hours_ru', 'working_hours_en',
            'instagram_url', 'telegram_channel_url', 'telegram_bot_url',
            'latitude', 'longitude', 'map_embed_code',
            'about_text_uz', 'about_text_ru', 'about_text_en',
            'google_verify', 'yandex_verify', 'google_analytics_id'
        ]
        widgets = {
            'map_embed_code': forms.Textarea(attrs={'rows': 3}),
            'about_text_uz': forms.Textarea(attrs={'rows': 4}),
            'about_text_ru': forms.Textarea(attrs={'rows': 4}),
            'about_text_en': forms.Textarea(attrs={'rows': 4}),
        }

class NewsForm(BootstrapModelForm):
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

class PromotionForm(BootstrapModelForm):
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

class GalleryItemForm(BootstrapModelForm):
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

class DishForm(BootstrapModelForm):
    class Meta:
        model = Dish
        fields = [
            'category', 'name_uz', 'name_ru', 'name_en',
            'description_uz', 'description_ru', 'description_en',
            'price', 'image', 'is_available', 'is_active', 'prep_time'
        ]
        widgets = {
            'description_uz': forms.Textarea(attrs={'rows': 3}),
            'description_ru': forms.Textarea(attrs={'rows': 3}),
            'description_en': forms.Textarea(attrs={'rows': 3}),
        }
