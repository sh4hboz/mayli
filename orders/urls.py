from django.urls import path

from . import views

# Sayt buyurtma API — tilsiz (i18n_patterns'dan tashqari, config.urls da ulanadi).
urlpatterns = [
    path('order/otp/request/', views.otp_request, name='order_otp_request'),
    path('order/otp/verify/', views.otp_verify, name='order_otp_verify'),
    path('order/create/', views.order_create, name='order_create'),
    path('order/my/', views.my_orders, name='order_my'),
]
