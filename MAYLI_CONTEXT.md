# 📖 MAYLI RESTOBAR — Loyiha konteksti (AI BIRINCHI SHUNI O'QISIN)

> Bu fayl loyihaning hozirgi holatini beradi. AI modellar ish boshlashdan oldin shu faylni va `MAYLI_PLAN.md`ni o'qisin (delivery/takeaway ustida ishlaganda — `MAYLI_DELIVERY.md` ham) — eski suhbatlarni titkilash shart emas.

---

## 1. Loyiha nima
Mayli Restobar — **3 qismli restoran platformasi** (bitta Django loyihasi):
1. **Rasmiy web-sayt** (marketing) — maylirestobar.uz
2. **Delivery & Take away** (web) — header'dagi link orqali kiriladi
3. **Admin dashboard** (Paces shablon asosida) — hammasini boshqarish

**Asosiy maqsad:** shaharda yetakchi/yagona bo'lish → internetdan qidirilganda **1-o'rinda chiqish (SEO)** + qulay, sodda, yoqimli delivery/takeaway.

**Kelajak (hozir EMAS):** mobil ilova (React Native, API orqali, Android+iOS — productionда sinovlardan keyin), mijozlar bazasi + marketing (SMS/email/Telegram/push, tug'ilgan kun tabrigi, promo kod), POS/kiosk va restoran buyurtma boshqaruv tizimi.

---

## 2. Texnik stack
- **Python 3.14.4**, **Django 5.1**, **DRF 3.17.1**
- Frontend: **Django template + HTML/CSS/JS** (+ DRF API delivery uchun)
- Baza: **SQLite** (`db.sqlite3`); `psycopg2-binary` requirements'da bor (PostgreSQL kelajakda)
- i18n: **django-modeltranslation**
- SMS: **Eskiz.uz**
- Telegram: `notifications/telegram.py` (vakansiya/aloqa formasi bildirishnomasi ishlaydi)
- **Delivery uchun (qo'shiladi):** SimpleJWT (mijoz JWT), Shapely (zona), Yandex Geocoder/Maps, reportlab + openpyxl (hisobot eksport) — to'liq: `MAYLI_DELIVERY.md`
- ⚠️ Eslatma: Django 5.1 rasman Python 3.10–3.13'ni qo'llab-quvvatlaydi. Agar 3.14 bilan muammo chiqsa, Django 5.2+ ni ko'rib chiqing.

---

## 3. HOZIRGI HOLAT (nima tayyor / nima yo'q)

| Qism | Holat |
|---|---|
| **Web-sayt (8 sahifa)** | ✅ TAYYOR — home, menu, about, news_list, news_detail, gallery, vacancies, contact (`templates/website/`) |
| **i18n (uz/ru/en)** | ✅ modeltranslation bor (`website/translation.py`, `menu/translation.py`). **i18n_patterns + prefix** (uz `/`, ru `/ru/`, en `/en/`) — **QOLADI**; faqat tugmalar o'rniga chiroyli **custom select** switcher qo'shiladi |
| **Telegram bildirishnoma** | ✅ Vakansiya arizasi va aloqa formasi uchun ishlaydi |
| **Custom User** | ⚠️ `accounts/models.py`'da `User(AbstractUser)` (phone=USERNAME_FIELD, role, full_name) + `StaffProfile` YOZILGAN, lekin `AUTH_USER_MODEL` o'rnatilganmi — **TEKSHIRILSIN** (Phase 0) |
| **Dish model** | ✅ category FK, name/description (uz/ru/en), price, image, is_available, is_active, prep_time |
| **Delivery/Take away** | 🟡 MODEL bor (`orders/models.py`: OrderType.DELIVERY, TAKEAWAY), lekin **UI/savat/buyurtma YO'Q** |
| **Eski dashboard** | 🟡 `management/` CMS ishlaydi (News, Promotion, Gallery, Vacancy, ContactMessage). **Paces bilan almashtiriladi** |
| **Paces dashboard** | 📦 Shablon fayllari `D:\mayli\static\` da — AI shu yerdan o'qib foydalansin |
| **Menyu rasmlari** | ✅ `src/img/menu/` da 38 ta `.webp`; `media/dishes/` da yuklangan rasmlar bo'lishi mumkin |

---

## 4. App'lar va fayl joylashuvi
**Mavjud app'lar:** `core, accounts, menu, orders, payments, tables, chat, notifications, website, dashboard, restobar`

⚠️ **MUHIM (Phase 0'da tekshirilsin):** AI hisobotiga ko'ra `settings.py`'da `INSTALLED_APPS` faqat `restobar`ni ko'rsatgan va `AUTH_USER_MODEL` yo'q edi — LEKIN haqiqiy settings **`D:\mayli\config\settings\`** (base/dev/prod) da bo'lishi mumkin. Loyiha hozir ishlayotgan bo'lsa, demak to'g'ri settings boshqa joyda. **Birinchi shuni aniqlash kerak.**

**Joylashuv:**
- Settings: `D:\mayli\config\settings\` (base.py / dev.py / prod.py taxminan)
- URL: `config/urls.py` (i18n_patterns + `/i18n/` yo'li bor)
- Template'lar: `templates/website/`, `management/`
- Statik: `D:\mayli\static\` (Paces shabloni ham shu yerda), `src/img/menu/` (38 webp)
- Media: `media/dishes/`

---

## 5. Konventsiyalar (AI bularga amal qilsin)
- Muloqot **o'zbek tilida**
- Kontent uz/ru/en — **django-modeltranslation** orqali; statik matn — `{% trans %}`/`{% blocktrans %}` + `.po`/`.mo`
- Delivery API — **DRF**
- 🔴 **CSS/JS QOIDA:** inline `style=""` va `onclick=""` TAQIQLANGAN. CSS → `static/src/<sahifa>.css`, JS → `static/src/<sahifa>.js`; HTML da faqat `class` va `data-*` (Pingvin loyihasidan olingan toza qoida)
- **Mavjud ishlaydigan kodni buzma**; eski modelga (ayniqsa orders, accounts) tegganda ehtiyot bo'l va ko'rsat
- **Har katta qadam oxirida** qisqa hisobot ber va tasdiq so'ra
- Yangi narsa qurishdan oldin mavjudini o'qib ko'r (takror yozma)

---

## 6. Tayyor resurslar (foydalanuvchida bor)
- ✅ Domain (maylirestobar.uz) + server
- ✅ SMS xizmati: Eskiz.uz (`.env`: ESKIZ_EMAIL / ESKIZ_PASSWORD)
- ✅ Menyu rasmlari (38 webp)
- ✅ Paces dashboard shabloni (`static/` da)

## 7. Hali kerak bo'ladigan (foydalanuvchidan)
- Yandex Maps API kaliti (delivery xaritasi uchun)
- Delivery zonasi chegaralari (polygon koordinatalari)
- Shahar nomi (SEO kontenti uchun)
- ~~Til/SEO qarori~~ ✅ HAL QILINDI: URL-prefiks (`/ru/`, `/en/`) qoladi + custom select
