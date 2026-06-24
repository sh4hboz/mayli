from django.urls import path

from . import views

# Sayt bron API — tilsiz (i18n_patterns'dan tashqari, config.urls da ulanadi).
urlpatterns = [
    path('booking/availability/', views.availability, name='booking_availability'),
    path('booking/otp/request/', views.otp_request, name='booking_otp_request'),
    path('booking/otp/verify/', views.otp_verify, name='booking_otp_verify'),
    path('booking/create/', views.reservation_create, name='booking_create'),
]
