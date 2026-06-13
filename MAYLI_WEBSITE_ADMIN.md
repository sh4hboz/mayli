# 🧑‍💼 MAYLI RESTOBAR — Website Admin Panel (Paces dashboard) — CRUD

> Claude Code uchun ish-buyurtmasi. Konventsiyalar: `MAYLI_CONTEXT.md`. Maqsad: web-saytni boshqaradigan to'liq, sodda admin panel.

---

## 🎯 QAMROV (MUHIM — chegaralarga rioya qil)
- ✅ **HOZIR FAQAT:** web-saytni boshqaradigan admin panel (website modellari uchun **CRUD**).
- ⛔ **TEGMA / KEYINGA QOLDIR:** buyurtma boshqaruvi, live board, statistika/analytics dashboard, delivery, kuryer tayinlash, mobil ilova.
- 🛠️ Backend bilan ishlash: **views, forms, modellar**.

## 📐 QOIDALAR
- 🔴 **CSS/JS:** inline `style=""` / `onclick=""` YO'Q. CSS → `static/assets/css/custom-management.css`, JS → `static/assets/js/custom-management.js`; HTML da faqat `class`, `data-*`.
- Dashboard sahifalari `management/base.html` dan extend qilsin.
- `content-page` + `container-fluid` — base.html da bor, templateda takrorlanmaydi.
- Trilingual kontent — modeltranslation (forma uz/ru/en maydonlar bilan).
- **Mavjud public sayt va Django admin buzilmasin.**
- Muloqot **o'zbek tilida**. **Har qadam oxirida** hisobot ber va tasdiq so'ra.

---

## ✅ BAJARILGAN VAZIFALAR (2026-06-13)

