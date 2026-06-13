from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_view, name='dashboard_chat'),

    # Sayt sozlamalari
    path('settings/website/', views.SiteSettingsUpdateView.as_view(), name='dashboard_settings_website'),

    # Yangiliklar
    path('website/news/', views.NewsListView.as_view(), name='dashboard_news_list'),
    path('website/news/add/', views.NewsCreateView.as_view(), name='dashboard_news_create'),
    path('website/news/<int:pk>/edit/', views.NewsUpdateView.as_view(), name='dashboard_news_edit'),
    path('website/news/<int:pk>/delete/', views.NewsDeleteView.as_view(), name='dashboard_news_delete'),

    # Aksiyalar
    path('website/promotions/', views.PromotionListView.as_view(), name='dashboard_promotion_list'),
    path('website/promotions/add/', views.PromotionCreateView.as_view(), name='dashboard_promotion_create'),
    path('website/promotions/<int:pk>/edit/', views.PromotionUpdateView.as_view(), name='dashboard_promotion_edit'),
    path('website/promotions/<int:pk>/delete/', views.PromotionDeleteView.as_view(), name='dashboard_promotion_delete'),

    # Galereya
    path('website/gallery/', views.GalleryItemListView.as_view(), name='dashboard_gallery_list'),
    path('website/gallery/add/', views.GalleryItemCreateView.as_view(), name='dashboard_gallery_create'),
    path('website/gallery/<int:pk>/delete/', views.GalleryItemDeleteView.as_view(), name='dashboard_gallery_delete'),

    # Vakansiyalar
    path('website/vacancies/', views.VacancyListView.as_view(), name='dashboard_vacancy_list'),
    path('website/vacancies/add/', views.VacancyCreateView.as_view(), name='dashboard_vacancy_create'),
    path('website/vacancies/<int:pk>/edit/', views.VacancyUpdateView.as_view(), name='dashboard_vacancy_edit'),
    path('website/vacancies/<int:pk>/delete/', views.VacancyDeleteView.as_view(), name='dashboard_vacancy_delete'),

    # Ishga topshirilgan arizalar
    path('website/applications/', views.JobApplicationListView.as_view(), name='dashboard_application_list'),
    path('website/applications/<int:pk>/', views.JobApplicationDetailView.as_view(), name='dashboard_application_detail'),
    path('website/applications/<int:pk>/delete/', views.JobApplicationDeleteView.as_view(), name='dashboard_application_delete'),

    # Murojaatlar
    path('website/contacts/', views.ContactMessageListView.as_view(), name='dashboard_contact_list'),
    path('website/contacts/<int:pk>/', views.ContactMessageDetailView.as_view(), name='dashboard_contact_detail'),
    path('website/contacts/<int:pk>/toggle-read/', views.ContactMessageToggleReadView.as_view(), name='dashboard_contact_toggle_read'),
    path('website/contacts/<int:pk>/delete/', views.ContactMessageDeleteView.as_view(), name='dashboard_contact_delete'),
    
    # Kategoriyalar boshqaruvi
    path('menu/categories/', views.CategoryListView.as_view(), name='dashboard_category_list'),
    path('menu/categories/add/', views.CategoryCreateView.as_view(), name='dashboard_category_create'),
    path('menu/categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='dashboard_category_edit'),
    path('menu/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='dashboard_category_delete'),

    # Taomlar boshqaruvi
    path('menu/dishes/', views.DishListView.as_view(), name='dashboard_dish_list'),
    path('menu/dishes/add/', views.DishCreateView.as_view(), name='dashboard_dish_create'),
    path('menu/dishes/<int:pk>/edit/', views.DishUpdateView.as_view(), name='dashboard_dish_edit'),
    path('menu/dishes/<int:pk>/delete/', views.DishDeleteView.as_view(), name='dashboard_dish_delete'),

    # Buyurtmalar boshqaruvi
    path('orders/', views.OrderListView.as_view(), name='dashboard_order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='dashboard_order_detail'),
    path('orders/<int:pk>/status-change/', views.OrderStatusChangeView.as_view(), name='dashboard_order_status_change'),
    path('orders/<int:pk>/delete/', views.OrderDeleteView.as_view(), name='dashboard_order_delete'),

    # Mijozlar boshqaruvi
    path('customers/', views.CustomerListView.as_view(), name='dashboard_customer_list'),

    # Universal AJAX toggle active
    path('toggle-active/<str:app_label>/<str:model_name>/<int:pk>/', views.toggle_active_ajax, name='dashboard_toggle_active'),
]
