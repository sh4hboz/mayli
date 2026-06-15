# Mayli Restobar — Production deploy (nginx + gunicorn)

Bu papkada productionga deploy qilish uchun konfiguratsiya fayllari:

| Fayl | Vazifasi |
|------|----------|
| `gunicorn.service` | systemd xizmati — gunicorn WSGI serverini ishga tushiradi |
| `nginx-maylirestobar.conf` | nginx server block — HTTPS + statik fayllar + gunicorn proxy |
| `env.prod.example` | Production `.env` namunasi |

**Arxitektura:** `nginx (443, SSL) → unix socket → gunicorn → Django (config.wsgi)`.
WebSocket ishlatilmaydi, shuning uchun WSGI (gunicorn) yetarli.

> Quyidagi yo'llar `/var/www/mayli` va foydalanuvchi `www-data` deb olingan.
> O'zingiznikiga moslang.

---

## 1. Server tayyorgarligi (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git
# Ixtiyoriy (prod.py cache/channels Redis'ga ishora qiladi):
sudo apt install -y redis-server
# Postgres ishlatsangiz:
# sudo apt install -y postgresql libpq-dev
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
- https://maylirestobar.uz/login/ — xodimlar kirishi
- https://maylirestobar.uz/dashboard/ — login keyin boshqaruv paneli

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

## Telegram webhook (kerak bo'lsa)

```bash
python manage.py set_webhook https://maylirestobar.uz
```
