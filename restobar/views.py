import re
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
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

def home_view(request):
    """Bosh sahifa (Landing Page)"""
    return render(request, 'index.html')

def menu_view(request):
    """Menyu sahifasi"""
    return render(request, 'menu.html')

@login_required(login_url='login')
def dashboard_view(request):
    """
    Eski '/dashboard/' nomi uchun moslik.
    Asosiy boshqaruv paneli endi `dashboard` app'da (dashboard_home).
    """
    if request.user.role == Role.CUSTOMER:
        return redirect('menu')
    return redirect('dashboard_home')

def login_view(request):
    """
    Yagona Tizimga Kirish Portali (Mijozlar va Xodimlar uchun yagona kirish nuqtasi)
    Mijozlar: telefon + parol orqali.
    Xodimlar: login + PIN/parol orqali.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true'

    if request.user.is_authenticated:
        if request.user.role != Role.CUSTOMER:
            if is_ajax:
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
            return redirect('dashboard')

        if is_ajax:
            return JsonResponse({'success': True, 'redirect': '/menu/'})
        return redirect('menu')

    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'customer')

        if user_type == 'customer':
            phone_input = request.POST.get('phone', '').strip()
            password_input = request.POST.get('password', '').strip()

            if not phone_input or not password_input:
                error_msg = "Iltimos, barcha maydonlarni to'ldiring!"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                return render(request, 'registration/login.html', {
                    'error': error_msg,
                    'active_tab': 'customer'
                })

            cleaned_phone = clean_uz_phone(phone_input)
            if not cleaned_phone:
                error_msg = "Faqat O'zbekiston telefon raqami qabul qilinadi (+998 XX XXX-XX-XX)!"
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                return render(request, 'registration/login.html', {
                    'error': error_msg,
                    'phone': phone_input,
                    'active_tab': 'customer'
                })

            user_exists = User.objects.filter(phone=cleaned_phone).exists()

            if user_exists:
                user = User.objects.get(phone=cleaned_phone)
                if user.role != Role.CUSTOMER:
                    error_msg = "Ushbu foydalanuvchi nomi xodimga tegishli! Iltimos, xodimlar tabidan kiring."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg})
                    return render(request, 'registration/login.html', {
                        'error': error_msg,
                        'phone': phone_input,
                        'active_tab': 'customer'
                    })

                authenticated_user = authenticate(request, username=cleaned_phone, password=password_input)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    remember = request.POST.get('remember') == 'on'
                    if remember:
                        request.session.set_expiry(30 * 24 * 60 * 60)
                    if is_ajax:
                        next_url = request.POST.get('next')
                        if not next_url or next_url == '/' or '/login/' in next_url or '/staff/' in next_url:
                            next_url = '/menu/'
                        return JsonResponse({'success': True, 'redirect': next_url})
                    return redirect('menu')
                else:
                    error_msg = "Ushbu telefon raqami ro'yxatdan o'tgan, lekin parol noto'g'ri!"
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg})
                    return render(request, 'registration/login.html', {
                        'error': error_msg,
                        'phone': phone_input,
                        'active_tab': 'customer'
                    })
            else:
                try:
                    user = User.objects.create_user(
                        phone=cleaned_phone,
                        password=password_input,
                        role=Role.CUSTOMER,
                        full_name=cleaned_phone
                    )
                    login(request, user)
                    if is_ajax:
                        return JsonResponse({'success': True, 'redirect': '/menu/'})
                    return redirect('menu')
                except Exception as e:
                    error_msg = f"Ro'yxatdan o'tishda xatolik yuz berdi: {str(e)}"
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg})
                    return render(request, 'registration/login.html', {
                        'error': error_msg,
                        'phone': phone_input,
                        'active_tab': 'customer'
                    })

        elif user_type == 'staff':
            username_input = request.POST.get('username', '').strip()
            password_input = request.POST.get('password', '').strip()

            if not username_input or not password_input:
                error_msg = "Iltimos, login va parolni/PINni kiriting!"
                return render(request, 'registration/login.html', {
                    'error': error_msg,
                    'active_tab': 'staff'
                })

            user_exists = User.objects.filter(phone=username_input).exists()

            if user_exists:
                user = User.objects.get(phone=username_input)
                if user.role == Role.CUSTOMER:
                    return render(request, 'registration/login.html', {
                        'error': "Mijozlar faqat telefon raqami orqali mijozlar bo'limidan kira oladilar!",
                        'username': username_input,
                        'active_tab': 'staff'
                    })

                role = user.role
                if role in [Role.WAITER, Role.BARMAN]:
                    if len(password_input) != 4 or not password_input.isdigit():
                        return render(request, 'registration/login.html', {
                            'error': "Ofitsiant va Barmanlar faqat 4 xonali PIN kod kiritishlari shart!",
                            'username': username_input,
                            'active_tab': 'staff'
                        })

                authenticated_user = authenticate(request, username=username_input, password=password_input)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    remember = request.POST.get('remember') == 'on'
                    if remember:
                        request.session.set_expiry(30 * 24 * 60 * 60)
                    return redirect('dashboard')
                else:
                    return render(request, 'registration/login.html', {
                        'error': "Foydalanuvchi nomi yoki parol/PIN noto'g'ri!",
                        'username': username_input,
                        'active_tab': 'staff'
                    })
            else:
                # Yangi xodim
                if not username_input.startswith('+') or not username_input[1:].isdigit():
                    return render(request, 'registration/login.html', {
                        'error': "Tizimda mavjud bo'lmagan xodim! Login telefon raqami formatida bo'lishi kerak.",
                        'username': username_input,
                        'active_tab': 'staff'
                    })

                staff_role = Role.WAITER
                if 'barman' in username_input:
                    staff_role = Role.BARMAN
                elif 'manager' in username_input:
                    staff_role = Role.MANAGER
                elif 'admin' in username_input or 'super' in username_input:
                    staff_role = Role.ADMIN

                if staff_role in [Role.WAITER, Role.BARMAN]:
                    if len(password_input) != 4 or not password_input.isdigit():
                        return render(request, 'registration/login.html', {
                            'error': "Ofitsiant va Barmanlar faqat 4 xonali PIN kod kiritishlari shart!",
                            'username': username_input,
                            'active_tab': 'staff'
                        })

                try:
                    new_user = User.objects.create_user(
                        phone=username_input,
                        password=password_input,
                        role=staff_role,
                        full_name=username_input
                    )

                    staff_prof = StaffProfile.objects.create(
                        user=new_user,
                        role=staff_role
                    )
                    if staff_role in [Role.WAITER, Role.BARMAN]:
                        staff_prof.set_pin(password_input)
                        staff_prof.save()

                    login(request, new_user)
                    return redirect('dashboard')
                except Exception as e:
                    return render(request, 'registration/login.html', {
                        'error': f"Xodimni yaratishda xatolik: {str(e)}",
                        'username': username_input,
                        'active_tab': 'staff'
                    })

    active_tab = request.GET.get('tab', 'customer')
    return render(request, 'registration/login.html', {'active_tab': active_tab})

def register_view(request):
    """Mijozlar ro'yxatdan o'tish oynasi ham yagona mijoz portaliga yo'naltiriladi"""
    return redirect('login')

