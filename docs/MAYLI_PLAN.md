# 🗺️ MAYLI RESTOBAR — Reja va vazifalar

> Loyiha konteksti uchun avval `MAYLI_CONTEXT.md`ni o'qing.

---

## 1. MAQSADLAR
- 🥇 Shaharda **yetakchi** bo'lish → internetdan qidirilganda **1-o'rinda chiqish (SEO)**.
- 🧑‍🤝‍🧑 **Mijozlar bilan ishlash (CRM):** mijozlar bazasini yuritish va **doimiy ko'paytirish**.
- 📣 **Marketing:** SMM (Instagram) ga qo'shimcha **SMS / Email / Telegram** orqali reklama yuborib,
  sotuv va mijozlar sonini oshirish.
- 🧑‍💼 **Admin dashboard** — sayt + menyu + mijozlarni boshqarish.

## 2. QAMROV
- **HOZIR:** marketing web-sayt (deyarli tayyor) + **Mijozlar CRM tizimi**.
- **KEYIN:** CRM marketing kampaniyalari (SMS/email/Telegram yuborish).
- **ALOHIDA LOYIHA (keyin):** Delivery & Take away — noldan, kattaroq loyiha sifatida qayta quriladi.

---

## 3. YO'L XARITASI

| Bosqich | Nima | Holat |
|---|---|:--:|
| **0** | Fundament (settings, AUTH_USER_MODEL, app'lar, RBAC, i18n) | ✅ |
| **1** | Marketing sayti (til switcher, footer, responsive, SEO) | ✅ |
| **2** | Boshqaruv paneli (CMS) — sayt + menyu CRUD | ✅ |
| **3** | **Mijozlar CRM** — Customer modeli + dashboard CRUD + qidiruv/segmentlash | ✅ |
| **4** | **Production tozalash** — legacy settings, docs, requirements-dev | ✅ |
| **5** | **CRM marketing** — kampaniya tizimi (SMS/email/Telegram, Eskiz API) | 🔜 tayyor |
| — | Delivery & Take away — **alohida katta loyiha** | rejada |

---

## 4. BOSQICH 4 — Production tozalash (✅ 2026-06-14)

**Maqsad:** loyihani production uchun tayyorlash, legacy fayl va docs tozalash.

- **Legacy `config/settings.py`** (hardcoded SECRET_KEY) o'chirildi — `config/settings/` paketi ishlatiladi.
- **Docs struktura:** 6 ta `.md` fayl `docs/` papkasiga ko'chirildi (MAYLI_PLAN, MAYLI_CONTEXT, MAYLI_WEBSITE_ADMIN va h.k.).
- **requirements-dev.txt:** development uchun (pytest-django, black, flake8, django-debug-toolbar, isort).
- **Git cleanup:** `.env`, `db.sqlite3`, `staticfiles/` allaqachon `.gitignore`'da.
- **Tekshiruv:** Django check ✅ 0 xato, migrations toza, collectstatic ✅ 427 fayl.

---

## 5. BOSQICH 5 — CRM marketing (🔜 tayyor boshlashga)

**Maqsad:** SMS/email/Telegram orqali mass marketing kampaniyalarini jo'natish tizimi.

**Modellar:**
- **`Campaign`:** nomi, tavsif, kanal (sms/email/telegram), shablon ({{first_name}} suporta), target tags, status (draft/scheduled/sent), timestamps, counts (success/fail).
- **`CampaignLog`:** har customer-kanal juftligi uchun; status (pending/sent/failed), error message.

**Dashboard UI:**
- CampaignListView: janvali (nomi, kanal, holat, sana, natija), filtr (kanal, holat).
- CampaignCreateView: forma (nomi, tavsif, kanal, shablon, teglar, sxemali vaqt).
- CampaignDetailView: log jadavali (pagination), success/fail statistika.
- Send button: holat draft → scheduled.

**Provider adapters (crm/providers/):**
- **SMSProvider (Eskiz.uz):** API credentials → send(customer, message_text).
- **EmailProvider:** Django email backend → send(customer, subject, message_text).
- **TelegramProvider:** `notifications.telegram.send_message` reuse.

**Send logic (ixtiyoriy):**
- Django management command yoki Celery task: scheduled campaigns → send all customers → log update.
- Template variable helper ({{first_name}}, {{full_name}}, {{phone}}) suggestion.

**Status:** Reja taqdim qilindi. Keyingi: User Eskiz credentials (email, password, SMS sender name, rate limit) → Campaign model + SMS provider yoziladi.



---

## 6. ⚠️ FOYDALANUVCHIDAN KERAK
- **Telegram bot token + admin chat ID** (sayt bildirishnomalari + kelajak marketing).
- **Eskiz.uz** login/parol (CRM SMS marketing — serverda test qilinadi).
- **Shahar nomi va NAP** (SEO va off-site listinglar uchun).

---

## 7. 🌍 Sayt tashqarisidagi SEO (kod emas)
**Google Business Profile**, **Yandex Business/Karta**, **2GIS** — uz/ru/en tavsif, foto,
ish vaqti, telefon bilan to'ldiring. Barcha platformada NAP bir xil bo'lsin.

---

**Ish tartibi:** har katta bosqich oxirida qisqa hisobot, keyin tasdiq bilan davom.
