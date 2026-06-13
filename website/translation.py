from modeltranslation.translator import register, TranslationOptions
from .models import SiteSettings, News, Promotion, Vacancy, GalleryItem, TeamMember, Testimonial


@register(SiteSettings)
class SiteSettingsTranslation(TranslationOptions):
    fields = ('tagline', 'address', 'working_hours', 'about_text')


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
