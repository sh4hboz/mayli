# 🧑‍💼 MAYLI RESTOBAR — Website Admin Panel (Paces dashboard) — CRUD

> Claude Code uchun ish-buyurtmasi. Bu **`MAYLI_WEBSITE_DAVOM.md` dan KEYIN** keladi (public sayt sayqallangach). Konventsiyalar: `MAYLI_CONTEXT.md`. Maqsad: web-saytni boshqaradigan to'liq, sodda admin panel.

---

## 🎯 QAMROV (MUHIM — chegaralarga rioya qil)
- ✅ **HOZIR FAQAT:** web-saytni boshqaradigan admin panel (website modellari uchun **CRUD**).
- ⛔ **TEGMA / KEYINGA QOLDIR:** buyurtma boshqaruvi, live board, statistika/analytics dashboard, delivery, kuryer tayinlash, mobil ilova. (Bular keyingi bosqich — hozir EMAS.)
- 🛠️ Backend bilan ishlash: **views, forms, modellar**.

## 📄 HOLAT
- **Paces template tayyor:** topbar + sidebar + content sahifalarga ajratilib **include** qilingan (base struktura bor).
- **Django admin** website modellari uchun ishlaydi (bu — dev/superuser zaxirasi, tegmaymiz). Paces dashboard — **egasi/menejer uchun brendli CMS**. Ikkalasi birga turaveradi.
- **i18n:** uz/ru/en — `django-modeltranslation`.

## 📐 QOIDALAR
- 🔴 **CSS/JS:** inline `style=""` / `onclick=""` YO'Q. CSS → `static/src/<sahifa>.css`, JS → `static/src/<sahifa>.js`; HTML da faqat `class`, `data-*`.
- Dashboard sahifalari **Paces base**dan extend qilsin (topbar/sidebar/content include).
- Trilingual kontent — modeltranslation (forma uz/ru/en maydonlar bilan).
- **Mavjud public sayt va Django admin buzilmasin.**
- Muloqot **o'zbek tilida**. **Har qadam oxirida** hisobot ber va tasdiq so'ra.

---

## ✅ VAZIFALAR (shu tartibda)

### 0 — urls.py tozalash (vaqtincha)
- `config/urls.py` da web-saytga **tegishli bo'lmagan** URL'larni **VAQTINCHA comment qil** (O'CHIRMA — keyin tiklanadi): `orders`/buyurtma API, `delivery`, `payments`, `tables` va shu kabilar.
- **QOLDIR:** `website` (public sayt), **dashboard** (website-management), `django.contrib.admin`, `i18n` (`set_language`), staff **auth** (dashboard login).
- Maqsad: surface'ni kichraytirib, tugallanmagan delivery/orders kodidan keladigan xatolarni oldini olish.

### 1 — Inventar (kod yozishdan oldin)
- Mavjud dashboard (Paces) template va view'larini ko'r — **qaysi website CRUD allaqachon bor, qaysi yo'q** aniqla (takror qilma).
- Paces base (topbar/sidebar/content include) tuzilishini tushun.
- Hisobot ber: nima bor, nima qilinadi.

### 2 — Modellarga `is_active` qo'shish
- **Kontent modellariga** `is_active = BooleanField(default=True)` qo'sh (yo'q bo'lsa): `News`, `Promotion`, `GalleryItem`, `Testimonial`, `Vacancy`, `TeamMember`. (`Dish`'da bor.)
- **Submission modellari** (`JobApplication`, `ContactMessage`) — is_active emas, balki **`is_read`/holat** mantiqliroq (qabul/ko'rildi).
- Migration qil.
- 🔴 **Public sayt query'lari `is_active=True` (va kerakli `is_published`) bo'yicha filtrlasin**; dashboard esa hammasini ko'rsatib **toggle** bersin.

### 3 — Dashboard asoslari
- **Staff login** (Django session) — **rol asosida**: faqat `admin`/`manager`/`owner` kirsin (`login_required` + rol tekshiruvi). Public foydalanuvchi yoki mijoz kira olmasin.
- **Sidebar navigatsiya** (website bo'limlari): Sayt sozlamalari · Yangiliklar · Aksiyalar · Galereya · Sharhlar · Vakansiyalar · Arizalar · Aloqa xabarlari · Jamoa.
- **Dashboard bosh sahifa:** oddiy overview kartalari — yangiliklar/aksiyalar soni, o'qilmagan aloqa xabarlari, yangi arizalar. (⛔ buyurtma/tushum statistikasi YO'Q.)

### 4 — CRUD (har bir model)
Tavsiya: Django generic CBV (`ListView`/`CreateView`/`UpdateView`/`DeleteView`) + `ModelForm` + Paces template'lar.
- **Trilingual kontent modellari** (`News`, `Promotion`, `GalleryItem`, `Testimonial`, `Vacancy`, `TeamMember`):
  - **List:** is_active **toggle**, qidiruv, pagination, sana.
  - **Create / Edit:** forma uz/ru/en maydonlar bilan (modeltranslation), rasm upload (kerak joyda).
  - **Delete:** **tasdiq** (confirmation modal/sahifa).
- **`SiteSettings`** (singleton): bitta **edit** forma (kontakt, ijtimoiy, about, stats, lat/lng, ish vaqti...).
- **`JobApplication` / `ContactMessage`** (admin yaratmaydi): **list + ko'rish + o'qildi belgilash + o'chirish**.
- **`GalleryItem`:** rasm yuklash (upload), tartib.
- `is_active` toggle: tugma yoki kichik AJAX endpoint (`POST .../toggle-active/` → `{is_active}`).

### 5 — Sayqal va xavfsizlik
- Forma **validatsiya** + muvaffaqiyat/xato xabarlari (Django `messages`).
- Dashboard view'lar **staff-only** (rol/permission tekshiruvi har joyda).
- Paces (Bootstrap) — **mobil responsive** ekanini tekshir.
- CSS/JS qoidasiga amal qil.

---

## ✅ ACCEPTANCE
- [ ] `config/urls.py`: faqat website + dashboard + admin + i18n + auth qoldi (orders/delivery/payments **comment** qilingan).
- [ ] Website kontent modellarida `is_active` bor; public faqat `is_active=True` ko'rsatadi.
- [ ] Har website modeli uchun dashboarddan **CRUD ishlaydi** (trilingual, is_active toggle, delete confirmation).
- [ ] `SiteSettings` tahrirlanadi; arizalar/aloqa xabarlari ko'riladi va boshqariladi.
- [ ] Dashboardga **faqat admin/manager/owner** kiradi; public/mijoz kira olmaydi.
- [ ] ⛔ Buyurtma / delivery / statistika'ga **TEGILMAGAN**. Public sayt + Django admin **ishlaydi**, mavjud kod buzilmagan.

---

**Boshla: 0-qadam (urls.py tozalash) + 1-qadam (inventar). Hisobot ber, keyin bosqichma-bosqich davom et.**
