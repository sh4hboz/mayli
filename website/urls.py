from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('menu/items/', views.menu_items, name='menu_items'),
    path('menu/<int:pk>/', views.dish_detail, name='dish_detail'),
    path('cart/', views.cart, name='cart'),
    path('orders/', views.my_orders, name='my_orders'),
    path('chat/send/', views.chat_send, name='chat_send'),
    path('chat/poll/', views.chat_poll, name='chat_poll'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news_list'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
]
