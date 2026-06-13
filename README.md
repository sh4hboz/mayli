# 🍽️ Mayli Restobar — Backend Platformasi

**Termiz shahridagi Mayli Restobar uchun to'liq Django backend.**
Marketing sayti (3 tilda), jonli chat, QR-buyurtma tizimi, xodimlar paneli, Telegram bot.

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

# 5. Ishga tushirish (ASGI + Daphne — WebSocket uchun)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Yoki oddiy dev server (WebSocket ishlamaydi, faqat HTTP)
python manage.py runserver
```

---

## 🗂️ App Tuzilishi

| App | Vazifasi | Holat |
|---|---|---|
| `core` | Abstrakt `TimeStampedModel` | ✅ |
| `accounts` | RBAC rollar, `StaffProfile` (PIN) | ✅ BOSQICH 0.4 |
| `restobar` | Mavjud auth/dashboard/buyurtma tizimi | ✅ Ishlaydi |
| `website` | Marketing sayti (3 til, SEO) | ✅ BOSQICH 1 |
| `chat` | Jonli chat: modellari + WS consumer (to'liq — BOSQICH 2.1) | ✅ BOSQICH 2.1 |
| `notifications` | Telegram webhook + bildirishnoma utilitalari | ✅ BOSQICH 0.7 |
| `menu` | Kategoriya + Taom (uz/ru/en, modeltranslation) | ✅ BOSQICH 0.8 |
| `tables` | Stollar + QR token + TableSession | ✅ BOSQICH 0.8 |
| `orders` | Buyurtmalar + OrderItem + WaiterCall | ✅ BOSQICH 0.8 |
| `payments` | To'lovlar (Payme/Click — BOSQICH 5) | 🔲 |
| `dashboard` | Xodimlar paneli app (BOSQICH 4) | 🔲 |

---

## ⚙️ Sozlamalar (Settings)

Uchta muhit:
- `config/settings/base.py` — umumiy bazaviy sozlamalar
- `config/settings/dev.py` — lokal ishlab chiqish (SQLite + InMemory channel)
- `config/settings/prod.py` — production (PostgreSQL + Redis + xavfsizlik)

```bash
# Dev (default — manage.py da belgilangan)
python manage.py runserver

# Prod
DJANGO_SETTINGS_MODULE=config.settings.prod daphne config.asgi:application
```

---

## 🔑 RBAC Rollar

`accounts.permissions` da tayyor DRF permission klasslari:

| Klass | Kimlar kira oladi |
|---|---|
| `IsCustomer` | Faqat mijozlar |
| `IsWaiter` | Ofitsiant va undan yuqori |
| `IsAccountant` | Bugalter va undan yuqori |
| `IsManager` | Menejer va undan yuqori |
| `IsOwner` | Faqat ega/admin |
| `IsStaff` | Har qanday xodim (mijoz emas) |

---

## 🌐 Asosiy URL'lar

| URL | Vazifasi |
|---|---|
| `/` | Marketing bosh sahifasi (uz) |
| `/ru/` | Marketing bosh sahifasi (ru) |
| `/en/` | Marketing bosh sahifasi (en) |
| `/menu/` | Menyu sahifasi |
| `/about/`, `/news/`, `/gallery/`, `/vacancies/`, `/contact/` | Sayf sahifalari |
| `/login/` | Xodimlar va mijozlar login portali |
| `/dashboard/` | Xodimlar boshqaruv paneli |
| `/profile/` | Mijoz kabineti |
| `/admin/` | Django Admin |
| `/api/docs/` | Swagger UI (DRF Spectacular) |
| `/api/token/` | JWT token olish |
| `/api/token/refresh/` | JWT token yangilash |
| `/sitemap.xml` | SEO sitemap (3 tilda) |
| `/robots.txt` | Robots.txt |
| `/telegram/webhook/<secret>/` | Telegram Webhook (BOSQICH 2.2) |
| `ws/chat/<visitor_id>/` | Chat WebSocket (BOSQICH 2.1) |
| `ws/support/` | Xodimlar support WebSocket (BOSQICH 2.1) |

---

## 📌 .env O'zgaruvchilar

```env
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3        # dev
# DATABASE_URL=postgres://user:pass@localhost/mayli  # prod
REDIS_URL=redis://127.0.0.1:6379

TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...              # guruh yoki kanal ID
TELEGRAM_WEBHOOK_SECRET=...

PAYME_MERCHANT_ID=
PAYME_SECRET_KEY=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
ESKIZ_EMAIL=
ESKIZ_PASSWORD=
```

---

## 🗺️ Yo'l Xaritasi

| Bosqich | Nima | Holat |
|---|---|---|
| **0** | Fundament (settings, app'lar, RBAC, ASGI, i18n, chat/notif skeleti) | ✅ Tugallandi |
| **1** | Marketing sayti (3 tilda, 8 sahifa, SEO, chat UI) | ✅ Tugallandi |
| **2** | Jonli chat + Telegram bot + dashboard chat (real-time) | 🔥 2.1 ✅ / 2.2–2.6 navbatda |
| 3 | QR menyu + stol buyurtmasi | kelajak |
| 4 | Xodimlar paneli (to'liq) | kelajak |
| 5 | To'lovlar (Payme/Click/Uzum) | kelajak |
| 6 | Dostavka + mobil API + push | kelajak |

---

## 🌍 Sayt Tashqarisidagi SEO (Eslatma)

Top'ga chiqish uchun quyidagilarni ham ro'yxatga olish kerak:
- **Google Business Profile** — uz/ru/en tavsiflar bilan
- **Yandex Business/Karta** — chet ellik ro'yxatdan o'tkazish
- **2GIS** — Termiz mahalliy qidiruvlari uchun

Barcha platformada **NAP (nom / manzil / telefon) bir xil** bo'lsin.
