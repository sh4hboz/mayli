from django.urls import path
from . import views

urlpatterns = [
    # Xodimlar autentifikatsiyasi (boshqaruv paneli uchun)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Xodimlarni boshqarish (dashboard ichidagi sahifalar)
    path('staff/', views.staff_management_view, name='staff_management'),
    path('staff/delete/<int:user_id>/', views.delete_staff_view, name='delete_staff'),
    path('staff/<int:user_id>/permissions/', views.staff_permissions_view, name='staff_permissions'),
]
