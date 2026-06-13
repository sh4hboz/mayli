# 🗺️ MAYLI RESTOBAR — Yangilangan reja va vazifalar

> `MAYLI_CONTEXT.md`ni o'qigach shuni o'qing. Delivery/Take away tafsiloti — alohida `MAYLI_DELIVERY.md` da.

---

## 1. MAQSADLAR (yangilangan)
- 🥇 Shaharda **yetakchi/yagona** bo'lish → internetdan qidirilganda **1-o'rinda chiqish (SEO)**
- 🛵 **Delivery & Take away** — qulay, sodda, tushunarli, yoqimli platforma (header link orqali kiriladi)
- 🧑‍💼 **Admin dashboard** (Paces) — sayt + delivery/takeaway + mijozlarni boshqarish
- 📱 **Kelajak:** mobil ilova (React Native + API), mijozlar bazasi + marketing (SMS/email/Telegram/push, tug'ilgan kun tabrigi, promo kod), POS/kiosk, restoran buyurtma boshqaruvi

## 2. QAMROV
- **HOZIR:** web-sayt yangilash + Delivery/Take away (web) + Paces dashboard
- **KEYIN:** mobil ilova, POS/kiosk, buyurtma boshqaruv tizimi, online to'lov (Payme/Click)

---

## 3. YO'L XARITASI

| Bosqich | Nima | Holat |
|---|---|:--:|
| **0** | Holatni aniqlash + barqarorlashtirish (settings, AUTH_USER_MODEL, loyiha ishlaydimi, Paces inventari) | 🔥 |
| **1** | Sayt yangilanishlari (til switcher, footer, floating-btns, full responsive + xato tuzatish, analytics, h.k.) | 🔥 |
| **2** | Delivery & Take away (web) — savat, buyurtma, Yandex xarita + zona, naqd to'lov → **`MAYLI_DELIVERY.md`** | 🔥 |
| **3** | Admin dashboard (Paces) — eski dashboardni almashtirish + buyurtma boshqaruvi | 🔥 |
| 4 | Kelajak: mobil (React Native+API), mijoz DB + marketing, POS/kiosk | rejada |

---

## 4. BOSQICH 0 — Aniqlash va barqarorlashtirish (kod yozishdan oldin)
1. **`config/settings/` ni och** (base/dev/prod) — `INSTALLED_APPS`'da BARCHA app'lar (`core, accounts, menu, orders, payments, tables, chat, notifications, website, dashboard`) borligini tekshir. Yo'q bo'lsa qo'sh.
2. **`AUTH_USER_MODEL = 'accounts.User'`** o'rnatilganini tasdiqla.
   - ⚠️ Agar o'rnatilmagan bo'lsa va SQLite'da data bo'lsa — bu jiddiy. Migratsiya holatini tekshir. Dev data muhim bo'lmasa, eng toza yo'l: migratsiyalar + db ni qayta qurish. **Avval menga holatni ko'rsat va qaror so'ra.**
3. `python manage.py check`, `migrate`, `runserver` — loyiha **xatosiz ishlashini** tasdiqla.
4. **`static/` dagi Paces shabloni**ni ko'r — qaysi HTML/CSS/JS fayllar bor, tuzilishi qanday (Phase 3 uchun).
5. Menga qisqa hisobot ber: nima holatda, nima tuzatildi, davom etaymizmi.

---

## 5. BOSQICH 1 — Sayt yangilanishlari

### 5.1 Til almashtirish → URL-prefiks (QOLADI) + custom select ✅
**Qaror:** `/ru/`, `/en/` prefikslari **qoladi** (`i18n_patterns` saqlanadi) — xalqaro SEO uchun yaxshi (har til alohida indekslanadi, `hreflang` ishlaydi). Tugmalar o'rniga **bitta chiroyli custom select** (uz/ru/en) qo'yiladi.

**Bajarish:**
- `i18n_patterns` (prefix_default_language=False — uz `/`, ru `/ru/`, en `/en/`) **o'zgarmaydi**, saqlanadi.
- Custom select (yoki custom dropdown): joriy tilni `{% get_current_language as LANGUAGE_CODE %}` bilan aniqla; til tanlanganda **o'sha tildagi URL'ga o'tkaz** — joriy sahifaning mos til varianti. Buning uchun `{% load i18n %}` + til prefiksini to'g'ri almashtirish (template'da har til uchun havola yoki JS bilan path prefiksini almashtirish; faol til "active" ko'rinsin).
- `hreflang` (uz/ru/en + x-default) **har sahifada** bo'lsin — SEO uchun muhim.
- Select dizayni: header'da chiroyli (bayroq + til kodi yoki nom), mobil drawer'da ham. Faqat UI tugmadan **custom select**ga o'zgaradi.
- modeltranslation va `{% trans %}` URL-prefiks bilan hozirgidek to'g'ri ishlaydi — bu qismni buzma.

### 5.2 Footer
- **Xaritani footer'dan butunlay olib tashla.**

### 5.3 Floating tugmalar (floating-btns)
- **`scrollTopBtn` doim ko'rinadi.**
- Qolganlari (tel / Telegram / Instagram) — **bitta slotda, har 3 soniyada almashib turadi** (rotatsiya). Ya'ni istalgan vaqtda: scrollTopBtn + 1 ta aylanuvchi item.
- Yumshoq fade/slide animatsiya bilan almashsin.
- (Bezak chat vidjeti — alohida turaversin, hozircha deco.)

### 5.4 Full responsive + xato tuzatish
- **Barcha 8 sahifani** mobil (375px) / tablet (768px) / desktop (1440px)da tekshir va to'g'rila.
- Katta-kichik **HTML / CSS / JS xatolarni** toza qil (console errorlar, layout buzilishlari, broken image, ustma-ust elementlar).
- 🔴 CSS/JS qoidasiga amal qil (inline style/onclick yo'q; CSS/JS → `static/src/`).
- (Chrome extension tekshiruv promptidan foydalanish mumkin.)

### 5.5 Qo'shimcha (esdan chiqmasin)
- Header'da **Delivery/Take away'ga link** (masalan "Yetkazib berish").
- **Google Analytics + Yandex Metrica** (SEO/biznes uchun).
- **Maxfiylik siyosati / Shartlar** sahifasi (`PageContent`) + mijoz ma'lumot yig'ishga **rozilik (opt-in)** (SMS/email marketing huquqiy asosi).
- Bezatilgan **404 / 500** sahifalar.
- **Tezlik:** rasm webp + `loading="lazy"`, JS `defer`, fonts `preconnect`.

---

## 6. BOSQICH 2 — Delivery & Take away (web)
> 📄 **To'liq, batafsil spetsifikatsiya: `MAYLI_DELIVERY.md`** (boshqa loyiha "Pingvin"ning ishlaydigan tizimidan moslangan). Quyida faqat qisqacha — tafsilot uchun o'sha faylni o'qing.

**Asosiy nuqtalar:**
- Header link orqali kiriladi. `orders` (DELIVERY/TAKEAWAY) + `Dish` (i18n) mavjud — shulardan foydalan.
- **Mijoz auth:** telefon + **OTP (Eskiz)** → JWT (parolsiz). Menyu ochiq, buyurtma uchun login.
- 🔴 **UX (muhim):** delivery/takeaway sahifalarida **header `position:fixed` BO'LMASIN**; **kategoriyalar `position:sticky`** (scroll'da yuqorida yopishadi, "pozitsiyalar almashadi"). Savat — localStorage.
- **Delivery checkout:** Yandex xarita (markaziy fixed pin + `boundschange`→500ms reverse geocode), **Shapely** zona tekshiruvi, ish vaqti + min summa (Setting'dan). **Takeaway:** xaritasiz, olib ketish vaqti.
- **To'lov:** hozircha **naqd** (online/chek rasmi — keyin).
- Buyurtma → **Telegram** xabar + (ixt.) SMS. Status: `pending→cooking→delivering→completed` (+`cancelled`).
- 🔴 **Race-condition himoya** (`daily_id`), **narx snapshot** (OrderItem.price) — `MAYLI_DELIVERY.md` da.
- **API-first** (React Native uchun ham): nested serializer, full URL, ISO sana.
- Trilingual (uz/ru/en). Rollar: `COURIER` + `CHEF` qo'shiladi.

---

## 7. BOSQICH 3 — Admin dashboard (Paces)
> 🔥 Avval **FAQAT website CRUD** qilinadi → **`MAYLI_WEBSITE_ADMIN.md`** (`MAYLI_WEBSITE_DAVOM.md` dan keyin). Buyurtma boshqaruvi/statistika/delivery board — KEYIN (quyidagi punktlar kelajak uchun).
- **Eski `management/` dashboardni Paces shabloni bilan almashtir** (fayllar `static/` da — o'qib ishlatadi). Funksiya saqlansin, UI Paces'ga ko'chsin.
- **CMS bo'limlari:** menyu/taomlar (Dish), yangiliklar, aksiyalar, galereya, vakansiyalar, aloqa xabarlari, mijozlar, sayt sozlamalari.
- **Buyurtma boshqaruvi** (faol buyurtmalar live board + timer rangi, status oqimi, kuryer tayinlash, arxiv, statistika + **Excel/PDF eksport**) — to'liq **`MAYLI_DELIVERY.md` 7-bo'limda**; Paces UI'da render qilinadi.
- **Rol asosida** (`accounts.User.role` — ega/menejer/bugalter/oshpaz/kuryer): kim nimani ko'radi/boshqaradi. Status o'zgarish qoidalari — delivery faylida.
- Dashboard'da asosiy statistika (buyurtmalar soni, tushum).

---

## 8. BOSQICH 4 — Kelajak (hozir EMAS, vizyon uchun)
- **Mobil ilova:** React Native (Android+iOS), backend DRF **API** orqali (delivery API allaqachon API-first qilinadi).
- **Mijozlar bazasi + marketing:** SMS / email / Telegram bot / push (FCM) — yangilik, aksiya, SMS kod, **tug'ilgan kun tabrigi** (profilda `birth_date` + rejalashtirilgan jo'natish), promo kod.
- **POS / kiosk** va **restoran buyurtma boshqaruv tizimi** (oshxona, ofitsiant, stol).

---

## 9. ⚠️ MENDAN (foydalanuvchidan) KERAK
1. ~~Til/SEO qarori~~ ✅ HAL QILINDI: **URL-prefiks qoladi** (`/ru/`, `/en/`) + custom select switcher.
2. **Yandex Maps API kaliti** (delivery xaritasi uchun).
3. **Delivery zonasi koordinatalari** (polygon — yetkazib berish hududi chegarasi).
4. **Telegram bot token + chat ID** (yangi buyurtma bildirishnomasi).
5. **Delivery sozlamalari:** ish vaqti (start/end), min buyurtma summa, dostavka narxi, bepul dostavka chegarasi.
6. **Shahar nomi** (SEO kontenti uchun: "restaurant in [shahar]" va h.k.).

---

## 10. 🌍 Sayt tashqarisidagi SEO (1-o'rin uchun shart, kod emas)
Chet ellik va mahalliy mijozlar topishi uchun: **Google Business Profile**, **Yandex Business/Karta**, **2GIS** — **uz/ru/en tavsiflar, foto, ish vaqti, telefon bilan** to'ldiring. Barcha platformada NAP (nom/manzil/telefon) bir xil bo'lsin. (URL-prefiks + `hreflang` on-site SEO'ni kuchaytiradi; off-site listinglar lokal qidiruvni kuchaytiradi — ikkalasi birga ishlaydi.)

---

**Boshlash: BOSQICH 0 (holatni aniqlash). Hisobot ber, keyin bosqichma-bosqich davom et.**
