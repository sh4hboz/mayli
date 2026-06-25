# Mayli Restobar — Production deploy (nginx + gunicorn)

Bu papkada productionga deploy qilish uchun konfiguratsiya fayllari:

| Fayl | Vazifasi |
|------|----------|
| `gunicorn.service` | systemd xizmati — gunicorn WSGI serverini ishga tushiradi |
| `nginx-maylirestobar.conf` | nginx server block — HTTPS + statik fayllar + gunicorn proxy |
| `env.prod.example` | Production `.env` namunasi |
| `mayli-campaigns.{service,timer}` | Rejalashtirilgan kampaniyalarni har 5 daqiqada yuboradi |
| `mayli-birthday.{service,timer}` | Tug'ilgan kun SMS tabriklarini har kuni ertalab yuboradi |

**Arxitektura:** `nginx (443, SSL) → unix socket → gunicorn → Django (config.wsgi)`.
WebSocket ishlatilmaydi, shuning uchun WSGI (gunicorn) yetarli.

**Maqsadli server:** Ubuntu 24.04, 6 CPU, 12 GB RAM, 100 GB NVMe.
gunicorn 9 worker'ga sozlangan (`deploy/gunicorn.service`). Ma'lumotlar
bazasi sifatida **PostgreSQL** tavsiya etiladi (bu server quvvatiga mos).

> Quyidagi yo'llar `/var/www/mayli` va foydalanuvchi `www-data` deb olingan.
> O'zingiznikiga moslang.

---

## 1. Server tayyorgarligi (Ubuntu 24.04)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip python3-dev build-essential \
                    nginx git redis-server \
                    postgresql libpq-dev
```

Ubuntu 24.04 Python 3.12 bilan keladi (Django 5.1 to'liq qo'llab-quvvatlaydi).

Firewall (ochiq portlar — SSH, HTTP, HTTPS):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### PostgreSQL bazasini yaratish (tavsiya)

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE mayli;
CREATE USER mayli WITH PASSWORD 'KUCHLI_PAROL';
ALTER ROLE mayli SET client_encoding TO 'utf8';
ALTER ROLE mayli SET default_transaction_isolation TO 'read committed';
ALTER ROLE mayli SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE mayli TO mayli;
\c mayli
GRANT ALL ON SCHEMA public TO mayli;
SQL
```

So'ng `.env` da:
```
DATABASE_URL=postgres://mayli:KUCHLI_PAROL@127.0.0.1:5432/mayli
```

## 2. Kodni olish va virtual muhit

```bash
sudo mkdir -p /var/www/mayli
sudo chown $USER:$USER /var/www/mayli
git clone https://github.com/sh4hboz/mayli.git /var/www/mayli
cd /var/www/mayli
git checkout feature/marketing-crm   # yoki main (merge qilingach)

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. `.env` sozlash

```bash
cp deploy/env.prod.example .env
nano .env   # SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL va h.k. to'ldiring
```

Kuchli `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## 4. Django tayyorlash

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate
python manage.py collectstatic --noinput     # src/ + static/ -> staticfiles/
python manage.py compilemessages             # tarjimalar (.po -> .mo)
python manage.py createsuperuser             # birinchi admin
python manage.py check --deploy              # xavfsizlik tekshiruvi
```

## 5. gunicorn (systemd)

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
# Fayl ichidagi yo'l/foydalanuvchini tekshiring:
sudo nano /etc/systemd/system/gunicorn.service

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl status gunicorn          # active (running) bo'lishi kerak
ls -l /run/gunicorn/mayli.sock          # socket yaratilganini tekshiring
```

Fayl ruxsatlari: `www-data` ham loyihani o'qiy olishi kerak:
```bash
sudo chown -R www-data:www-data /var/www/mayli
```

## 6. nginx

Hozir `coming-soon.html` ko'rsatayotgan eski konfiguratsiyani almashtiring:

