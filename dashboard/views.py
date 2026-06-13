from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views import View

from accounts.models import Role
from website.models import SiteSettings, News, Promotion, GalleryItem, Vacancy, JobApplication, ContactMessage
from menu.models import Category, Dish
from orders.models import Order
from .forms import SiteSettingsForm, NewsForm, PromotionForm, GalleryItemForm, VacancyForm, CategoryForm, DishForm


@login_required(login_url='/login/')
def chat_view(request):
    if request.user.role == Role.CUSTOMER:
        return redirect('/dashboard/')
    return render(request, 'management/chat.html', {'profile': request.user})


# --- CMS views-lar uchun Mixin base ---
class CMSBaseMixin(PermissionRequiredMixin):
    """
    Barcha CMS view'lari uchun tayanch sinf.
    - Avtorizatsiya va ruxsatlarni tekshiradi.
    - Ruxsat bo'lmasa, login sahifasiga redirect qilish o'rniga 403 PermissionDenied beradi.
    - Context-ga profile (request.user) ni qo'shadi.
    - Bugalter (Accountant) uchun faqat Read-only (GET, HEAD, OPTIONS) ruxsat beradi.
    """
    raise_exception = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = self.request.user
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == Role.ACCOUNTANT:
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Bugalter faqat ma'lumotlarni ko'ra oladi (Read-only)!")
        return super().dispatch(request, *args, **kwargs)


