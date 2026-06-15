# 🍽️ Mayli Restobar — Backend Platformasi

**Termiz shahridagi Mayli Restobar uchun Django backend.**
Hozirgi fokus: **(1) marketing sayti (3 tilda, SEO)** va **(2) mijozlar bilan ishlash uchun CRM tizimi**.

> ℹ️ Delivery / olib-ketish / buyurtma tizimi loyihadan **olib tashlandi** —
> u alohida, kattaroq loyiha sifatida keyin qayta quriladi.

---

## ⚡ Tezkor Ishga Tushirish

```bash
# 1. Virtual muhit va paketlar
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. .env faylni sozlang
cp .env.example .env
# .env ichida kerakli qiymatlarni to'ldiring

# 3. Ma'lumotlar bazasi
python manage.py migrate

# 4. Superuser
python manage.py createsuperuser

# 5. Ishga tushirish (dev)
python manage.py runserver
```

---

## 🗂️ App Tuzilishi

| App | Vazifasi | Holat |
|---|---|---|
| `core` | Abstrakt `TimeStampedModel` | ✅ |
| `accounts` | RBAC rollar (`User`, phone=USERNAME_FIELD), `StaffProfile` (PIN) | ✅ |
| `restobar` | Auth (login/logout/register/reset) + xodimlarni boshqarish | ✅ |
| `website` | Marketing sayti (3 til, SEO, yangiliklar, aksiya, galereya, vakansiya, aloqa) | ✅ |
| `menu` | Kategoriya + Taom (uz/ru/en, modeltranslation) | ✅ |
| `notifications` | Telegram outbound bildirishnoma (aloqa/vakansiya; kelajakda CRM marketing) | ✅ |
| `dashboard` | Boshqaruv paneli (CMS) — sayt + menyu + CRM | ✅ |
| `crm` | Mijozlar bazasi + marketing (SMS/email/Telegram) | ✅ (Campaign 🔜) |

> Olib tashlangan app'lar: ~~`orders`, `tables`, `payments`, `chat`~~ (delivery/buyurtma keyingi alohida loyiha).

---

## ⚙️ Sozlamalar (Settings)

Uchta muhit:
- `config/settings/base.py` — umumiy bazaviy sozlamalar
- `config/settings/dev.py` — lokal ishlab chiqish (SQLite)
- `config/settings/prod.py` — production (PostgreSQL + Redis + xavfsizlik)

```bash
# Dev (default — manage.py da belgilangan)
python manage.py runserver

# Prod
DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi:application
```

---

## 🔑 RBAC Rollar

`accounts.permissions` da tayyor DRF permission klasslari:

| Klass | Kimlar kira oladi |
|---|---|
| `IsCustomer` | Faqat mijozlar |
| `IsStaff` | Har qanday xodim (mijoz emas) |
| `IsManager` | Menejer va undan yuqori |
| `IsOwner` | Faqat ega/admin |

Dashboard'ga faqat **OWNER, MANAGER, ADMIN** kira oladi (`dashboard.views.CMSBaseMixin`).

---

## 🌐 Asosiy URL'lar

| URL | Vazifasi |
|---|---|
| `/`, `/ru/`, `/en/` | Marketing bosh sahifasi (3 til) |
| `/menu/` | Menyu sahifasi |
| `/about/`, `/news/`, `/news/<slug>/` | Sayt sahifalari |
| `/privacy-policy/`, `/terms-conditions/` | Huquqiy sahifalar |
| `/login/` · `/logout/` | Login portali (mijoz + xodim) |
| `/profile/` | Mijoz kabineti |
| `/dashboard/` | Xodimlar boshqaruv paneli (CMS) |
| `/admin/` | Django Admin |
| `/api/docs/` | Swagger UI (DRF Spectacular) |
| `/sitemap.xml` · `/robots.txt` | SEO |

---

## 📌 .env O'zgaruvchilar

```env
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3        # dev
# DATABASE_URL=postgres://user:pass@localhost/mayli  # prod

TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...              # guruh yoki kanal ID

# CRM SMS marketing (FAZA 5)
ESKIZ_EMAIL=                            # Eskiz.uz akkaunt email
ESKIZ_PASSWORD=                         # Eskiz.uz akkaunt paroli
ESKIZ_SMS_FROM=MAYLI                    # SMS yuboruvchi nomi
```

---

## 🗺️ Yo'l Xaritasi

| Bosqich | Nima | Holat |
|---|---|---|
| **0** | Fundament (settings, app'lar, RBAC, i18n) | ✅ |
| **1** | Marketing sayti (3 tilda, SEO) | ✅ |
| **2** | Boshqaruv paneli (CMS) — sayt + menyu | ✅ |
| **3** | **Mijozlar CRM** — baza + dashboard CRUD + segmentlash | ✅ |
| **4** | **Production tozalash** — legacy settings, docs, requirements-dev | ✅ |
| **5** | **CRM marketing kampaniyalari** — SMS/email/Telegram (Eskiz API) | 🔜 tayyor |
| — | Delivery & Take away — **alohida katta loyiha** (keyin) | rejada |

---

## 🌍 Sayt Tashqarisidagi SEO (Eslatma)

1-o'ringa chiqish uchun: **Google Business Profile**, **Yandex Business/Karta**, **2GIS** —
uz/ru/en tavsiflar bilan. Barcha platformada **NAP (nom / manzil / telefon) bir xil** bo'lsin.