def reset_password_view(request):
    """
    Mijozlar Parolini Tiklash (Qayta belgilash)
    Telefon raqamini kiritib, to'g'ridan-to'g'ri yangi parol belgilaydi (Ishlab chiqish rejimi).
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true'

    if request.method == 'POST':
         phone_input = request.POST.get('phone', '').strip()
         new_password = request.POST.get('new_password', '').strip()
         confirm_password = request.POST.get('confirm_password', '').strip()

         if not phone_input or not new_password or not confirm_password:
             error_msg = "Iltimos, barcha maydonlarni to'ldiring!"
             if is_ajax:
                 return JsonResponse({'success': False, 'error': error_msg})
             return render(request, 'registration/reset_password.html', {
                 'error': error_msg
             })

         cleaned_phone = clean_uz_phone(phone_input)
         if not cleaned_phone:
             error_msg = "Telefon raqami noto'g'ri formatda!"
             if is_ajax:
                 return JsonResponse({'success': False, 'error': error_msg})
             return render(request, 'registration/reset_password.html', {
                 'error': error_msg
             })

         if new_password != confirm_password:
             error_msg = "Yangi parollar bir-biriga mos kelmadi!"
             if is_ajax:
                 return JsonResponse({'success': False, 'error': error_msg})
             return render(request, 'registration/reset_password.html', {
                 'error': error_msg,
                 'phone': phone_input
             })

         # Foydalanuvchini topish
         try:
             user = User.objects.get(phone=cleaned_phone)
             # Rolini tekshirish (Faqat mijozlar parolini tiklay oladi)
             if user.role != Role.CUSTOMER:
                 error_msg = "Xodimlarning paroli faqat menejer/admin tomonidan o'zgartirilishi mumkin!"
                 if is_ajax:
                     return JsonResponse({'success': False, 'error': error_msg})
                 return render(request, 'registration/reset_password.html', {
                     'error': error_msg,
                     'phone': phone_input
                 })

             user.set_password(new_password)
             user.save()

             success_msg = "Parolingiz muvaffaqiyatli tiklandi! Yangi parol bilan kirishingiz mumkin."
             if is_ajax:
                 return JsonResponse({'success': True, 'message': success_msg})
             return render(request, 'registration/reset_password.html', {
                 'success': success_msg
             })
         except User.DoesNotExist:
             error_msg = "Ushbu telefon raqami tizimda ro'yxatdan o'tmagan!"
             if is_ajax:
                 return JsonResponse({'success': False, 'error': error_msg})
             return render(request, 'registration/reset_password.html', {
                 'error': error_msg,
                 'phone': phone_input
             })

    return render(request, 'registration/reset_password.html')

def logout_view(request):
    """Tizimdan chiqish (Mijozlar -> home, Xodimlar -> login)"""
    is_customer = False
    if request.user.is_authenticated:
        if request.user.role == Role.CUSTOMER:
            is_customer = True

    logout(request)
    if is_customer:
        return redirect('home')  # Mijozlar bosh sahifaga (landing modalga) qaytariladi
    return redirect('login')  # Xodimlar xodimlar login portaliga qaytariladi

# --- XODIMLAR UCHUN VIEWS ---

def staff_login_view(request):
    """Muvofiqlik uchun: xodimlar sahifasiga kelganda yagona portalga yo'naltirish"""
    return redirect('login')

