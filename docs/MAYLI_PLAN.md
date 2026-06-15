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

## 5. BOSQICH 5 — CRM marketing (🔄 send logic tayyor)

**Maqsad:** SMS/email/Telegram orqali mass marketing kampaniyalarini jo'natish tizimi.

**Tayyor qilingan:**
✅ **Modellar:** Campaign, CampaignLog (migrations applied)
✅ **Admin paneli:** Campaign CRUD + inline logs
✅ **Dashboard UI:** CampaignListView, CreateView, DetailView, UpdateView, DeleteView
  - Campaign listini ko'rish (filtr: kanal, holat)
  - Kampaniya yaratish/tahrirlash (shablon, taglar, sxemali vaqt)
  - Detail view → log jadval (har customer'ning jo'natish holati)

✅ **Provider adapters (crm/providers.py):**
- **SMSProvider (Eskiz.uz):** Stub (keyingi: Eskiz API integration)
- **EmailProvider:** Django email backend ishlatadi
- **TelegramProvider:** `notifications.telegram` orqali
- **render_template():** {{first_name}}, {{full_name}}, {{phone}} almashtirish

✅ **Send logic (crm/services.py):**
- **CampaignSendService.send_campaign():** Kampaniyani barcha target mijozlarga jo'natish
- Mijozlarni filtrlash: tags + kanal + consent
- Log yaratish har customer uchun (success/failed + error message)
- Campaign statistika yangilash (sent_count, failed_count, status=SENT)

✅ **Management command (crm/management/commands/send_campaigns.py):**
```bash
# Barcha rejalashtirylgan kampaniyalarni jo'natish
python manage.py send_campaigns

# Bitta kampaniyani jo'natish (by ID)
python manage.py send_campaigns 1

# Test jo'natish (bitta mijozga)
python manage.py send_campaigns 1 --test
python manage.py send_campaigns 1 --test --customer-id 5
```

**Keyingi:**
🔜 **Eskiz.uz SMS integration:** ESKIZ_EMAIL, ESKIZ_PASSWORD (Eskiz API)
🔜 **Celery task:** scheduled campaigns automatik jo'natish (yoki cron job)
🔜 **Dashboard "Send" button:** Draft → Scheduled holat o'zgartirish



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
