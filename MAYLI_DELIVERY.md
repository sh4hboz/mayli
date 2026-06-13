# 🛵 MAYLI RESTOBAR — Delivery & Take away tizimi (batafsil spetsifikatsiya)

> Bu spec boshqa loyiha — **"Pingvin"** ning ishlaydigan (deyarli tugagan) delivery tizimidan olingan va Mayli'ga moslangan. Delivery/Take away ustida ishlayotgan AI shu faylni o'qisin (`MAYLI_CONTEXT.md` + `MAYLI_PLAN.md` bilan birga).

---

## 0. MAYLI'GA MOSLASHDA FARQLAR (Pingvin'dan farqi)
| Pingvin | Mayli'da |
|---|---|
| `Product` modeli | **`Dish`** (menu app, i18n bilan) ishlatiladi |
| Faqat uz (yoki uz/ru) | **Trilingual uz/ru/en** (modeltranslation + `{% trans %}`) |
| Faqat delivery (table/takeaway tegmagan) | **Delivery + Take away** ikkalasi |
| Arclon admin template | **Paces** shabloni (`static/` da) |
| To'lov: naqd + online (chek rasmi) | Hozircha **faqat naqd** (online/chek rasmi — keyin) |
| Rollar: admin/waiter/delivery/chef/client | Mayli rollariga **`COURIER` + `CHEF`** qo'shiladi |

**Saqlanadi (Pingvin'dan o'zgartirmasdan olinadi):** Order status oqimi, race-condition himoyasi, OTP login, Yandex xarita + Shapely zona, Setting-asosli konfiguratsiya, live board, status o'zgarish qoidalari, kuryer filtri, Telegram xabar, statistika eksport.

---

## 1. STACK (delivery uchun qo'shimcha)
- DRF + **SimpleJWT** (mijoz JWT auth) + **Django session** (xodim auth)
- **Shapely** (yetkazib berish zonasi — geo polygon)
- **Yandex Geocoder API** (koordinatdan manzil — reverse geocode) + **Yandex Maps JS API** (checkout xaritasi)
- **Telegram Bot API** (yangi buyurtma xabari)
- **reportlab + openpyxl** (hisobot eksport — PDF, Excel)
- **Eskiz.uz** (OTP SMS)

## 2. 🔴 CSS/JS QOIDA (butun loyihaga — Pingvin'dan olingan)
- inline `style=""` va `onclick=""` **TAQIQLANGAN**
- Barcha CSS → `static/src/<sahifa>.css`, barcha JS → `static/src/<sahifa>.js`
- HTML da faqat `class` va `data-*` atributlar

## 3. ROLLAR (Mayli `User.role` ni moslash)
Delivery uchun kerakli rollar va Mayli'ga moslash:

