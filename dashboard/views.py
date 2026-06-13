from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views import View
from django.core.exceptions import PermissionDenied

from accounts.models import Role
from website.models import SiteSettings, News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage
from menu.models import Category, Dish
from orders.models import Order
from .forms import SiteSettingsForm, NewsForm, PromotionForm, GalleryItemForm, VacancyForm, CategoryForm, DishForm


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
    }
    recent_contacts = ContactMessage.objects.order_by('-created_at')[:5]
    return render(request, 'management/dashboard.html', {
        'profile': request.user,
        'stats': stats,
        'recent_contacts': recent_contacts,
    })


@login_required(login_url='/login/')
def chat_view(request):
    if request.user.role == Role.CUSTOMER:
        return redirect('/dashboard/')
    return render(request, 'management/chat.html', {'profile': request.user})


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
            raise PermissionDenied(f"Ruxsat yo'q! Faqat {', '.join([r[1] for r in Role.choices if r[0] in allowed_roles])} dashboard'ga kira oladi.")

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


# --- Sayt sozlamalari (Site Settings) ---
class SiteSettingsUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'management/website/settings.html'
    success_url = reverse_lazy('dashboard_settings_website')

    def get_object(self, queryset=None):
        return SiteSettings.get()


# --- Yangiliklar (News) ---
class NewsListView(CMSBaseMixin, ListView):
    model = News
    template_name = 'management/website/news_list.html'
    context_object_name = 'news_list'


class NewsCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'management/website/news_form.html'
    success_url = reverse_lazy('dashboard_news_list')


class NewsUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
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


class PromotionCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'management/website/promotion_form.html'
    success_url = reverse_lazy('dashboard_promotion_list')


class PromotionUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
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


class GalleryItemCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
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
from django.views.decorators.http import require_POST

@login_required(login_url='/login/')
@require_POST
def toggle_active_ajax(request, app_label, model_name, pk):
    """
    Istalgan modeldagi is_active yoki boshqa boolean maydonini AJAX orqali o'zgartiruvchi universal view.
    """
    if request.user.role == Role.CUSTOMER:
        return JsonResponse({'success': False, 'error': "Ruxsat berilmagan!"}, status=403)
        
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


class CategoryDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Category
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_category_list')


# --- Taomlar Boshqaruvi ---
class DishListView(CMSBaseMixin, ListView):
    model = Dish
    template_name = 'management/menu/dish_list.html'
    context_object_name = 'dish_list'


class DishCreateView(CMSBaseMixin, SuccessMessageMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    success_url = reverse_lazy('dashboard_dish_list')


class DishUpdateView(CMSBaseMixin, SuccessMessageMixin, UpdateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    success_url = reverse_lazy('dashboard_dish_list')


class DishDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Dish
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_dish_list')


# --- Buyurtmalar Boshqaruvi ---
class OrderListView(CMSBaseMixin, ListView):
    model = Order
    template_name = 'management/orders/order_list.html'
    context_object_name = 'order_list'

    def get_queryset(self):
        qs = super().get_queryset()
        order_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        if order_type:
            qs = qs.filter(order_type=order_type)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_type'] = self.request.GET.get('type', '')
        ctx['active_status'] = self.request.GET.get('status', '')
        return ctx


class OrderDetailView(CMSBaseMixin, DetailView):
    model = Order
    template_name = 'management/orders/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.conf import settings
        ctx['YANDEX_MAPS_API_KEY'] = getattr(settings, 'YANDEX_MAPS_API_KEY', '')
        return ctx


class OrderStatusChangeView(CMSBaseMixin, View):

    def post(self, request, *args, **kwargs):
        from django.utils import timezone

        order = get_object_or_404(Order, pk=kwargs.get('pk'))
        status = request.POST.get('status')

        if status in [choice[0] for choice in order._meta.get_field('status').choices]:
            old_status = order.status
            order.status = status

            # Auto-set timestamps based on status
            if status == 'cooking' and not order.accepted_at:
                order.accepted_at = timezone.now()
            elif status == 'delivering' and not order.delivered_at:
                order.delivered_at = timezone.now()
            elif status == 'completed' and not order.completed_at:
                order.completed_at = timezone.now()

            order.save()
            messages.success(request, f"Buyurtma #{order.id} statusi '{status}' ga o'zgartirildi.")

        return redirect('dashboard_order_detail', pk=order.pk)


class OrderDeleteView(CMSBaseMixin, SuccessMessageMixin, DeleteView):
    model = Order
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('dashboard_order_list')


# --- Mijozlar Ro'yxati ---
from django.contrib.auth import get_user_model
User = get_user_model()

class CustomerListView(CMSBaseMixin, ListView):
    model = User
    template_name = 'management/customers/customer_list.html'
    context_object_name = 'customer_list'

    def get_queryset(self):
        return super().get_queryset().filter(role=Role.CUSTOMER).order_by('-date_joined')


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
    return redirect('lock_screen')
