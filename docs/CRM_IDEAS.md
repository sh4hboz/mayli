# 💡 CRM g'oyalari — menejer bilan muhokama uchun

> Bu fayl **kelajak rejalari** ro'yxati. Hozir qurilmaydi — menejer bilan kelishilgach,
> ustuvorlik bo'yicha bosqichma-bosqich qilinadi.
>
> ⚠️ Ko'p g'oyalar **buyurtma (orders) va to'lov (payments)** ma'lumotlariga bog'liq —
> ular hozir loyihada yo'q. Shuningdek ba'zilari uchun **Eskiz / Telegram bot access** kerak.

---

## A. Avtomatik xabarlar
| # | G'oya | Nima kerak | Murakkablik |
|---|---|---|---|
| 1 | 🎂 **Tug'ilgan kun tabrigi** — avtomatik tabrik + sovg'a/promo-kod | Kunlik cron, Eskiz/Telegram | O'rta |
| 2 | 📣 **Aksiya/yangilik avto-tarqatish** — yangi Promotion/News chiqqanda rozilik berganlarga | Signal/cron, kanal access | O'rta |
| 3 | 💤 **"Sog'indik" (win-back)** — N kun tashrif qilmaganlarga qaytarish taklifi | **Tashrif/buyurtma tarixi**, cron | Yuqori |
| 4 | 🎉 **Bayram tabriklari** — Navro'z, Yangi yil, Hayit, 8-mart, Mustaqillik | Rejalashtirilgan kampaniya | Past |
| 5 | 👋 **Xush kelibsiz** — yangi mijozga birinchi rahmat xabari | Signal (Customer create) | Past |

## B. Sodiqlik (loyalty)
| # | G'oya | Nima kerak | Murakkablik |
|---|---|---|---|
| 6 | ⭐ **Bonus/ball tizimi** — har tashrif/buyurtma uchun ball | **Buyurtma/to'lov tizimi** | Yuqori |
| 7 | 🏅 **Darajalar (VIP/Gold/Silver)** — tashrif soni bo'yicha avtomatik teglash | **Tashrif tarixi** | O'rta |
| 8 | 🎟 **Shaxsiy promo-kodlar** — har mijozga unikal, kuzatiladigan kod | Promo-kod modeli | O'rta |
| 9 | 🤝 **Do'st taklif qilish (referral)** — mukofot (`source=referral` bor) | Referral hisobi | O'rta |

## C. Bron va tashrif
| # | G'oya | Nima kerak | Murakkablik |
|---|---|---|---|
| 10 | 📅 **Bron (Reservation) tizimi** — sana/vaqt/mehmonlar; har bron avtomatik Customer yaratadi | Yangi model | O'rta |
| 11 | ⏰ **Bron eslatma/tasdiqlash** — bron oldidan SMS/Telegram | Reservation + cron + Eskiz | O'rta |

> Hozircha bron = **ContactMessage** (sodda murojaat). Keyin to'liq Reservation modeliga o'tkazish mumkin.

## D. Feedback va reputatsiya (SEO uchun muhim)
| # | G'oya | Nima kerak | Murakkablik |
|---|---|---|---|
| 12 | 🌟 **Tashrifdan keyin sharh so'rash** — ijobiy → Google/Yandex sharhi (SEO 1-o'rin), salbiy → ichki ogohlantirish | Tashrif tarixi, cron | O'rta |

## E. Segmentatsiya va analitika
| # | G'oya | Nima kerak | Murakkablik |
|---|---|---|---|
| 13 | 🏷 **Avtomatik teglar** — "doimiy", "yangi", "uxlagan" qoidalari | Tashrif tarixi | O'rta |
| 14 | 📊 **Dashboard analitika** — oylik yangi mijoz, manba taqsimoti, kampaniya samarasi, shu oydagi tug'ilganlar | Faqat kod | Past |
| 15 | 🤖 **Telegram bot orqali o'zini ro'yxatga olish** — `telegram_user_id` avtomatik yig'iladi | Telegram bot access | O'rta |

## F. Texnik asos (yuqoridagilar uchun bazaviy)
- **Cron yoki Celery** — kunlik avtomatik vazifalar (tug'ilgan kun, win-back, sharh so'rash).
- **Eskiz.uz real integratsiyasi** — haqiqiy SMS (hozir stub).
- **Tashrif/buyurtma tarixi** — loyalty, win-back, sharhlarning aksariyati shunga tayanadi.

---

## Tavsiya etilgan bosqichlar (access kelganda)
1. **Tez g'alabalar (kod yetarli):** #4 bayram tabriklari, #5 xush kelibsiz, #14 dashboard analitika.
2. **O'rta:** #1 tug'ilgan kun, #2 aksiya avto-tarqatish, #8 promo-kod, #10 bron modeli.
3. **Buyurtma/to'lov kelgach:** #3 win-back, #6 loyalty ballari, #7 darajalar, #12 sharh so'rash.