def staff_logout_view(request):
    """Muvofiqlik uchun: xodimlar chiqishi"""
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def staff_management_view(request):
    """
    Dashboarddagi Xodimlarni Boshqarish Sahifasi
    Faqat manager, admin va superadmin kirishi mumkin.
    Barcha xodimlarni qo'shish, ro'yxatini ko'rish va o'chirish.
    """
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard')

    error_msg = None
    success_msg = None

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        role_input = request.POST.get('role', '').strip()
        pin_input = request.POST.get('pin', '').strip()

        # Telefon raqam ekanligini tozalab tekshiramiz
        cleaned_phone = clean_uz_phone(username_input)

        if not username_input or not role_input or not pin_input:
            error_msg = "Iltimos, barcha maydonlarni to'ldiring!"
        elif role_input not in [Role.WAITER, Role.BARMAN, Role.ACCOUNTANT, Role.MANAGER, Role.ADMIN]:
            error_msg = "Roli noto'g'ri tanlandi!"
        elif not cleaned_phone:
            error_msg = "Login O'zbekiston telefon raqami formatida bo'lishi shart (+998XXXXXXXXX)!"
        elif role_input in [Role.WAITER, Role.BARMAN] and (len(pin_input) != 4 or not pin_input.isdigit()):
            error_msg = "PIN kod faqat 4 xonali raqam bo'lishi shart!"
        elif role_input not in [Role.WAITER, Role.BARMAN] and len(pin_input) < 6:
            error_msg = "Menejer, Admin va Bugalterlar uchun parol kamida 6 belgidan iborat bo'lishi shart!"
        elif User.objects.filter(phone=cleaned_phone).exists():
            error_msg = f"Ushbu '{cleaned_phone}' logini (telefon) tizimda allaqachon mavjud!"
        else:
            try:
                # Yangi foydalanuvchi yaratish
                new_user = User.objects.create_user(
                    phone=cleaned_phone,
                    password=pin_input,
                    role=role_input,
                    full_name=cleaned_phone
                )

                # StaffProfile yaratish
                staff_prof = StaffProfile.objects.create(
                    user=new_user,
                    role=role_input
                )
                if role_input in [Role.WAITER, Role.BARMAN]:
                    staff_prof.set_pin(pin_input)
                    staff_prof.save()

                success_msg = f"Yangi xodim '{cleaned_phone}' ({role_input}) muvaffaqiyatli qo'shildi!"
            except Exception as e:
                error_msg = f"Xodimni saqlashda xatolik yuz berdi: {str(e)}"

    # Barcha xodimlarni olish (Customer'dan tashqari)
    staff_list = User.objects.exclude(role=Role.CUSTOMER).order_by('role', 'phone')

    return render(request, 'management/staff_list.html', {
        'staff_list': staff_list,
        'profile': user,
        'error': error_msg,
        'success': success_msg
    })

@login_required(login_url='login')
def delete_staff_view(request, user_id):
    """Xodimni o'chirib tashlash"""
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard')

    try:
        user_to_delete = User.objects.get(id=user_id)
        # Superadmin o'zini o'chira olmaydi
        if user_to_delete != user and user_to_delete.role != Role.CUSTOMER:
            user_to_delete.delete()
    except User.DoesNotExist:
        pass

    return redirect('staff_management')

@login_required(login_url='login')
def staff_permissions_view(request, user_id):
    """
    Xodimlarning individual Django permission'larini (ruxsatnomalarini)
    tahrirlash sahifasi (chap-o'ng split select widget interfeysi).
    Faqat manager, admin va superadmin kirishi mumkin.
    """
    user = request.user
    if user.role not in [Role.MANAGER, Role.ADMIN, Role.OWNER]:
        return redirect('dashboard')

    from django.shortcuts import get_object_or_404
    from django.contrib.auth.models import Permission

    staff_user = get_object_or_404(User, id=user_id)
    if staff_user.role == Role.CUSTOMER:
        return redirect('staff_management')

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

# --- MIJOZ SHAXSIY KABINETI ---

@login_required(login_url='login')
def profile_view(request):
    """Mijozning oddiy shaxsiy kabineti (profil) sahifasi."""
    user = request.user
    if user.role != Role.CUSTOMER:
        return redirect('dashboard_home')
    return render(request, 'profile.html', {'profile': user})