```bash
sudo cp deploy/nginx-maylirestobar.conf /etc/nginx/sites-available/maylirestobar.uz
sudo ln -sf /etc/nginx/sites-available/maylirestobar.uz /etc/nginx/sites-enabled/maylirestobar.uz
# Eski coming-soon konfiguratsiyasini o'chiring (agar alohida fayl bo'lsa):
# sudo rm /etc/nginx/sites-enabled/<eski-config>

sudo nginx -t            # sintaksis tekshiruvi
sudo systemctl reload nginx
```

> SSL sertifikat yo'llari certbot standartida (`/etc/letsencrypt/live/maylirestobar.uz/`).
> Agar boshqacha bo'lsa, konfiguratsiyadagi `ssl_certificate*` yo'llarini moslang.

## 7. Tekshirish

- https://maylirestobar.uz — sayt ochilishi kerak
- https://maylirestobar.uz/static/src/style.css — 200 qaytishi kerak (statik)
- https://maylirestobar.uz/dashboard/ — **404** bo'lishi kerak (dashboard ommaviy domende yashirin)
- https://manage.maylirestobar.uz/ — login keyin boshqaruv paneli (dashboard ILDIZDA, `/dashboard/` yo'q)
- https://manage.maylirestobar.uz/login/ — xodimlar kirishi
- https://manage.maylirestobar.uz/<ADMIN_URL> — Django admin (maxfiy yo'l)

Loglar:
```bash
sudo journalctl -u gunicorn -f          # gunicorn loglari
sudo tail -f /var/log/nginx/error.log   # nginx xatolari
```

---

## Yangilanish (keyingi deploy)

```bash
cd /var/www/mayli
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages
sudo systemctl restart gunicorn
```

> Menyu kategoriyalari va custom CSS fayllari (`media/css/`) endi **data migration**
> orqali bir marta seed qilinadi (`menu.0006`, `website.0015`) — ya'ni `migrate`
> ularni avtomatik bajaradi. Har deploy'da `init_custom_css` / `sync_menu_categories`
> ni alohida yurgizish **kerak emas**. Qayta seed kerak bo'lsa, qo'lda:
> `python manage.py sync_menu_categories` yoki `python manage.py init_custom_css --force`.

## Telegram webhook (kerak bo'lsa)

```bash
python manage.py set_webhook https://maylirestobar.uz
```

## Avtomatlashtirish — systemd timer'lar (kampaniya + tug'ilgan kun)

Ikki davriy vazifa systemd timer orqali ishlaydi (alohida cron kerak emas):
- **kampaniya yuborish** — har 5 daqiqada `send_campaigns` (rejalashtirilgan, vaqti kelganlarini yuboradi);
- **tug'ilgan kun tabriklari** — har kuni 09:00 da `send_birthday_greetings`.

```bash
sudo cp deploy/mayli-campaigns.service /etc/systemd/system/
sudo cp deploy/mayli-campaigns.timer   /etc/systemd/system/
sudo cp deploy/mayli-birthday.service  /etc/systemd/system/
sudo cp deploy/mayli-birthday.timer    /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now mayli-campaigns.timer mayli-birthday.timer

systemctl list-timers 'mayli-*'        # keyingi ishga tushish vaqtini ko'rsatadi
```

> ⚠️ Tug'ilgan kun timer'i mahalliy vaqtga bog'liq — server vaqt mintaqasi
> `Asia/Tashkent` ekanini tekshiring: `timedatectl set-timezone Asia/Tashkent`.
> SMS chinakam yuborilishi uchun `.env` da `TEXTUP_*` + tegishli template ID
> (`BIRTHDAY_SMS_TEMPLATE_ID`) sozlangan bo'lishi kerak; aks holda yuborish
> xato qaytaradi, lekin timer xavfsiz ishlayveradi.

Qo'lda sinash:
```bash
python manage.py send_birthday_greetings --dry-run   # bugun kim tabriklanadi
python manage.py send_campaigns                       # rejalashtirilganlarni darhol
```
