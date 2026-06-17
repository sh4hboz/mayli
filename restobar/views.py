import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission
from accounts.models import Role, StaffProfile

User = get_user_model()


def clean_uz_phone(phone_str):
    """
    Telefon raqamini formatlash va to'g'riligini tekshirish.
    Faqat raqamlar va '+' belgisini qoldiradi.
    O'zbekiston raqami ekanligini (+998XXXXXXXXX) tekshiradi.
    """
    cleaned = re.sub(r'[^\d+]', '', phone_str)
    if cleaned.startswith('998') and len(cleaned) == 12:
        cleaned = '+' + cleaned
    elif len(cleaned) == 9 and cleaned.isdigit():
        cleaned = '+998' + cleaned
    if re.match(r'^\+998\d{9}$', cleaned):
        return cleaned
    return None


# --- XODIMLAR AUTENTIFIKATSIYASI (boshqaruv paneli uchun) ---

def login_view(request):
    """
    Xodimlar uchun tizimga kirish portali.
    Oddiy login (username) + parol orqali kiradi va boshqaruv paneliga o'tadi.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '').strip()

        if not username_input or not password_input:
            return render(request, 'registration/login.html', {
                'error': "Iltimos, login va parolni kiriting!",
                'username': username_input,
            })

        authenticated_user = authenticate(request, username=username_input, password=password_input)
        if authenticated_user is not None:
            login(request, authenticated_user)
            remember = request.POST.get('remember') == 'on'
            if remember:
                request.session.set_expiry(30 * 24 * 60 * 60)
            return redirect('dashboard_home')

        return render(request, 'registration/login.html', {
            'error': "Login yoki parol noto'g'ri!",
            'username': username_input,
        })

    return render(request, 'registration/login.html')


def logout_view(request):
    """Tizimdan chiqish — kirish sahifasiga qaytaradi."""
    logout(request)
    return redirect('login')


# --- XODIMLARNI BOSHQARISH (boshqaruv paneli) ---

@login_required(login_url='login')
def staff_management_view(request):
    """
    Dashboarddagi Xodimlarni Boshqarish Sahifasi.
    Faqat manager, admin va owner kirishi mumkin.
    Barcha xodimlarni qo'shish, ro'yxatini ko'rish va o'chirish.
    """
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard_home')

    error_msg = None
    success_msg = None

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        role_input = request.POST.get('role', '').strip()
        password_input = request.POST.get('password', '').strip()

        if not username_input or not role_input or not password_input:
            error_msg = "Iltimos, barcha maydonlarni to'ldiring!"
        elif role_input not in [Role.WAITER, Role.BARMAN, Role.ACCOUNTANT, Role.MANAGER, Role.ADMIN]:
            error_msg = "Roli noto'g'ri tanlandi!"
        elif len(password_input) < 6:
            error_msg = "Parol kamida 6 belgidan iborat bo'lishi shart!"
        elif User.objects.filter(username=username_input).exists():
            error_msg = f"Ushbu '{username_input}' logini tizimda allaqachon mavjud!"
        else:
            try:
                new_user = User.objects.create_user(
                    username=username_input,
                    password=password_input,
                    role=role_input,
                    full_name=username_input,
                )
                StaffProfile.objects.create(user=new_user, role=role_input)
                success_msg = f"Yangi xodim '{username_input}' ({role_input}) muvaffaqiyatli qo'shildi!"
            except Exception as e:
                error_msg = f"Xodimni saqlashda xatolik yuz berdi: {str(e)}"

    # Barcha xodimlar ro'yxati
    staff_list = User.objects.all().order_by('role', 'username')

    # Qo'shish formasi uchun tanlanadigan rollar (Egadan tashqari)
    assignable_roles = [
        (Role.WAITER, Role.WAITER.label),
        (Role.BARMAN, Role.BARMAN.label),
        (Role.ACCOUNTANT, Role.ACCOUNTANT.label),
        (Role.MANAGER, Role.MANAGER.label),
        (Role.ADMIN, Role.ADMIN.label),
    ]

    return render(request, 'management/staff_list.html', {
        'staff_list': staff_list,
        'profile': user,
        'assignable_roles': assignable_roles,
        'error': error_msg,
        'success': success_msg
    })


@login_required(login_url='login')
def delete_staff_view(request, user_id):
    """Xodimni o'chirib tashlash"""
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard_home')

    try:
        user_to_delete = User.objects.get(id=user_id)
        # Foydalanuvchi o'zini o'chira olmaydi
        if user_to_delete != user:
            user_to_delete.delete()
    except User.DoesNotExist:
        pass

    return redirect('staff_management')


@login_required(login_url='login')
def staff_permissions_view(request, user_id):
    """
    Xodimlarning individual Django permission'larini (ruxsatnomalarini)
    tahrirlash sahifasi (chap-o'ng split select widget interfeysi).
    Faqat manager, admin va owner kirishi mumkin.
    """
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard_home')

    staff_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        assigned_perms = request.POST.getlist('permissions')
        staff_user.user_permissions.set(assigned_perms)
        staff_user.save()
        return redirect('staff_management')

    # Asosan website, menu, accounts ilovalari ruxsatlari muhim
    all_permissions = Permission.objects.select_related('content_type').filter(
        content_type__app_label__in=['website', 'menu', 'accounts', 'crm']
    ).order_by('content_type__app_label', 'codename')

    assigned_permissions = staff_user.user_permissions.all()
    assigned_ids = set(assigned_permissions.values_list('id', flat=True))

    available_permissions = [p for p in all_permissions if p.id not in assigned_ids]

    return render(request, 'management/staff_permissions.html', {
        'staff_user': staff_user,
        'profile': user,
        'assigned_permissions': assigned_permissions,
        'available_permissions': available_permissions,
    })
