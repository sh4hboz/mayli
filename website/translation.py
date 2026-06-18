from modeltranslation.translator import register, TranslationOptions
from .models import SiteSettings, News, Promotion, Vacancy, GalleryItem, TeamMember, Testimonial, Feature, StatItem


@register(SiteSettings)
class SiteSettingsTranslation(TranslationOptions):
    fields = ('tagline', 'address', 'working_hours', 'about_text',
              'hero_title', 'hero_title_accent', 'hero_subtitle',
              'why_us_title',
              'about_title', 'about_badge_label', 'about_features',
              'booking_cta_title', 'booking_cta_desc',
              'about_page_badge', 'about_page_title',
              'home_seo_body', 'about_seo_title', 'about_seo_body')


@register(News)
class NewsTranslation(TranslationOptions):
    fields = ('title', 'body')


@register(Promotion)
class PromotionTranslation(TranslationOptions):
    fields = ('title', 'description')


@register(Vacancy)
class VacancyTranslation(TranslationOptions):
    fields = ('title', 'description', 'requirements', 'salary')


@register(GalleryItem)
class GalleryItemTranslation(TranslationOptions):
    fields = ('caption',)


@register(TeamMember)
class TeamMemberTranslation(TranslationOptions):
    fields = ('position',)


@register(Testimonial)
class TestimonialTranslation(TranslationOptions):
    fields = ('text',)


@register(Feature)
class FeatureTranslation(TranslationOptions):
    fields = ('title', 'text')


@register(StatItem)
class StatItemTranslation(TranslationOptions):
    fields = ('label',)
