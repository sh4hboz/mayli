import os
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, Sum, Avg, Max, DecimalField
from django.db.models.functions import TruncMonth, ExtractDay, Coalesce
from django.utils import timezone
from datetime import date

from accounts.models import Role
from website.models import SiteSettings, News, Promotion, GalleryItem, Partner, Vacancy, JobApplication, ContactMessage, Feature, StatItem
from menu.models import Category, Dish
from crm.models import Customer, Tag, Gender, CustomerSource, Campaign, CampaignLog, LoyaltySettings, LoyaltyTransaction
from notifications.models import ChatSession, ChatMessage
from orders.models import Order, OrderStatus, OrderSettings
from .forms import (
    SiteSettingsGeneralForm, SiteSettingsLocationForm, SiteSettingsHeroForm,
    SiteSettingsHomeContentForm, SiteSettingsSeoForm,
    NewsForm, PromotionForm, GalleryItemForm, PartnerForm, VacancyForm, CategoryForm,
    DishForm, CustomerForm, CampaignForm, FeatureForm, StatItemForm, OrderSettingsForm,
    LoyaltySettingsForm,
)
from .search import global_search, CMS_ROLES


@login_required(login_url='/login/')
def dashboard_home(request):
    stats = {
        'news_count': News.objects.count(),
        'news_active': News.objects.filter(is_active=True).count(),
        'promo_count': Promotion.objects.count(),
        'promo_active': Promotion.objects.filter(is_active=True).count(),
        'gallery_count': GalleryItem.objects.filter(is_active=True).count(),
        'vacancy_count': Vacancy.objects.count(),
        'vacancy_active': Vacancy.objects.filter(is_active=True).count(),
        'unread_contacts': ContactMessage.objects.filter(is_read=False).count(),
        'new_applications': JobApplication.objects.count(),
        'customers_count': Customer.objects.count(),
    }
    recent_contacts = ContactMessage.objects.order_by('-created_at')[:5]

    # ── Analitika (apexcharts uchun) ──────────────────────────────
    today = timezone.localdate()

    # 1) Oxirgi 6 oydagi yangi mijozlar
    months = []
    yy, mm = today.year, today.month
    for _ in range(6):
        months.append((yy, mm))
        mm -= 1
        if mm == 0:
            mm, yy = 12, yy - 1
    months.reverse()
    start_y, start_m = months[0]
    monthly_raw = (
        Customer.objects
        .filter(created_at__date__gte=date(start_y, start_m, 1))
        .annotate(mon=TruncMonth('created_at'))
        .values('mon').annotate(c=Count('id'))
    )
    monthly_map = {(r['mon'].year, r['mon'].month): r['c'] for r in monthly_raw}
    uz_months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
    monthly = {
        'labels': [f"{uz_months[m - 1]} {y}" for (y, m) in months],
        'data': [monthly_map.get((y, m), 0) for (y, m) in months],
    }

    # 2) Mijoz manbalari taqsimoti
    source_labels = dict(CustomerSource.choices)
    src_raw = Customer.objects.values('source').annotate(c=Count('id')).order_by('-c')
    sources = {
        'labels': [str(source_labels.get(r['source'], r['source'])) for r in src_raw],
        'data': [r['c'] for r in src_raw],
    }

    # 3) So'nggi 6 kampaniya samarasi
    camp_qs = list(Campaign.objects.order_by('-created_at')[:6])[::-1]
    campaigns = {
        'labels': [c.name for c in camp_qs],
        'sent': [c.sent_count for c in camp_qs],
        'failed': [c.failed_count for c in camp_qs],
    }

    # 4) Buyurtma dinamikasi — oxirgi 6 oy (soni + daromad)
    revenue_statuses = (OrderStatus.ACCEPTED, OrderStatus.COMPLETED)
    orders_monthly_raw = (
        Order.objects
        .filter(created_at__date__gte=date(start_y, start_m, 1))
        .annotate(mon=TruncMonth('created_at'))
        .values('mon')
        .annotate(
            cnt=Count('id'),
            revenue=Coalesce(
                Sum('total_amount', filter=Q(status__in=revenue_statuses)),
                Decimal('0'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
    )
    om_cnt = {(r['mon'].year, r['mon'].month): r['cnt'] for r in orders_monthly_raw}
    om_rev = {(r['mon'].year, r['mon'].month): float(r['revenue']) for r in orders_monthly_raw}
    orders_monthly = {
        'labels': [f"{uz_months[m - 1]} {y}" for (y, m) in months],
        'counts': [om_cnt.get((y, m), 0) for (y, m) in months],
        'revenue': [round(om_rev.get((y, m), 0)) for (y, m) in months],
    }

    # 5) Buyurtma holatlari taqsimoti (faqat mavjud holatlar)
    status_labels = dict(OrderStatus.choices)
    ostat_map = {r['status']: r['c'] for r in Order.objects.values('status').annotate(c=Count('id'))}
    order_statuses = {
        'labels': [str(status_labels[s]) for s, _ in OrderStatus.choices if ostat_map.get(s)],
        'data': [ostat_map[s] for s, _ in OrderStatus.choices if ostat_map.get(s)],
    }

    analytics = {
        'monthly': monthly, 'sources': sources, 'campaigns': campaigns,
        'orders': orders_monthly, 'order_statuses': order_statuses,
    }

    # 4) Shu oyda tug'ilgan mijozlar
    birthdays = (
        Customer.objects
        .filter(birth_date__month=today.month, is_active=True)
        .annotate(bday=ExtractDay('birth_date')).order_by('bday')
    )

    return render(request, 'management/dashboard.html', {
        'profile': request.user,
        'stats': stats,
        'recent_contacts': recent_contacts,
        'analytics': analytics,
        'birthdays': birthdays,
    })


# --- CMS views-lar uchun Mixin base ---
class CMSBaseMixin(LoginRequiredMixin):
    """
    Barcha CMS view'lari uchun tayanch sinf.
    - Faqat OWNER, MANAGER, ADMIN role'lari ruxsat oladi.
    - Context-ga profile (request.user) ni qo'shadi.
    """
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = self.request.user
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        allowed_roles = [Role.OWNER, Role.MANAGER, Role.ADMIN]
        if request.user.role not in allowed_roles:
            raise PermissionDenied(f"Ruxsat yo'q! Faqat {', '.join([str(r[1]) for r in Role.choices if r[0] in allowed_roles])} dashboard'ga kira oladi.")

        return super().dispatch(request, *args, **kwargs)


class SuccessMessageMixin:
    """CRUD operatsiyalari uchun success message'lar."""
    success_message_create = "{} muvaffaqiyatli qo'shildi."
    success_message_update = "{} muvaffaqiyatli yangilandi."
    success_message_delete = "{} muvaffaqiyatli o'chirildi."

    def get_success_message(self, cleaned_data=None):
        return self.success_message_create.format(self.model._meta.verbose_name)

    def form_valid(self, form):
        if isinstance(self, CreateView):
            msg = self.success_message_create.format(self.model._meta.verbose_name)
        elif isinstance(self, UpdateView):
            msg = self.success_message_update.format(self.model._meta.verbose_name)
        else:
            msg = self.success_message_create
        messages.success(self.request, msg)
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        msg = self.success_message_delete.format(self.model._meta.verbose_name)
        messages.success(request, msg)
        return super().delete(request, *args, **kwargs)


class WebPReportMixin:
    """Forma `webp_report`idan rasm WebP siqish natijalarini message ko'rsatadi."""

    def form_valid(self, form):
        response = super().form_valid(form)
        for r in getattr(form, 'webp_report', []):
            label = r.get('label') or 'Rasm'
            orig_kb = round(r['original_size'] / 1024)
            if r.get('reason') == 'converted':
                webp_kb = round(r['webp_size'] / 1024)
                messages.success(
                    self.request,
                    f"{label}: WebP'ga siqildi — {r['saved_pct']}% tejaldi "
                    f"({orig_kb} KB → {webp_kb} KB).",
                )
            elif r.get('reason') == 'webp_larger':
                messages.info(
                    self.request,
                    f"{label}: asl rasm saqlandi (WebP kattaroq chiqdi).",
                )
        return response


# --- Sayt sozlamalari (Site Settings) — 5 ta alohida bo'lim ---
class SiteSettingsSectionView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    """Sayt sozlamalarining bitta bo'limi uchun tayanch view.

    Hammasi bitta SiteSettings (singleton) ni tahrirlaydi; har bo'lim faqat
    o'z formasidagi maydonlarni saqlaydi. `active_tab` — yuqoridagi bo'lim
    navigatsiyasida joriy bo'limni belgilash uchun.
    """
    model = SiteSettings
    active_tab = ''
    success_message_update = "Sozlamalar saqlandi."

    def get_object(self, queryset=None):
        return SiteSettings.get()

    def get_success_message(self, cleaned_data=None):
        return self.success_message_update

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = self.active_tab
        return ctx


class SiteSettingsGeneralView(SiteSettingsSectionView):
    form_class = SiteSettingsGeneralForm
    template_name = 'management/website/settings.html'
    success_url = reverse_lazy('dashboard_settings_website')
    active_tab = 'general'


class SiteSettingsLocationView(SiteSettingsSectionView):
    form_class = SiteSettingsLocationForm
    template_name = 'management/website/settings_location.html'
    success_url = reverse_lazy('dashboard_settings_location')
    active_tab = 'location'


class SiteSettingsHeroView(SiteSettingsSectionView):
    form_class = SiteSettingsHeroForm
    template_name = 'management/website/settings_hero.html'
    success_url = reverse_lazy('dashboard_settings_hero')
    active_tab = 'hero'


class SiteSettingsHomeContentView(SiteSettingsSectionView):
    form_class = SiteSettingsHomeContentForm
    template_name = 'management/website/settings_home.html'
    success_url = reverse_lazy('dashboard_settings_home')
    active_tab = 'home'


class SiteSettingsSeoView(SiteSettingsSectionView):
    form_class = SiteSettingsSeoForm
    template_name = 'management/website/settings_seo.html'
    success_url = reverse_lazy('dashboard_settings_seo')
    active_tab = 'seo'


# --- Custom CSS (media/css/ ichidagi fayllarni dashboarddan tahrirlash) ---
CUSTOM_CSS_FILES = {
    'site': 'css/site.css',
    'dashboard': 'css/dashboard.css',
}
CSS_SEED_DIR = os.path.join(settings.BASE_DIR, 'dashboard', 'css_seeds')


def _custom_css_read(key):
    """media/css/<key>.css ni o'qiydi; yo'q bo'lsa repo seed'iga qaytadi."""
    rel = CUSTOM_CSS_FILES[key]
    path = os.path.join(settings.MEDIA_ROOT, rel)
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    seed = os.path.join(CSS_SEED_DIR, os.path.basename(rel))
    if os.path.exists(seed):
        with open(seed, encoding='utf-8') as f:
            return f.read()
    return ''


def _custom_css_write(key, content):
    rel = CUSTOM_CSS_FILES[key]
    path = os.path.join(settings.MEDIA_ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write((content or '').replace('\r\n', '\n'))


class DashboardCustomCssView(CMSBaseMixin, TemplateView):
    """Sayt va dashboard custom CSS fayllarini (media/css/) tahrirlash."""
    template_name = 'management/website/settings_custom_css.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'css'
        ctx['site_css'] = _custom_css_read('site')
        ctx['dashboard_css'] = _custom_css_read('dashboard')
        return ctx

    def post(self, request, *args, **kwargs):
        _custom_css_write('site', request.POST.get('site_css', ''))
        _custom_css_write('dashboard', request.POST.get('dashboard_css', ''))
        messages.success(request, "Custom CSS saqlandi.")
        return redirect('dashboard_custom_css')


# --- Yangiliklar (News) ---
class NewsListView(CMSBaseMixin, ListView):
    model = News
    template_name = 'management/website/news_list.html'
    context_object_name = 'news_list'


class NewsCreateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'management/website/news_form.html'
    success_url = reverse_lazy('dashboard_news_list')


class NewsUpdateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'management/website/news_form.html'
    success_url = reverse_lazy('dashboard_news_list')


class NewsDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = News
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_news_list')


# --- Aksiyalar (Promotions) ---
class PromotionListView(CMSBaseMixin, ListView):
    model = Promotion
    template_name = 'management/website/promotion_list.html'
    context_object_name = 'promotion_list'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Bitta shablonda yangiliklar va aksiyalarni boshqarish qulay bo'lishi uchun
        return ctx


class PromotionCreateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'management/website/promotion_form.html'
    success_url = reverse_lazy('dashboard_promotion_list')


class PromotionUpdateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'management/website/promotion_form.html'
    success_url = reverse_lazy('dashboard_promotion_list')


class PromotionDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Promotion
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_promotion_list')


# --- Galereya (Gallery) ---
class GalleryItemListView(CMSBaseMixin, ListView):
    model = GalleryItem
    template_name = 'management/website/gallery_list.html'
    context_object_name = 'gallery_list'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = GalleryItemForm()
        return ctx


class GalleryItemCreateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, CreateView):
    model = GalleryItem
    form_class = GalleryItemForm
    template_name = 'management/website/gallery_list.html'
    success_url = reverse_lazy('dashboard_gallery_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['gallery_list'] = GalleryItem.objects.all()
        return ctx


class GalleryItemDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = GalleryItem
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_gallery_list')


# --- Hamkorlar (Partners) ---
class PartnerListView(CMSBaseMixin, ListView):
    model = Partner
    template_name = 'management/website/partner_list.html'
    context_object_name = 'partner_list'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = PartnerForm()
        return ctx


class PartnerCreateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, CreateView):
    model = Partner
    form_class = PartnerForm
    template_name = 'management/website/partner_list.html'
    success_url = reverse_lazy('dashboard_partner_list')
    success_message = "Hamkor qo'shildi"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['partner_list'] = Partner.objects.all()
        return ctx


class PartnerDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Partner
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_partner_list')
    success_message = "Hamkor o'chirildi"


# --- Vakansiyalar (Vacancies) ---
class VacancyListView(CMSBaseMixin, ListView):
    model = Vacancy
    template_name = 'management/website/vacancy_list.html'
    context_object_name = 'vacancy_list'


class VacancyCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/website/vacancy_form.html'
    success_url = reverse_lazy('dashboard_vacancy_list')


class VacancyUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/website/vacancy_form.html'
    success_url = reverse_lazy('dashboard_vacancy_list')


class VacancyDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Vacancy
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_vacancy_list')


# --- Arizalar (Job Applications) ---
class JobApplicationListView(CMSBaseMixin, ListView):
    model = JobApplication
    template_name = 'management/website/applications_list.html'
    context_object_name = 'applications_list'


class JobApplicationDetailView(CMSBaseMixin, DetailView):
    model = JobApplication
    template_name = 'management/website/application_detail.html'
    context_object_name = 'application'


class JobApplicationDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = JobApplication
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_application_list')


# --- Murojaatlar (Contact Messages) ---
class ContactMessageListView(CMSBaseMixin, ListView):
    model = ContactMessage
    template_name = 'management/website/contacts_list.html'
    context_object_name = 'contacts_list'


class ContactMessageDetailView(CMSBaseMixin, DetailView):
    model = ContactMessage
    template_name = 'management/website/contact_detail.html'
    context_object_name = 'message'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return obj


class ContactMessageToggleReadView(CMSBaseMixin, UpdateView):
    model = ContactMessage

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(ContactMessage, pk=kwargs.get('pk'))
        obj.is_read = not obj.is_read
        obj.save(update_fields=['is_read'])
        return JsonResponse({'success': True, 'is_read': obj.is_read})


class ContactMessageDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = ContactMessage
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_contact_list')


from django.apps import apps
from django.views.decorators.http import require_POST, require_GET

@login_required(login_url='/login/')
@require_POST
def toggle_active_ajax(request, app_label, model_name, pk):
    """
    Istalgan modeldagi is_active yoki boshqa boolean maydonini AJAX orqali o'zgartiruvchi universal view.
    """
    if request.user.role == Role.ACCOUNTANT:
        return JsonResponse({'success': False, 'error': "Bugalter ma'lumotlarni o'zgartira olmaydi!"}, status=403)
        
    field_name = request.GET.get('field', 'is_active')
    if field_name not in ('is_active', 'is_available'):
        return JsonResponse({'success': False, 'error': "Noto'g'ri maydon nomi!"}, status=400)
        
    try:
        model = apps.get_model(app_label, model_name)
        obj = model.objects.get(pk=pk)
        if hasattr(obj, field_name):
            current_val = getattr(obj, field_name)
            setattr(obj, field_name, not current_val)
            obj.save(update_fields=[field_name])
            return JsonResponse({'success': True, field_name: getattr(obj, field_name)})
        return JsonResponse({'success': False, 'error': f"Modelda {field_name} maydoni mavjud emas!"}, status=400)
    except LookupError:
        return JsonResponse({'success': False, 'error': "Model topilmadi!"}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=404)


# --- Kategoriyalar Boshqaruvi ---
class CategoryListView(CMSBaseMixin, ListView):
    model = Category
    template_name = 'management/menu/category_list.html'
    context_object_name = 'category_list'


class CategoryCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'management/menu/category_form.html'
    success_url = reverse_lazy('dashboard_category_list')


class CategoryUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'management/menu/category_form.html'
    success_url = reverse_lazy('dashboard_category_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category_dishes'] = self.object.dishes.all().order_by('name_uz')
        return ctx


class CategoryDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_category_list')


# --- Taomlar Boshqaruvi ---
class DishListView(CMSBaseMixin, ListView):
    model = Dish
    template_name = 'management/menu/dish_list.html'
    context_object_name = 'dish_list'

    def get_queryset(self):
        # Barcha taom DOM'ga chiqadi; filtr/sort ustun-darajasida client-side (DataTables).
        return super().get_queryset().prefetch_related('categories')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Kategoriya ustuni filtri (dropdown) opsiyalari uchun.
        ctx['all_categories'] = Category.objects.all()
        return ctx


class DishCreateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    success_url = reverse_lazy('dashboard_dish_list')


class DishUpdateView(CMSBaseMixin, WebPReportMixin, SuccessMessageMixin, UpdateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    success_url = reverse_lazy('dashboard_dish_list')


class DishDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Dish
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_dish_list')


# --- Mijozlar CRM ---
class CustomerListView(CMSBaseMixin, ListView):
    model = Customer
    template_name = 'management/crm/customer_list.html'
    context_object_name = 'customer_list'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('tags')
        q = self.request.GET.get('q', '').strip()
        gender = self.request.GET.get('gender', '')
        source = self.request.GET.get('source', '')
        tag = self.request.GET.get('tag', '')
        birth_month = self.request.GET.get('birth_month', '')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q)
            )
        if gender:
            qs = qs.filter(gender=gender)
        if source:
            qs = qs.filter(source=source)
        if tag:
            qs = qs.filter(tags__id=tag)
        if birth_month:
            qs = qs.filter(birth_date__month=birth_month)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['active_gender'] = self.request.GET.get('gender', '')
        ctx['active_source'] = self.request.GET.get('source', '')
        ctx['active_tag'] = self.request.GET.get('tag', '')
        ctx['active_birth_month'] = self.request.GET.get('birth_month', '')
        ctx['genders'] = Gender.choices
        ctx['sources'] = CustomerSource.choices
        ctx['all_tags'] = Tag.objects.all()
        ctx['months'] = [
            (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'),
            (5, 'May'), (6, 'Iyun'), (7, 'Iyul'), (8, 'Avgust'),
            (9, 'Sentabr'), (10, 'Oktabr'), (11, 'Noyabr'), (12, 'Dekabr'),
        ]
        ctx['total_count'] = Customer.objects.count()
        return ctx


class CustomerDetailView(CMSBaseMixin, DetailView):
    model = Customer
    template_name = 'management/crm/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        orders = self.object.orders.all()
        # LTV / o'rtacha chek — faqat "muvaffaqiyatli" buyurtmalar (qabul + yetkazildi)
        done = orders.filter(status__in=(OrderStatus.ACCEPTED, OrderStatus.COMPLETED))
        agg = done.aggregate(ltv=Sum('total_amount'), avg=Avg('total_amount'), cnt=Count('id'))
        ctx['order_stats'] = {
            'total': orders.count(),
            'done': agg['cnt'] or 0,
            'ltv': agg['ltv'] or 0,
            'avg_check': agg['avg'] or 0,
            'last_order': orders.aggregate(m=Max('created_at'))['m'],
        }
        ctx['recent_orders'] = orders.order_by('-created_at')[:10]
        ctx['STATUS'] = OrderStatus
        # Sodiqlik
        ctx['loyalty_enabled'] = LoyaltySettings.get().is_enabled
        ctx['loyalty_tier'] = self.object.loyalty_tier
        ctx['loyalty_txns'] = self.object.loyalty_transactions.select_related('order')[:10]
        return ctx


class CustomerCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'management/crm/customer_form.html'
    success_url = reverse_lazy('dashboard_customer_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CustomerUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'management/crm/customer_form.html'
    success_url = reverse_lazy('dashboard_customer_list')


class CustomerDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Customer
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_customer_list')


# --- Kampaniyalar (Campaigns) ---
class CampaignListView(CMSBaseMixin, ListView):
    model = Campaign
    template_name = 'management/crm/campaign_list.html'
    context_object_name = 'campaign_list'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('tags')
        channel = self.request.GET.get('channel', '')
        status = self.request.GET.get('status', '')
        if channel:
            qs = qs.filter(channel=channel)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from crm.models import CampaignChannel, CampaignStatus
        ctx['channels'] = CampaignChannel.choices
        ctx['statuses'] = CampaignStatus.choices
        ctx['active_channel'] = self.request.GET.get('channel', '')
        ctx['active_status'] = self.request.GET.get('status', '')
        return ctx


class CampaignCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'management/crm/campaign_form.html'
    success_url = reverse_lazy('dashboard_campaign_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class CampaignDetailView(CMSBaseMixin, DetailView):
    model = Campaign
    template_name = 'management/crm/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        campaign = self.get_object()
        ctx['logs'] = campaign.logs.select_related('customer')
        return ctx


class CampaignUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'management/crm/campaign_form.html'
    success_url = reverse_lazy('dashboard_campaign_list')


class CampaignDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Campaign
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_campaign_list')


# --- Kampaniya yuborish (TextUp SMS) ---
_CAMPAIGN_SEND_ROLES = (Role.OWNER, Role.MANAGER, Role.ADMIN)


@login_required(login_url='/login/')
@require_POST
def dashboard_campaign_test_send(request, pk):
    """Kampaniyani bitta mijozga test sifatida yuboradi."""
    from crm.services import CampaignSendService

    if request.user.role not in _CAMPAIGN_SEND_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")

    result = CampaignSendService.test_send(pk)
    if result.get('success'):
        messages.success(request, f"Test yuborildi: {result.get('customer', '')} — «{result.get('message', '')[:60]}»")
    else:
        messages.error(request, f"Test yuborilmadi: {result.get('error') or result.get('message', 'Nomaʼlum xato')}")
    return redirect('dashboard_campaign_detail', pk=pk)


@login_required(login_url='/login/')
@require_POST
def dashboard_campaign_send(request, pk):
    """Kampaniyani barcha target mijozlarga yuboradi."""
    from crm.services import CampaignSendService

    if request.user.role not in _CAMPAIGN_SEND_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")

    result = CampaignSendService.send_campaign(pk)
    sent, failed = result.get('sent', 0), result.get('failed', 0)
    if sent:
        messages.success(request, f"Yuborildi: {sent} ta. Xato: {failed} ta.")
    if not sent and result.get('errors'):
        messages.error(request, "; ".join(result['errors'][:3]))
    return redirect('dashboard_campaign_detail', pk=pk)


@login_required(login_url='/login/')
@require_POST
def dashboard_birthday_congratulate(request):
    """Bugun tug'ilgan kuni bo'lgan mijozlarga SMS tabrik yuboradi (AJAX, JSON)."""
    from crm.services import BirthdayService

    result = BirthdayService.congratulate()
    sent, failed = result.get('sent', 0), result.get('failed', 0)
    if sent and not failed:
        msg = f"{sent} ta mijoz SMS bilan tabriklandi 🎉"
    elif sent and failed:
        msg = f"{sent} ta yuborildi, {failed} ta xato."
    elif failed:
        msg = "Tabrik yuborilmadi: " + "; ".join(result.get('errors', [])[:2])
    else:
        msg = "Bugun tabriklanadigan mijoz qolmadi."
    return JsonResponse({
        'success': bool(sent) or (sent == 0 and failed == 0),
        'sent': sent,
        'failed': failed,
        'message': msg,
    })


# --- Buyurtmalar (Orders) ---
_ORDER_ROLES = (Role.OWNER, Role.MANAGER, Role.ADMIN)


class OrderListView(CMSBaseMixin, ListView):
    model = Order
    template_name = 'management/orders/order_list.html'
    context_object_name = 'order_list'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('items')
        status = self.request.GET.get('status', '')
        if status in OrderStatus.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = OrderStatus.choices
        ctx['active_status'] = self.request.GET.get('status', '')
        ctx['new_count'] = Order.objects.filter(status=OrderStatus.NEW).count()
        return ctx


class OrderDetailView(CMSBaseMixin, DetailView):
    model = Order
    template_name = 'management/orders/order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = self.object.items.all()
        ctx['STATUS'] = OrderStatus
        return ctx


class OrderDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_order_list')


@login_required(login_url='/login/')
@require_POST
def dashboard_order_status(request, pk):
    """Manager buyurtmani qabul qiladi yoki rad etadi (sabab bilan)."""
    if request.user.role not in _ORDER_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")
    order = get_object_or_404(Order, pk=pk)
    action = request.POST.get('action', '')

    if action == 'accept':
        order.status = OrderStatus.ACCEPTED
        order.reject_reason = ''
        order.accepted_at = timezone.now()
        order.handled_by = request.user
        order.save(update_fields=['status', 'reject_reason', 'accepted_at', 'handled_by', 'updated_at'])
        messages.success(request, f"Buyurtma #{order.pk} qabul qilindi.")
    elif action == 'reject':
        reason = (request.POST.get('reject_reason') or '').strip()[:1000]
        if not reason:
            messages.error(request, "Rad etish sababini kiriting.")
            return redirect('dashboard_order_detail', pk=pk)
        order.status = OrderStatus.REJECTED
        order.reject_reason = reason
        order.rejected_at = timezone.now()
        order.handled_by = request.user
        order.save(update_fields=['status', 'reject_reason', 'rejected_at', 'handled_by', 'updated_at'])
        messages.success(request, f"Buyurtma #{order.pk} bekor qilindi.")
    elif action == 'complete':
        order.status = OrderStatus.COMPLETED
        order.handled_by = request.user
        order.save(update_fields=['status', 'handled_by', 'updated_at'])
        messages.success(request, f"Buyurtma #{order.pk} yetkazildi deb belgilandi.")
        # Sodiqlik: yetkazilgan buyurtma uchun ball (idempotent)
        from crm.services import LoyaltyService
        txn = LoyaltyService.award_for_order(order)
        if txn:
            messages.info(request, f"Mijozga {txn.points} sodiqlik balli berildi.")
    return redirect('dashboard_order_detail', pk=pk)


class OrderSettingsView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    """Buyurtma sozlamalari (singleton): qabul toggle + minimum summa."""
    model = OrderSettings
    form_class = OrderSettingsForm
    template_name = 'management/orders/order_settings.html'
    success_url = reverse_lazy('dashboard_order_settings')
    success_message_update = "Buyurtma sozlamalari saqlandi."

    def get_object(self, queryset=None):
        return OrderSettings.get()

    def get_success_message(self, cleaned_data=None):
        return self.success_message_update


# --- Sodiqlik dasturi (loyalty) ---
class LoyaltySettingsView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    """Sodiqlik dasturi sozlamalari (singleton)."""
    model = LoyaltySettings
    form_class = LoyaltySettingsForm
    template_name = 'management/crm/loyalty_settings.html'
    success_url = reverse_lazy('dashboard_loyalty_settings')
    success_message_update = "Sodiqlik sozlamalari saqlandi."

    def get_object(self, queryset=None):
        return LoyaltySettings.get()

    def get_success_message(self, cleaned_data=None):
        return self.success_message_update


@login_required(login_url='/login/')
@require_POST
def dashboard_customer_loyalty_adjust(request, pk):
    """Mijoz balliga qo'lda +/- tuzatish (faqat OWNER/MANAGER/ADMIN)."""
    from crm.services import LoyaltyService
    if request.user.role not in (Role.OWNER, Role.MANAGER, Role.ADMIN):
        raise PermissionDenied("Ruxsat yo'q!")
    customer = get_object_or_404(Customer, pk=pk)
    try:
        points = int(request.POST.get('points', '0'))
    except (TypeError, ValueError):
        points = 0
    note = (request.POST.get('note') or '').strip()
    result = LoyaltyService.adjust(customer.pk, points, note=note, user=request.user)
    if result.get('success'):
        messages.success(request, f"Ball yangilandi. Yangi balans: {result['balance']}.")
    else:
        messages.error(request, result.get('error', "Ballni o'zgartirib bo'lmadi."))
    return redirect('dashboard_customer_detail', pk=pk)


# --- Topbar bildirishnomalari (AJAX) ---
@login_required(login_url='/login/')
def dashboard_notifications_count(request):
    """Joriy bildirishnoma sonini qaytaradi (orqaga qaytishda badge'ni yangilash uchun)."""
    from .context_processors import build_notifications
    data = build_notifications(request.user)
    return JsonResponse({'count': data['topbar_notifications_count']})


@login_required(login_url='/login/')
@require_POST
def dashboard_notifications_mark_all_read(request):
    """Barcha o'qilmagan murojaat va yangi buyurtmalarni o'qilgan deb belgilaydi."""
    from website.models import ContactMessage
    from .context_processors import build_notifications
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    Order.objects.filter(status=OrderStatus.NEW, is_read=False).update(is_read=True)
    data = build_notifications(request.user)
    return JsonResponse({'success': True, 'count': data['topbar_notifications_count']})


# --- Lock Screen ---
@login_required(login_url='/login/')
def lock_screen(request):
    request.session['screen_locked'] = True
    return render(request, 'management/lock_screen.html', {'profile': request.user})


@login_required(login_url='/login/')
def unlock_screen(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if request.user.check_password(password):
            request.session['screen_locked'] = False
            messages.success(request, "Ekran qulfi ochildi.")
            return redirect('dashboard_home')
        else:
            messages.error(request, "Noto'g'ri parol.")
    return redirect('dashboard_lock_screen')


# ── Statistika — StatItem CRUD ──────────────────────────────────────────────

class StatItemListView(CMSBaseMixin, ListView):
    model = StatItem
    template_name = 'management/website/statitem_list.html'
    context_object_name = 'statitem_list'
    queryset = StatItem.objects.order_by('order', 'pk')


class StatItemCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = StatItem
    form_class = StatItemForm
    template_name = 'management/website/statitem_form.html'
    success_url = reverse_lazy('dashboard_statitem_list')
    success_message_create = "Statistika muvaffaqiyatli qo'shildi."

    def form_valid(self, form):
        messages.success(self.request, self.success_message_create)
        return super().form_valid(form)


class StatItemUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = StatItem
    form_class = StatItemForm
    template_name = 'management/website/statitem_form.html'
    success_url = reverse_lazy('dashboard_statitem_list')
    success_message_update = "Statistika muvaffaqiyatli yangilandi."

    def form_valid(self, form):
        messages.success(self.request, self.success_message_update)
        return super().form_valid(form)


class StatItemDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = StatItem
    success_url = reverse_lazy('dashboard_statitem_list')
    success_message_delete = "Statistika muvaffaqiyatli o'chirildi."

    def post(self, request, *args, **kwargs):
        messages.success(request, self.success_message_delete)
        return super().post(request, *args, **kwargs)


# ── "Nega biz?" — Feature CRUD ──────────────────────────────────────────────

class FeatureListView(CMSBaseMixin, ListView):
    model = Feature
    template_name = 'management/website/feature_list.html'
    context_object_name = 'feature_list'
    queryset = Feature.objects.order_by('order', 'pk')


class FeatureCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Feature
    form_class = FeatureForm
    template_name = 'management/website/feature_form.html'
    success_url = reverse_lazy('dashboard_feature_list')
    success_message_create = "Xususiyat muvaffaqiyatli qo'shildi."

    def form_valid(self, form):
        messages.success(self.request, self.success_message_create)
        return super().form_valid(form)


class FeatureUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Feature
    form_class = FeatureForm
    template_name = 'management/website/feature_form.html'
    success_url = reverse_lazy('dashboard_feature_list')
    success_message_update = "Xususiyat muvaffaqiyatli yangilandi."

    def form_valid(self, form):
        messages.success(self.request, self.success_message_update)
        return super().form_valid(form)


class FeatureDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Feature
    success_url = reverse_lazy('dashboard_feature_list')
    success_message_delete = "Xususiyat muvaffaqiyatli o'chirildi."

    def post(self, request, *args, **kwargs):
        messages.success(request, self.success_message_delete)
        return super().post(request, *args, **kwargs)


# ── Sayt chat — dashboarddan javob berish ───────────────────────────────────
# Mijoz sayt chatida yozadi → ChatMessage(IN). Bu yerda admin javob yozadi →
# ChatMessage(OUT). Mijozning sahifasi mavjud /chat/poll/ orqali javobni oladi.
# (Telegram Reply yo'li ham ishlayveradi — bu unga MUQOBIL, qo'shimcha infra yo'q.)
_CHAT_ROLES = (Role.OWNER, Role.MANAGER, Role.ADMIN)


class ChatSessionListView(CMSBaseMixin, ListView):
    model = ChatSession
    template_name = 'management/chat/chat_list.html'
    context_object_name = 'sessions'
    paginate_by = 30

    def get_queryset(self):
        return (ChatSession.objects
                .annotate(msg_count=Count('messages'))
                .filter(msg_count__gt=0)
                .order_by('-updated_at'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for s in ctx['sessions']:
            last = s.messages.order_by('-id').first()
            s.last_msg = last
            # Oxirgi xabar mehmondan bo'lsa — javob kutilmoqda.
            s.awaiting = bool(last and last.direction == ChatMessage.IN)
        return ctx


class ChatSessionDetailView(CMSBaseMixin, DetailView):
    model = ChatSession
    template_name = 'management/chat/chat_detail.html'
    context_object_name = 'session'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['chat_messages'] = self.object.messages.order_by('id')
        return ctx


@login_required(login_url='/login/')
@require_POST
def dashboard_chat_reply(request, pk):
    """Admin javobi — ChatMessage(OUT). Mijoz /chat/poll/ orqali oladi."""
    if request.user.role not in _CHAT_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")
    session = get_object_or_404(ChatSession, pk=pk)
    text = (request.POST.get('text') or '').strip()[:2000]
    if text:
        ChatMessage.objects.create(
            session=session, direction=ChatMessage.OUT, text=text,
        )
        # Sessiya updated_at yangilanishi uchun (ro'yxat tartibi to'g'ri bo'lsin).
        session.save(update_fields=['updated_at'])
    return redirect('dashboard_chat_detail', pk=pk)


@login_required(login_url='/login/')
def dashboard_chat_messages(request, pk):
    """Dashboard chat oynasi uchun jonli yangilanish (oddiy JS poll)."""
    if request.user.role not in _CHAT_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")
    session = get_object_or_404(ChatSession, pk=pk)
    try:
        after = int(request.GET.get('after', '0'))
    except (TypeError, ValueError):
        after = 0
    qs = session.messages.filter(id__gt=after).order_by('id')
    data = [{
        'id': m.id,
        'direction': m.direction,
        'text': m.text,
        'time': timezone.localtime(m.created_at).strftime('%H:%M'),
        'is_auto': m.is_auto,
    } for m in qs]
    return JsonResponse({'messages': data})


# ── Global topbar qidiruv (AJAX) ────────────────────────────────────────────
@login_required(login_url='/login/')
@require_GET
def dashboard_search(request):
    """Topbar global qidiruvi — rolga mos guruhlangan natija (JSON).

    Natija faqat foydalanuvchi roli ko'ra oladigan modellardan keladi
    (ruxsat filtri `dashboard/search.py` ichida). Qarang: SEARCH_REGISTRY.
    """
    if request.user.role not in CMS_ROLES:
        raise PermissionDenied("Ruxsat yo'q!")
    results = global_search(request.user, request.GET.get('q', ''))
    return JsonResponse({'results': results})