| Vazifa | Pingvin | Mayli'da |
|---|---|---|
| Mijoz | client | `CUSTOMER` (mavjud) |
| Kuryer | delivery | **`COURIER`** (qo'shiladi) |
| Oshpaz | chef | **`CHEF`** (qo'shiladi) |
| To'liq boshqaruv | admin | `OWNER` / `MANAGER` / `ADMIN` (mavjud) |
| Hisobot/moliya | — | `ACCOUNTANT` (mavjud) |

→ `accounts.User.role` choices'ga `COURIER` va `CHEF` qo'sh. Ruxsatlar 7-bo'limdagi qoidalar bo'yicha.

---

## 4. MODELLAR (Mayli'ga moslash)

**`accounts.User`** (mavjud — kengaytiriladi): `phone`=USERNAME_FIELD, `role`, `full_name` bor. **QO'SH:** `extra_phone` (qo'shimcha telefon), `birth_date`, `gender` (mijoz profili + kelajak tug'ilgan kun tabrigi). Xodim **PIN** → `StaffProfile`'da (hashlangan).

**`menu.Category` / `menu.Dish`** (mavjud — SAQLA): i18n bilan. `Dish`'da `is_available`, `is_active`, `price`, `image`, `prep_time` bor. (Pingvin `Category.is_drink` kerak bo'lsa qo'shilsin: ichimlik toifasi.)

**`orders.Order`** (Pingvin modelini moslab kengaytir):
- **STATUS:** `pending` → `cooking` → `delivering` → `completed` (+ `cancelled` — faqat admin)
- **ORDER_TYPE:** `DELIVERY` (ishlayotgan), `TAKEAWAY` (qo'shiladi), `TABLE` (keyin)
- `daily_id` — bugungi umumiy tartib raqami (har kuni qaytadan)
- `type_daily_id` — tur bo'yicha tartib (faqat delivery ichida)
- 🔴 **RACE CONDITION HIMOYA:** `daily_id`/`type_daily_id` yaratishda `select_for_update()` + `transaction.atomic()` — parallel so'rovlarda bir xil ID olmaslik uchun
- `client` FK(User), `client_name`, `client_phone`, `location` (Yandex Geocoder matni), `delivery_lat`/`delivery_lng`
- `total_price`, `payment_method` (`cash` | `online`), `payment_image` (online chek rasmi — keyin)
- `delivery_courier` FK(User, COURIER), `comment`
- `created_at`, `accepted_at` (cooking'da), `delivered_at` (delivering'da), `completed_at` (completed/cancelled'da)
- **Takeaway uchun:** `pickup_time` (olib ketish vaqti); `delivery_lat/lng`/`location` shart emas
- INDEKSLAR: `created_at`, `status`, `daily_id`, `order_type+status`

**`orders.OrderItem`:** `order`, **`dish`** (Pingvin `product` o'rniga) FK, `quantity`, `price` (🔴 buyurtma paytidagi narx **snapshot** — keyin narx o'zgarse ham o'zgarmaydi)

**`OtpCode`** (yangi): `phone`, `code` (6 xona), `purpose` (`registration`|`phone_change`), `expires_at` (2 daqiqa), `is_used`. Rate limit bor (juda tez so'rasa bloklash).

**Konfiguratsiya — `Setting` (key-value) yoki `SiteSettings`** (Mayli'da SiteSettings bor): `DELIVERY_START_TIME` (08:00), `DELIVERY_END_TIME` (22:00), `min_order_price` (masalan 100000), `delivery_fee`, `free_delivery_threshold`. Admin DB'dan o'zgartiradi, server restart kerak emas.

**`PageContent`** (yangi yoki mavjud): `slug` (unique), `title`, `content` (HTML), `is_published` — terms/privacy sahifalari uchun.

---

## 5. URL / API (Mayli)

**Mijoz sahifalari** (i18n_patterns — uz `/`, ru `/ru/`, en `/en/`):
- `/order/` (yoki `/delivery/` + `/takeaway/`) → menyu + savatcha boshlash
- `/cart/` → savatcha, `/checkout/` → buyurtma (login shart)
- `/my-orders/` → buyurtma kuzatuvi, `/profile/` → profil
- `/terms/`, `/privacy/` → PageContent

**API (`/api/`):**
- `POST /api/auth/client/login/` → `{ phone_number }` (OTP yuboradi — Eskiz)
- `POST /api/auth/client/verify-otp/` → `{ phone_number, code }` → JWT (access+refresh)
- `GET  /api/auth/me/` → joriy profil
- `POST /api/auth/staff/login/` → `{ username, pin }` (session)
- `POST /api/auth/staff/logout/`, `GET /api/auth/staff/me/`
- `POST /api/orders/create/` → yangi buyurtma
- `GET  /api/orders/active/` → faol (staff only, polling)
- `GET  /api/orders/history/` → arxiv (staff only)
- `POST /api/orders/<pk>/update-status/` → status / kuryer yangilash
- `GET  /api/orders/<pk>/status/` → bitta buyurtma statusi (AllowAny)
- `GET  /api/my-orders/status/` → mijozning faol buyurtmalari (polling, JWT)
- `GET  /api/couriers/workload/` → kuryer yuklanishi
- `GET  /api/dashboard/stats/` → bugungi statistika
- `GET  /api/categories/`, `GET /api/products/` (Dishes) → ViewSet (AllowAny, React Native uchun ham)
- Statistika: `/api/dashboard/chart/{daily,weekly,monthly}/`, `/api/reports/top-products/`, `/api/reports/summary/`, `/api/reports/export/` (Excel/PDF)

🔴 **API-first (React Native uchun):** nested serializer (to'liq ma'lumot), **full URL** rasm, **ISO** sana format.

---

## 6. MIJOZ BUYURTMA JARAYONI (step by step)

**QADAM 1 — OTP login:** menyu ochiq, buyurtma uchun login. `phone` → OTP (6 xona, 2 min, bir marta, rate limit, Eskiz orqali) → JWT. Barcha mijoz so'rovlarida `Authorization: Bearer <token>`.

**QADAM 2 — Menyu + savatcha:** `/order/` server-side render (kategoriya + Dish'lar, trilingual). **Sticky kategoriya bar** (filtr). Dish kartochkasida "+" → savatcha **localStorage** da `[{dish_id, quantity, title, price}]`.

**QADAM 3 — Savatcha (`/cart/`):** miqdor o'zgartirish/o'chirish, jami summa. "Oldingi manzillarim" dropdown (mijozning oldingi koordinatli manzillaridan). Login bo'lmasa → login modal.

**QADAM 4 — Checkout (`/checkout/`, login shart):**
- **DELIVERY:** ism/asosiy telefon (auto, readonly), qo'shimcha telefon (ixt.), **Yandex xarita** (4.A), to'lov (**naqd** — hozir), izoh.
- **TAKEAWAY:** ism/telefon, **olib ketish vaqti**, izoh — **xarita YO'Q**.

**4.A — Yandex xarita (manzil tanlash):**
- *Frontend:* SDK (`apikey={{ yandex_api_key }}&lang=uz_UZ`). Modal xarita; markaz — shahar koordinatasi yoki `localStorage`'dagi oxirgi manzil. **Markaziy fixed pin** (CSS bilan ekran markazida qotgan) — foydalanuvchi xaritani suradi. `boundschange` → markaz koordinatasi → **500ms debounce** bilan reverse geocode → manzil matnini panelда ko'rsat. Tasdiqda lat/lng yashirin inputlarga.
- *Backend (`OrderCreateSerializer.validate`):* (1) koordinata shart, (2) **Shapely** polygon (`DELIVERY_ZONE_COORDS`) ichidami — `is_in_delivery_zone(lat, lng)`; tashqarida bo'lsa "bu hudud yetkazib berish zonasida emas", (3) **ish vaqti** (Setting `DELIVERY_START/END_TIME`), (4) **min summa** (Setting `min_order_price`). Saqlashda `reverse_geocode_address(lat,lng)` (Yandex, format `lng,lat`) → `Order.location`; API ishlamasa koordinata fallback. Kalit `settings.YANDEX_MAPS_API_KEY`.

**Buyurtma yaratilгach:** OrderItem'lar (narx snapshot), **Telegram xabar** (8-bo'lim), (ixt.) mijozga SMS tasdiq. Response: OrderSerializer.

**QADAM 5 — Buyurtma kuzatuvi (`/my-orders/`):** faol (pending/cooking/delivering) yuqorida alohida + barcha tarix. Har buyurtmada: tartib raqam, mahsulotlar, narx, status badge, sana. Kuryer biriktirilsa — kuryer ism + telefon. **Polling har 5 soniya:** `GET /api/my-orders/status/`. **Qayta buyurtma:** oldingi mahsulotlarni bir tugma bilan savatchaga.

---

## 7. DASHBOARD — BUYURTMA BOSHQARUVI (Paces UI, Pingvin funksiyasi)

**Xodim login:** username + PIN → session. Rol redirect: courier → o'z buyurtmalari; boshqalar → faol buyurtmalar board.

**Faol buyurtmalar (live board)** — split-view:
- *Stats bar* (polling **60s**, `GET /api/dashboard/stats/`): yangi / pishmoqda / yo'lda / bugun jami / bugun tushum.
- *Chap panel* (polling **5s**, `GET /api/orders/active/`): kompakt ro'yxat — `#daily_id · status · ism · manzil · narx · timer`. **Timer rangi:** 0–10 daq yashil, 10–20 sariq, 20+ qizil.
- *O'ng panel:* tanlangan buyurtma detali — mijoz/mahsulotlar, **kuryer tanlash** (admin), **status tugmalari** (rol asosida). `POST /api/orders/<pk>/update-status/`.

**Buyurtma detali (`/dashboard/orders/<pk>/`):** progress stepper (qabul→tayyorlandi→yo'lda→yetkazildi; cancelled'da stepper yo'q), mahsulotlar jadvali, kuryer tanlash (admin), status dropdown, **online to'lovda chek rasmi yuklash** (completing'da majburiy — keyin), activity timeline (created/accepted/delivered/completed).

**Arxiv:** completed buyurtmalar (`GET /api/orders/history/`), filtr/qidiruv.

**🔴 STATUS O'ZGARISH QOIDALARI (rol asosida):**
- `pending → cooking`: admin yoki **chef**
- `cooking → delivering`: admin, chef, yoki **courier**
- `delivering → completed`: admin yoki **courier**
- `any → cancelled`: **FAQAT admin**
- Online buyurtmani completed qilish: chek rasmi majburiy (keyin)

**Kuryer filtri:** COURIER faqat **o'ziga biriktirilgan** buyurtmalarni ko'radi (admin — barchasini).
**Kuryer tayinlash:** faqat admin — `update-status` → `{ delivery_courier: <user_id> }`.

**Statistika (`/dashboard/statistics/`):** kunlik/haftalik/oylik diagrammalar, top mahsulotlar, jami tushum. **Eksport:** Excel (openpyxl) / PDF (reportlab) — `GET /api/reports/export/`.

**CRUD bo'limlari:** toifalar, mahsulotlar (Dish), xodimlar (faol/nofaol toggle), mijozlar (ism/telefon/sana/buyurtma soni), sayt sozlamalari (SiteSettings).

> Bularning hammasi **Paces shablonida** render qilinadi (Arclon emas). Funksiya Pingvin'dan, UI Paces'dan.

---

## 8. TELEGRAM BOT (yangi buyurtma)
Har yangi buyurtmada avtomatik formatli xabar:
```
🆕 Yangi buyurtma #<daily_id>
👤 Mijoz: <ism>      📞 <telefon>
📍 Manzil: <location>   💰 <narx> UZS   💳 <Naqd/Online>
Mahsulotlar:
• <qty>x <nom> — <narx>
🕐 <vaqt>
```
`.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

---

## 9. MUHIM TEXNIK NUANSLAR (Pingvin'dan — saqlanadi)
1. **Narx snapshot:** `OrderItem.price` buyurtma paytidagi narx.
2. **Location:** koordinata → Yandex Geocoder → matn → `Order.location`.
3. **Min summa / ish vaqti:** `Setting`'dan dinamik (DB), restart kerak emas.
4. **Race condition:** `daily_id`/`type_daily_id` — `select_for_update()` + `transaction.atomic()`.
5. **Kuryer filtri:** COURIER faqat o'zinikini ko'radi.
6. **Online to'lov:** `payment_image` completing'da majburiy (keyin — hozir naqd).
7. **Cancelled:** faqat admin; `completed_at` yoziladi; mijozda maxsus badge.
8. **API-first:** React Native uchun nested serializer, full URL, ISO sana.
9. **Delivery zone:** Shapely polygon — koordinata Mayli shahri/tumani hududida.

---

## 10. FAYL TUZILISHI (tavsiya — Mayli)
```
accounts/   → User, StaffProfile, OTP auth
menu/       → Category, Dish (i18n) — mavjud
orders/     → Order, OrderItem, status logikasi
core/utils  → OTP, Telegram, Yandex Geocoder, delivery zone (Shapely)
<client>/   → checkout, cart, my-orders template + views (i18n_patterns)
dashboard/  → buyurtma boshqaruvi (Paces) + REST API views
static/src/ → <sahifa>.css / <sahifa>.js (CSS/JS qoidasi bo'yicha)
```

## 11. ⚠️ KERAK (foydalanuvchidan)
- **Yandex Maps API kaliti** (`YANDEX_MAPS_API_KEY`)
- **Delivery zona polygon koordinatalari** (Mayli shahri/tumani chegarasi)
- **Telegram bot token + chat ID**
- **Delivery sozlamalari:** ish vaqti (start/end), min summa, dostavka narxi, bepul dostavka chegarasi

---

**Eslatma:** mavjud Mayli kodini (website, menu, accounts) buzma. Bu tizim `orders` + `dashboard` + mijoz checkout sahifalarini quradi/to'ldiradi. Har katta qadamda hisobot ber.