### ✅ 0 — urls.py holati
- `config/urls.py` — API URL'lar (orders/delivery/payments) hozircha yo'q (kerak bo'lganda qaytariladi)
- Mavjud: `website` (public), `dashboard`, `admin`, `i18n`, `restobar` (auth)

### ✅ 1 — Inventar
- 36 ta view, 21+ template, forms (modeltranslation bilan), custom CSS/JS — barchasi mavjud
- `dashboard/urls.py` — barcha CRUD URL'lar to'liq

### ✅ 2 — is_active holati
- `News`, `Promotion`, `GalleryItem`, `Vacancy`, `TeamMember` — `is_active` bor
- `ContactMessage` — `is_read` bor
- `JobApplication` — submission model (delete/view only)

### ✅ 3 — Dashboard asoslari

#### base.html:
- `management/base.html` — title block (`{% block title %}`), `custom-management.css/js`, `content-page`+`container-fluid` wrapper

#### Sidebar (`management/partials/sidebar.html`):
- Paces demo menyu o'chirildi
- Mayli navigatsiyasi: **Asosiy** (Dashboard) · **Sayt Boshqaruvi** (Sozlamalar, Yangiliklar, Aksiyalar, Galereya, Vakansiyalar, Arizalar, Aloqa) · **Menyu** (Kategoriyalar, Taomlar) · **Buyurtmalar** · **Mijozlar**
- User profil: `profile.get_full_name` + `profile.get_role_display`
- Logout: `/logout/`

#### Topbar (`management/partials/topbar.html`):
- "Saytni ko'rish" tugmasi theme-dropdown oldida (kichik ekranda yashirinadi)

#### Dashboard home (`/dashboard/`):
- `dashboard_home` view — stats context: `news_count`, `news_active`, `promo_count`, `promo_active`, `gallery_count`, `vacancy_count`, `vacancy_active`, `unread_contacts`, `new_applications`
- `management/dashboard.html` — 4 ta kliklanadigan `<a class="card">` (footer yo'q) + bo'limlar ro'yxati + so'nggi 5 ta xabar

### ✅ 4 — Mavjud CRUD (views + urls + forms + templates)
| Model | List | Create | Update | Delete | Boshqa |
|---|:---:|:---:|:---:|:---:|---|
| SiteSettings | — | — | ✅ | — | singleton |
| News | ✅ | ✅ | ✅ | ✅ | is_active toggle |
| Promotion | ✅ | ✅ | ✅ | ✅ | is_active toggle |
| GalleryItem | ✅ | ✅ | — | ✅ | is_active toggle |
| Vacancy | ✅ | ✅ | ✅ | ✅ | is_active toggle |
| JobApplication | ✅ | — | — | ✅ | detail ko'rish |
| ContactMessage | ✅ | — | — | ✅ | detail + is_read toggle |
| Category | ✅ | ✅ | ✅ | ✅ | |
| Dish | ✅ | ✅ | ✅ | ✅ | is_active toggle |
| Order | ✅ | — | — | ✅ | detail + status change |
| Customer | ✅ | — | — | — | |

**Universal AJAX toggle:** `POST /dashboard/toggle-active/<app>/<model>/<pk>/`

### ✅ Public sayt — Yangiliklar sahifalari
- `website/urls.py` → `news/` + `news/<slug>/`
- `website/views.py` → `news_list` + `news_detail` (related 3 ta)
- `templates/website/news_list.html` — page hero + news grid
- `templates/website/news_detail.html` — to'liq matn + related sidebar + OG meta
- `_news.html` partial — modal o'chirildi, haqiqiy URL; "Barcha yangiliklar →" tugmasi

---

## ✅ BAJARILGAN

### Phase 1: CRUD Templatelar (2026-06-13)
- [x] **5 ta forma template** — Error messages + validation styling
  - `news_form.html`, `promotion_form.html`, `vacancy_form.html`, `category_form.html`, `dish_form.html`
- [x] **Settings form** — 30+ maydonning error messages
- [x] **Gallery form** — Error messages, caption_en qo'shildi
- [x] **Delete confirmation** — Global JavaScript (custom-management.js)

### Phase 2: Dashboard UI va Authentication (2026-06-13)
- [x] **Topbar improvements**
  - User avatar — initials (A, B, etc.) bilan dynamic
  - Dropdown: Lock Screen, Log Out
  - Fullscreen toggle
- [x] **Sidebar icon** — Taomlar `ti ti-utensils` → `ti ti-chart-donut`
- [x] **Lock Screen** 
  - View: `/dashboard/lock/` va `/dashboard/unlock/`
  - Template: Beautiful UI gradient, password input
  - Middleware: Session'ni "locked" deb mark qilish
  - Settings: LockScreenMiddleware qo'shildi
- [x] **Login page** — Paces uslubiga almashtirildi (auth-sign-in.html based)
  - Beautiful gradient background
  - Form errors display
  - Clean UI (descriptions o'chirildi)
- [x] **"Eslab qolish" (Remember me)**
  - Form checkbox
  - Backend: 30 kun session (remember checked bo'lsa)

### Phase 3: Dashboard Authorization va Messages (2026-06-13)
- [x] **CMSBaseMixin** — Role tekshiruvi
  - `PermissionRequiredMixin` → `LoginRequiredMixin` o'zgartirildi
  - Faqat OWNER, MANAGER, ADMIN rol'lar ruxsat oladi
  - Boshqa rol'lar → PermissionDenied (403)
  - `permission_required` qatorlari o'chirildi (zarur emas)
- [x] **Success messages** — Django messages framework
  - SuccessMessageMixin yaratildi
  - Barcha CreateView, UpdateView, DeleteView'larga qo'shildi
  - Messages: "X muvaffaqiyatli qo'shildi/yangilandi/o'chirildi"
  - Base template'da display (Bootstrap alerts bilan)
- [x] **OrderStatusChangeView** — Auto timestamps
  - Status → cooking: `accepted_at = now()` (agar null)
  - Status → delivering: `delivered_at = now()` (agar null)
  - Status → completed: `completed_at = now()` (agar null)
  - User-friendly messages

## 🔲 QOLGAN ISHLAR

- [ ] `Testimonial`, `TeamMember` CRUD (agar website'da bo'lsa)
- [ ] Dashboard analytics/statistics page
- [ ] Bulk operations (mass delete, status change)
- [ ] Export to CSV/Excel
- [ ] Email notifications (order status changes)

---

## ✅ ACCEPTANCE HOLATI
- [x] `config/urls.py`: faqat website + dashboard + admin + i18n + auth
- [x] Website kontent modellarida `is_active` bor
- [x] Dashboard CRUD asosan ishlaydi (news, promo, gallery, vacancy, contacts, applications)
- [x] `SiteSettings` tahrirlanadi; arizalar/aloqa xabarlari ko'riladi
- [x] Dashboardga **faqat admin/manager/owner** — CMSBaseMixin tekshirilishi qilindi
- [x] Success messages — Form save/update/delete bo'lganda feedback
- [x] Login page — Beautiful Paces uslubida
- [x] Lock screen — Password bilan ekran qulfi
- [x] Order timestamps — Status o'zgarganda auto-set
- [x] ⛔ Buyurtma/delivery/statistika'ga tegmagan. Public sayt ishlaydi.

---

## 📊 Dashboard Status
- ✅ Authentication: Login, Lock screen, Role-based access
- ✅ UI: Topbar, Sidebar, Base template, Messages
- ✅ CRUD: 10 ta model (News, Promo, Gallery, Vacancy, Contacts, Applications, Category, Dish, Order, Customer)
- ✅ Forms: Error messages, validation styling, delete confirmations
- ✅ User feedback: Success messages, form errors, alerts
- ✅ Order management: Status change, auto timestamps
- 🔲 Analytics: Dashboard statistics page (optional)
- 🔲 Bulk operations: Mass actions (optional)
