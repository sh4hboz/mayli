# 🎨 WEBSITE CLEANUP & OPTIMIZATION (BOSQICH 1 YANGILASH)

> Mayli Restobar website'ni sayqallash, responsive design, va mobile experience takomillashlash

---

## 1. URL ROUTING O'ZGARISHLARI

### Qoldirilgan URL'lar (faqat 4 ta)
- `/` — Bosh sahifa
- `/about/` — Biz haqimizda
- `/privacy-policy/` — Maxfiylik siyosati
- `/terms-conditions/` — Foydalanish shartlari

### Olib tashlangan URL'lar
- `/order/`, `/order/create/`, `/order/status/` → olib tashlandi (delivery alohida loyiha sifatida keyin quriladi)
- `/menu/` → restobar app'da (menyu ko'rsatish)

**Fayl:** `website/urls.py`

---

## 2. HEADER TAKOMILLASHLASH

### Header Navigation
- ❌ "Yetkazib berish" link olib tashlandi
- ✅ Faqat "Biz haqimizda" linki qoldi

### Mobile (768px dan kichik)
- ✅ `.nav-right` (telefon, til switcher) `display: none`
- ✅ **Mobile Menu Drawer** qo'shildi:
  - **Joylashuv:** Fixed, o'ng taraf (300px width)
  - **Header:** Logo + X yopish button
  - **Ichida:** Navigation links + Home page sections
  - **Pastda:** Telefon va til almashtirgich
  - **Backdrop:** Semi-transparent yopish qismi
  - **Animation:** Smooth slide 0.3s

### Mobile Menu Sections
- Bosh sahifa
- Nega Mayli? (#why-us)
- Biz haqimizda (#about-home)
- Aksiyalar (#promotions)
- Galereya (#gallery)
- Sharhlar (#testimonials)
- Yangiliklar (#news)
- Batafsil (/about/)

**Fayllar:** 
- `templates/website/base.html` (HTML)
- `src/style.css` (CSS: `.mobile-menu-drawer`, `.mobile-menu-header`, `.mobile-lang-*`)
- `src/website.js` (JS: drawer toggle, close handlers)

---

## 3. FOOTER O'ZGARISHLARI

### Manzil
- ✅ `<p>` → `<a>` (Yandex Maps linkiga bog'landi)
- **URL:** `https://yandex.uz/maps/-/CPtG7YIO`

### Ijtimoiy Tarmoqlar
- ✅ Telegram @ MayliRestobar (SiteSettings'dan)
- ✅ Instagram @ maylirestobar (SiteSettings'dan)
- ✅ @ belgisiz text, faqat username ko'rinadi

### Ish Vaqti
- ✅ Barcha joyda **24/7** qilindi
  - `SiteSettings.working_hours` = "Har kuni: 24/7" (uz/ru/en)
  - JSON-LD SEO: `"openingHours": "Mo-Su 00:00-23:59"`
  - Management command: `set_working_hours_24_7`

**Fayllar:**
- `templates/website/base.html` (footer markup)
- `website/models.py` (SiteSettings)
- `website/management/commands/seed_site.py`
- `website/management/commands/set_working_hours_24_7.py`

---

## 4. DESIGN & STYLING

### CSS Variables
- ✅ `--gold: #ea6900` (primary orange bilan aligned)

### CSS Rules Cleanup
- ❌ `.nav-delivery { ... }` — order page uchun (olib tashlandi)
- ❌ `.nav-delivery:hover { ... }` (olib tashlandi)
- ❌ `.btn-outline:hover` color animatsiya (olib tashlandi)

### Layout Fixes
- ✅ `.swiper-slide` height: `auto` (content-based height)
- ✅ `.testimonial-card` height: `100%` (equal height cards)
- ✅ `.yandex-map-widget-container` → dark mode filter:
  ```css
  filter: invert(.9) hue-rotate(180deg) brightness(0.85);
  ```

**Fayl:** `src/style.css`

---

## 5. HOMEPAGE SECTIONS — ID VA LINKLAR

### Sections'larga ID Qo'shildi
| Section | ID | Link |
|---------|----|----|
| WHY US | `why-us` | `/#why-us` |
| ABOUT TEASER | `about-home` | `/#about-home` |
| PROMOTIONS | `promotions` | `/#promotions` |
| GALLERY | `gallery` | `/#gallery` (allaqachon bor) |
| TESTIMONIALS | `testimonials` | `/#testimonials` |
| LATEST NEWS | `news` | `/#news` (allaqachon bor) |

### Contact Section
- ❌ Olib tashlandi (desktop contact info)
- ✅ O'rniga: **Yandex xarita** (full width, 400px height)

**Fayl:** `templates/website/home.html`

---

## 6. GALLERY — SWIPER IMPLEMENTATION

### HTML Structure
- ❌ `.gallery-grid` (CSS grid) → ✅ `.gallery-swiper` (Swiper)
- ✅ Swiper structure: `.swiper-wrapper` > `.swiper-slide`

### Responsive Layout
| Breakpoint | Slides | Gap |
|------------|--------|-----|
| Mobile | 1.2 | 16px |
| 480px+ | 2 | 16px |
| 768px+ | 3 | 20px |
| 1024px+ | 4 | 20px |

### Autoplay
- ✅ **Delay:** 800ms (tez rotation)
- ✅ **Loop:** true
- ✅ Desktop va Mobile'da bir xil

**Fayllar:**
- `templates/website/home.html` (HTML)
- `src/style.css` (`.gallery-swiper` styles)
- `src/website.js` (Swiper initialization)

---

## 7. FILES MODIFIED

| Fayl | O'zgarish |
|------|-----------|
| `website/urls.py` | Order URL'lari olib tashlandi |
| `templates/website/base.html` | Header, footer, mobile drawer |
| `templates/website/home.html` | Sections ID, gallery swiper, contact map |
| `src/style.css` | CSS cleanup, mobile menu, gallery swiper |
| `src/website.js` | Mobile drawer toggle, gallery swiper |
| `website/management/commands/seed_site.py` | 24/7 ish vaqti |
| `website/management/commands/set_working_hours_24_7.py` | **Yangi** |

---

## 8. TEST CHECKLIST

- [ ] Mobile hamburger menu (< 768px) toggle qiladi
- [ ] Mobile drawer header'da logo + X button ko'rinadi
- [ ] Mobile drawer sections'lariga click bo'lsa yopiladi
- [ ] Gallery swiper autoplay 800ms'da (desktop va mobile)
- [ ] Footer'da manzil Yandex Maps'ga bog'langan
- [ ] Footer'da tel va ijtimoiy tarmoqlar ko'rinadi
- [ ] Ish vaqti barcha joyda "24/7" ko'rinadi
- [ ] Responsive: 375px, 768px, 1440px'larda test qilish

---

## 9. KELAJAK

- ✅ Admin dashboard (CMS) — tayyor
- 🔲 Mijozlar CRM (BOSQICH 3)
- 🔲 CRM marketing (SMS/email/Telegram)

---

**Status:** ✅ WEBSITE CLEANUP TUGALLANDI  
**Date:** 2026-06-13  
**Branch:** main
