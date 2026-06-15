from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('menu/', views.menu_view, name='menu'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Mijozlar uchun url manzillar
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    
    # Xodimlar uchun url manzillar
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/logout/', views.staff_logout_view, name='staff_logout'),
    
    # Dashboard Xodimlar boshqaruvi
    path('dashboard/staff/', views.staff_management_view, name='staff_management'),
    path('dashboard/staff/delete/<int:user_id>/', views.delete_staff_view, name='delete_staff'),
    path('dashboard/staff/<int:user_id>/permissions/', views.staff_permissions_view, name='staff_permissions'),
    
    # Mijoz shaxsiy kabineti
    path('profile/', views.profile_view, name='profile'),
]
