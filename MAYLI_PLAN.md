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
| **3** | **Mijozlar CRM** — Customer modeli + dashboard CRUD + qidiruv/segmentlash | 🔥 |
| 4 | CRM marketing — kampaniya tizimi (auditoriya, SMS/email/Telegram, jadval) | rejada |
| — | Delivery & Take away — **alohida katta loyiha** | rejada |

---

## 4. BOSQICH 3 — Mijozlar CRM (hozirgi ish)

**Maqsad:** dashboardda mijozlar bilan ishlash uchun to'liq tizim va backend.

- **`Customer` modeli** (yangi `crm` app): ism\*, familiya, telefon\*, tug'ilgan kun, jins
  (keyin: email, telegram, kanal bo'yicha rozilik). `accounts.User`'ga ixtiyoriy bog'lanadi.
  Xodim qo'lda qo'shgan, hali ro'yxatdan o'tmagan mijozlarni ham saqlaydi.
- **Dashboard CRUD:** ro'yxat (qidiruv + filtr/segment: tug'ilgan oy, jins, sana, teg),
  qo'shish / tahrirlash / o'chirish / batafsil.
- **Django admin** ro'yxatdan o'tkazish.
- 🔴 CSS/JS qoidasi: inline `style=""` / `onclick=""` YO'Q.
- **Mavjud pattern**: `dashboard` app'dagi `CMSBaseMixin`, `SuccessMessageMixin`,
  `BootstrapModelForm` va News/Dish CRUD namunasidan foydalan.

---

## 5. BOSQICH 4 — CRM marketing (kelajak)

- **Campaign** modeli + dashboard UI: auditoriya tanlash (segment), kanal (SMS/email/Telegram), matn, jadval.
- Provider-adapter: **Eskiz.uz** (SMS), email, Telegram (`notifications.telegram`).
- Yuborish loglari, statistika. (Loyiha serverda ishga tushgach SMS real test qilinadi.)
- Tug'ilgan kun tabrigi, promo kod, segment bo'yicha avtomatik jo'natmalar.

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