# --- Sayt sozlamalari (Site Settings) ---
class SiteSettingsUpdateView(CMSBaseMixin, UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'management/website/settings.html'
    permission_required = 'website.change_sitesettings'
    success_url = reverse_lazy('dashboard_settings_website')

    def get_object(self, queryset=None):
        return SiteSettings.get()


# --- Yangiliklar (News) ---
class NewsListView(CMSBaseMixin, ListView):
    model = News
    template_name = 'management/website/news_list.html'
    context_object_name = 'news_list'
    permission_required = 'website.view_news'


class NewsCreateView(CMSBaseMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'management/website/news_form.html'
    permission_required = 'website.add_news'
    success_url = reverse_lazy('dashboard_news_list')


class NewsUpdateView(CMSBaseMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'management/website/news_form.html'
    permission_required = 'website.change_news'
    success_url = reverse_lazy('dashboard_news_list')


class NewsDeleteView(CMSBaseMixin, DeleteView):
    model = News
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_news'
    success_url = reverse_lazy('dashboard_news_list')


# --- Aksiyalar (Promotions) ---
class PromotionListView(CMSBaseMixin, ListView):
    model = Promotion
    template_name = 'management/website/promotion_list.html'
    context_object_name = 'promotion_list'
    permission_required = 'website.view_promotion'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Bitta shablonda yangiliklar va aksiyalarni boshqarish qulay bo'lishi uchun
        return ctx


class PromotionCreateView(CMSBaseMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'management/website/promotion_form.html'
    permission_required = 'website.add_promotion'
    success_url = reverse_lazy('dashboard_promotion_list')


class PromotionUpdateView(CMSBaseMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'management/website/promotion_form.html'
    permission_required = 'website.change_promotion'
    success_url = reverse_lazy('dashboard_promotion_list')


class PromotionDeleteView(CMSBaseMixin, DeleteView):
    model = Promotion
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_promotion'
    success_url = reverse_lazy('dashboard_promotion_list')


# --- Galereya (Gallery) ---
class GalleryItemListView(CMSBaseMixin, ListView):
    model = GalleryItem
    template_name = 'management/website/gallery_list.html'
    context_object_name = 'gallery_list'
    permission_required = 'website.view_galleryitem'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = GalleryItemForm()
        return ctx


class GalleryItemCreateView(CMSBaseMixin, CreateView):
    model = GalleryItem
    form_class = GalleryItemForm
    template_name = 'management/website/gallery_list.html'
    permission_required = 'website.add_galleryitem'
    success_url = reverse_lazy('dashboard_gallery_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['gallery_list'] = GalleryItem.objects.all()
        return ctx


class GalleryItemDeleteView(CMSBaseMixin, DeleteView):
    model = GalleryItem
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_galleryitem'
    success_url = reverse_lazy('dashboard_gallery_list')


# --- Vakansiyalar (Vacancies) ---
class VacancyListView(CMSBaseMixin, ListView):
    model = Vacancy
    template_name = 'management/website/vacancy_list.html'
    context_object_name = 'vacancy_list'
    permission_required = 'website.view_vacancy'


class VacancyCreateView(CMSBaseMixin, CreateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/website/vacancy_form.html'
    permission_required = 'website.add_vacancy'
    success_url = reverse_lazy('dashboard_vacancy_list')


class VacancyUpdateView(CMSBaseMixin, UpdateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = 'management/website/vacancy_form.html'
    permission_required = 'website.change_vacancy'
    success_url = reverse_lazy('dashboard_vacancy_list')


class VacancyDeleteView(CMSBaseMixin, DeleteView):
    model = Vacancy
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_vacancy'
    success_url = reverse_lazy('dashboard_vacancy_list')


# --- Arizalar (Job Applications) ---
class JobApplicationListView(CMSBaseMixin, ListView):
    model = JobApplication
    template_name = 'management/website/applications_list.html'
    context_object_name = 'applications_list'
    permission_required = 'website.view_jobapplication'


class JobApplicationDetailView(CMSBaseMixin, DetailView):
    model = JobApplication
    template_name = 'management/website/application_detail.html'
    context_object_name = 'application'
    permission_required = 'website.view_jobapplication'


class JobApplicationDeleteView(CMSBaseMixin, DeleteView):
    model = JobApplication
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_jobapplication'
    success_url = reverse_lazy('dashboard_application_list')


# --- Murojaatlar (Contact Messages) ---
class ContactMessageListView(CMSBaseMixin, ListView):
    model = ContactMessage
    template_name = 'management/website/contacts_list.html'
    context_object_name = 'contacts_list'
    permission_required = 'website.view_contactmessage'


class ContactMessageDetailView(CMSBaseMixin, DetailView):
    model = ContactMessage
    template_name = 'management/website/contact_detail.html'
    context_object_name = 'message'
    permission_required = 'website.view_contactmessage'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return obj


class ContactMessageToggleReadView(CMSBaseMixin, UpdateView):
    model = ContactMessage
    permission_required = 'website.change_contactmessage'

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(ContactMessage, pk=kwargs.get('pk'))
        obj.is_read = not obj.is_read
        obj.save(update_fields=['is_read'])
        return JsonResponse({'success': True, 'is_read': obj.is_read})


class ContactMessageDeleteView(CMSBaseMixin, DeleteView):
    model = ContactMessage
    template_name = 'management/confirm_delete.html'
    permission_required = 'website.delete_contactmessage'
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
    permission_required = 'menu.view_category'


class CategoryCreateView(CMSBaseMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'management/menu/category_form.html'
    permission_required = 'menu.add_category'
    success_url = reverse_lazy('dashboard_category_list')


class CategoryUpdateView(CMSBaseMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'management/menu/category_form.html'
    permission_required = 'menu.change_category'
    success_url = reverse_lazy('dashboard_category_list')


class CategoryDeleteView(CMSBaseMixin, DeleteView):
    model = Category
    template_name = 'management/confirm_delete.html'
    permission_required = 'menu.delete_category'
    success_url = reverse_lazy('dashboard_category_list')


# --- Taomlar Boshqaruvi ---
class DishListView(CMSBaseMixin, ListView):
    model = Dish
    template_name = 'management/menu/dish_list.html'
    context_object_name = 'dish_list'
    permission_required = 'menu.view_dish'


class DishCreateView(CMSBaseMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    permission_required = 'menu.add_dish'
    success_url = reverse_lazy('dashboard_dish_list')


class DishUpdateView(CMSBaseMixin, UpdateView):
    model = Dish
    form_class = DishForm
    template_name = 'management/menu/dish_form.html'
    permission_required = 'menu.change_dish'
    success_url = reverse_lazy('dashboard_dish_list')


class DishDeleteView(CMSBaseMixin, DeleteView):
    model = Dish
    template_name = 'management/confirm_delete.html'
    permission_required = 'menu.delete_dish'
    success_url = reverse_lazy('dashboard_dish_list')


# --- Buyurtmalar Boshqaruvi ---
class OrderListView(CMSBaseMixin, ListView):
    model = Order
    template_name = 'management/orders/order_list.html'
    context_object_name = 'order_list'
    permission_required = 'orders.view_order'

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
    permission_required = 'orders.view_order'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.conf import settings
        ctx['YANDEX_MAPS_API_KEY'] = getattr(settings, 'YANDEX_MAPS_API_KEY', '')
        return ctx


class OrderStatusChangeView(CMSBaseMixin, View):
    permission_required = 'orders.change_order'

    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs.get('pk'))
        status = request.POST.get('status')
        if status in [choice[0] for choice in order._meta.get_field('status').choices]:
            order.status = status
            order.save(update_fields=['status'])
            messages.success(request, f"Buyurtma #{order.id} statusi muvaffaqiyatli yangilandi.")
        return redirect('dashboard_order_detail', pk=order.pk)


class OrderDeleteView(CMSBaseMixin, DeleteView):
    model = Order
    template_name = 'management/confirm_delete.html'
    permission_required = 'orders.delete_order'
    success_url = reverse_lazy('dashboard_order_list')


# --- Mijozlar Ro'yxati ---
from django.contrib.auth import get_user_model
User = get_user_model()

class CustomerListView(CMSBaseMixin, ListView):
    model = User
    template_name = 'management/customers/customer_list.html'
    context_object_name = 'customer_list'
    permission_required = 'accounts.view_user'

    def get_queryset(self):
        return super().get_queryset().filter(role=Role.CUSTOMER).order_by('-date_joined')

