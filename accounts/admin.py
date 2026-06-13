from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import StaffProfile, Role

User = get_user_model()


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name = 'Xodim profili'
    fields = ('role', 'position', 'hired_at')
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (StaffProfileInline,)
    list_display = ('phone', 'full_name', 'role', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('phone', 'full_name')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Shaxsiy ma\'lumotlar', {'fields': ('full_name', 'email')}),
        ('Rollar va Ruxsatlar', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'role', 'password'),
        }),
    )


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'position', 'hired_at', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__phone', 'position')
    readonly_fields = ('created_at', 'updated_at', 'pin_hash')
    fieldsets = (
        ('Asosiy', {'fields': ('user', 'role', 'position', 'hired_at')}),
        ('PIN (o\'zgartirish uchun admin paneli emas, dashboard ishlatilsin)', {
            'fields': ('pin_hash',),
            'classes': ('collapse',),
        }),
        ('Vaqt', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
