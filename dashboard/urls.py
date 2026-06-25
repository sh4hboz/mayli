from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),

    # Sayt sozlamalari — 5 ta alohida bo'lim
    path('settings/website/', views.SiteSettingsGeneralView.as_view(), name='dashboard_settings_website'),
    path('settings/website/location/', views.SiteSettingsLocationView.as_view(), name='dashboard_settings_location'),
    path('settings/website/hero/', views.SiteSettingsHeroView.as_view(), name='dashboard_settings_hero'),
    path('settings/website/home/', views.SiteSettingsHomeContentView.as_view(), name='dashboard_settings_home'),
    path('settings/website/seo/', views.SiteSettingsSeoView.as_view(), name='dashboard_settings_seo'),
    path('settings/website/custom-css/', views.DashboardCustomCssView.as_view(), name='dashboard_custom_css'),

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
    path('website/partners/', views.PartnerListView.as_view(), name='dashboard_partner_list'),
    path('website/partners/add/', views.PartnerCreateView.as_view(), name='dashboard_partner_create'),
    path('website/partners/<int:pk>/delete/', views.PartnerDeleteView.as_view(), name='dashboard_partner_delete'),

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

    # Mijozlar (CRM)
    path('customers/', views.CustomerListView.as_view(), name='dashboard_customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='dashboard_customer_create'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='dashboard_customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='dashboard_customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='dashboard_customer_delete'),
    path('customers/<int:pk>/loyalty-adjust/', views.dashboard_customer_loyalty_adjust, name='dashboard_customer_loyalty_adjust'),

    # Sodiqlik dasturi sozlamalari
    path('loyalty/settings/', views.LoyaltySettingsView.as_view(), name='dashboard_loyalty_settings'),

    # Kampaniyalar (CRM Marketing)
    path('campaigns/', views.CampaignListView.as_view(), name='dashboard_campaign_list'),
    path('campaigns/add/', views.CampaignCreateView.as_view(), name='dashboard_campaign_create'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='dashboard_campaign_detail'),
    path('campaigns/<int:pk>/edit/', views.CampaignUpdateView.as_view(), name='dashboard_campaign_edit'),
    path('campaigns/<int:pk>/delete/', views.CampaignDeleteView.as_view(), name='dashboard_campaign_delete'),
    path('campaigns/<int:pk>/test-send/', views.dashboard_campaign_test_send, name='dashboard_campaign_test_send'),
    path('campaigns/<int:pk>/send/', views.dashboard_campaign_send, name='dashboard_campaign_send'),

    # Tug'ilgan kun SMS tabrigi (AJAX)
    path('customers/birthday-congratulate/', views.dashboard_birthday_congratulate, name='dashboard_birthday_congratulate'),

    # Topbar bildirishnomalari (AJAX)
    path('notifications/count/', views.dashboard_notifications_count, name='dashboard_notifications_count'),
    path('notifications/mark-all-read/', views.dashboard_notifications_mark_all_read, name='dashboard_notifications_mark_all_read'),

    # Topbar global qidiruv (AJAX)
    path('search/', views.dashboard_search, name='dashboard_search'),

    # Statistika
    path('website/stats/', views.StatItemListView.as_view(), name='dashboard_statitem_list'),
    path('website/stats/add/', views.StatItemCreateView.as_view(), name='dashboard_statitem_create'),
    path('website/stats/<int:pk>/edit/', views.StatItemUpdateView.as_view(), name='dashboard_statitem_edit'),
    path('website/stats/<int:pk>/delete/', views.StatItemDeleteView.as_view(), name='dashboard_statitem_delete'),

    # "Nega biz?" xususiyatlari
    path('website/features/', views.FeatureListView.as_view(), name='dashboard_feature_list'),
    path('website/features/add/', views.FeatureCreateView.as_view(), name='dashboard_feature_create'),
    path('website/features/<int:pk>/edit/', views.FeatureUpdateView.as_view(), name='dashboard_feature_edit'),
    path('website/features/<int:pk>/delete/', views.FeatureDeleteView.as_view(), name='dashboard_feature_delete'),

    # Buyurtmalar
    path('orders/', views.OrderListView.as_view(), name='dashboard_order_list'),
    path('orders/settings/', views.OrderSettingsView.as_view(), name='dashboard_order_settings'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='dashboard_order_detail'),
    path('orders/<int:pk>/status/', views.dashboard_order_status, name='dashboard_order_status'),
    path('orders/<int:pk>/delete/', views.OrderDeleteView.as_view(), name='dashboard_order_delete'),

    # Sayt chat — dashboarddan javob berish
    path('chat/', views.ChatSessionListView.as_view(), name='dashboard_chat_list'),
    path('chat/<int:pk>/', views.ChatSessionDetailView.as_view(), name='dashboard_chat_detail'),
    path('chat/<int:pk>/reply/', views.dashboard_chat_reply, name='dashboard_chat_reply'),
    path('chat/<int:pk>/messages/', views.dashboard_chat_messages, name='dashboard_chat_messages'),

    # Universal AJAX toggle active
    path('toggle-active/<str:app_label>/<str:model_name>/<int:pk>/', views.toggle_active_ajax, name='dashboard_toggle_active'),

    # Lock Screen
    path('lock/', views.lock_screen, name='dashboard_lock_screen'),
    path('unlock/', views.unlock_screen, name='dashboard_unlock_screen'),
]
