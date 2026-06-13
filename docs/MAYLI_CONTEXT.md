# 📖 MAYLI RESTOBAR — Loyiha konteksti (AI BIRINCHI SHUNI O'QISIN)

> Bu fayl loyihaning hozirgi holatini beradi. AI modellar ish boshlashdan oldin shu faylni
> va `MAYLI_PLAN.md`ni o'qisin — eski suhbatlarni titkilash shart emas.

---

## 1. Loyiha nima
Mayli Restobar — **2 qismli platforma** (bitta Django loyihasi):
1. **Rasmiy web-sayt** (marketing) — maylirestobar.uz
2. **Admin dashboard** — sayt, menyu va **mijozlar (CRM)** ni boshqarish

**Asosiy maqsad:** shaharda yetakchi bo'lish (SEO 1-o'rin) + mijozlar bazasini yuritib,
SMS/email/Telegram marketing orqali mijozlar va sotuvni oshirish.

> ⚠️ **Delivery / olib-ketish / buyurtma tizimi loyihadan butunlay olib tashlandi**
> (`orders`, `tables`, `payments`, `chat` app'lari o'chirildi). U **alohida, kattaroq loyiha**
> sifatida keyin noldan quriladi.

**Kelajak (hozir EMAS):** CRM marketing kampaniyalari (SMS/email/Telegram, tug'ilgan kun tabrigi,
promo kod), keyinroq mobil ilova va alohida delivery loyihasi.

---

## 2. Texnik stack
- **Python 3.14**, **Django 5.1**, **DRF**
- Frontend: **Django template + HTML/CSS/JS**
- Baza: **SQLite** (dev, `db.sqlite3`); **PostgreSQL** (prod — `psycopg2-binary` bor)
- i18n: **django-modeltranslation** (uz/ru/en)
- Telegram: `notifications/telegram.py` (aloqa/vakansiya bildirishnomasi ishlaydi; kelajakda CRM marketing)
- SMS (kelajak CRM): **Eskiz.uz**

---

## 3. HOZIRGI HOLAT (nima tayyor / nima yo'q)

| Qism | Holat |
|---|---|
| **Web-sayt** | ✅ TAYYOR — home, menu, about, news_list, news_detail, privacy, terms (`templates/website/`) |
| **i18n (uz/ru/en)** | ✅ modeltranslation + `i18n_patterns` (uz `/`, ru `/ru/`, en `/en/`) + custom select switcher |
| **Telegram bildirishnoma** | ✅ Vakansiya arizasi va aloqa formasi uchun ishlaydi |
| **Custom User** | ✅ `accounts.User` (phone=USERNAME_FIELD, role, full_name) + `StaffProfile`; `AUTH_USER_MODEL` o'rnatilgan |
| **Menyu (Dish)** | ✅ category FK, name/description (uz/ru/en), price, image, is_available, is_active |
| **Dashboard (CMS)** | ✅ News, Promotion, Gallery, Vacancy, ContactMessage, JobApplication, Category, Dish, SiteSettings CRUD |
| **Auth** | ✅ `restobar` app — login/logout/register/reset + xodimlarni boshqarish |
| **Mijozlar CRM** | 🔜 `crm` app + Customer modeli quriladi (BOSQICH 3) |

---

## 4. App'lar va fayl joylashuvi
**Mavjud app'lar:** `core, accounts, restobar, website, menu, notifications, dashboard` (+ `crm` — quriladi)

**Joylashuv:**
- Settings: `config/settings/` (base.py / dev.py / prod.py)
- URL: `config/urls.py` (i18n_patterns + `/i18n/`)
- Template'lar: `templates/website/`, `templates/management/` (dashboard)
- Statik: `static/assets/` (dashboard UI), `src/` (sayt CSS/JS, `src/img/menu/` 38 webp)
- Media: `media/`

---

## 5. Konventsiyalar (AI bularga amal qilsin)
- Muloqot **o'zbek tilida**.
- Kontent uz/ru/en — **django-modeltranslation**; statik matn — `{% trans %}` + `.po`/`.mo`.
- 🔴 **CSS/JS QOIDA:** inline `style=""` va `onclick=""` TAQIQLANGAN.
  CSS → `static/assets/css/custom-management.css` (dashboard) yoki `src/style.css` (sayt);
  JS → `static/assets/js/custom-management.js` yoki `src/website.js`; HTML da faqat `class`, `data-*`.
- **Mavjud ishlaydigan kodni so'ramasdan buzma/o'chirma**; ehtiyot bo'l va ko'rsat.
- **Har katta qadam oxirida** qisqa hisobot ber va tasdiq so'ra.
- Yangi narsa qurishdan oldin mavjudini o'qib ko'r (takror yozma).

---

## 6. Tayyor resurslar
- ✅ Domain (maylirestobar.uz) + server
- ✅ SMS xizmati: Eskiz.uz (`.env`: ESKIZ_EMAIL / ESKIZ_PASSWORD) — CRM uchun
- ✅ Menyu rasmlari (38 webp, `src/img/menu/`)
- ✅ Dashboard UI shabloni (`static/assets/`)

## 7. Hali kerak (foydalanuvchidan)
- Telegram bot token + admin chat ID
- Eskiz.uz login (CRM SMS — serverda test)
- Shahar nomi / NAP (SEO uchun)
