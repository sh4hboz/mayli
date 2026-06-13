# Mayli Restobar — Git'ga Yuklash Kerak Fayllar

## 📁 Django Proyekti Struktura (TRACK)

### Core Django Files
- `manage.py` — Django management script
- `requirements.txt` — Python dependencies
- `requirements-dev.txt` — Development dependencies
- `setup.py` — Project setup file (agar bor bo'lsa)
- `.env.example` — Environment variables template

### Django App Directories
```
accounts/          — User authentication
- migrations/      ✅ TRACK (DB schema history)
- models.py
- views.py
- urls.py
- forms.py
- admin.py
- apps.py
- tests.py

core/              — Core utilities
- migrations/      ✅ TRACK
- models.py
- etc.

dashboard/         — Admin dashboard
- migrations/      ✅ TRACK
- templates/       ✅ TRACK
- models.py
- views.py
- etc.

menu/              — Menu/dishes management
- migrations/      ✅ TRACK
- models.py
- views.py
- etc.

crm/               — Mijozlar CRM (quriladi)
- migrations/      ✅ TRACK
- models.py
- etc.

website/           — Public website
- migrations/      ✅ TRACK
- models.py
- views.py
- urls.py
- etc.
```

### Templates
```
templates/
├── base.html                    ✅ TRACK
├── website/
│   ├── base.html               ✅ TRACK
│   ├── home.html               ✅ TRACK
│   ├── about.html              ✅ TRACK
│   ├── menu.html               ✅ TRACK
│   ├── privacy_policy.html      ✅ TRACK
│   ├── terms_conditions.html    ✅ TRACK
│   ├── partials/
│   │   ├── _header.html        ✅ TRACK
│   │   ├── _footer.html        ✅ TRACK
│   │   ├── _hero.html          ✅ TRACK
│   │   ├── _floating_buttons.html ✅ TRACK
│   │   ├── _contact.html       ✅ TRACK
│   │   ├── _gallery.html       ✅ TRACK
│   │   ├── _map.html           ✅ TRACK
│   │   ├── _news.html          ✅ TRACK
│   │   ├── _promotions.html    ✅ TRACK
│   │   ├── _testimonials.html  ✅ TRACK
│   │   ├── _vacancies.html     ✅ TRACK
│   │   └── _chat_widget.html   ✅ TRACK
│   └── ...
├── management/                 ✅ TRACK (admin templates)
└── ...
```

### Static Files (Source Code)
```
static/
├── assets/                      ✅ TRACK
│   ├── css/
│   │   ├── app.min.css         ✅ TRACK
│   │   └── custom-management.css ✅ TRACK
│   ├── js/
│   │   ├── app.js              ✅ TRACK
│   │   ├── custom-management.js ✅ TRACK
│   │   └── order.js            ✅ TRACK
│   ├── images/                 ✅ TRACK
│   ├── fonts/                  ✅ TRACK
│   └── plugins/                ✅ TRACK
└── (src files — custom CSS/JS) ✅ TRACK (when created)
```

### Configuration
```
config/
├── settings.py                 ✅ TRACK
├── urls.py                     ✅ TRACK
├── wsgi.py                     ✅ TRACK
├── asgi.py                     ✅ TRACK
└── settings/
    ├── base.py                 ✅ TRACK
    ├── local.py                ❌ DON'T TRACK (use .env)
    └── production.py           ✅ TRACK
```

### Locale & i18n
```
locale/                         ✅ TRACK
├── uz/
│   └── LC_MESSAGES/
│       ├── django.po           ✅ TRACK
│       └── django.mo           ❌ (generated)
├── ru/
├── en/
└── ...
```

### Documentation & Config
- `README.md`                    ✅ TRACK
- `CLAUDE.md`                    ✅ TRACK
- `.gitignore`                   ✅ TRACK
- `.env.example`                 ✅ TRACK
- `docker-compose.yml`           ✅ TRACK (if used)
- `Dockerfile`                   ✅ TRACK (if used)
- `manage.py`                    ✅ TRACK

### Media Folder
```
media/                           ❌ DON'T TRACK
├── uploads/
├── gallery/
└── ...
(Use .gitignore: /media/)
```

## ❌ DON'T TRACK (Already in .gitignore)

```
venv/                   — Virtual environment
staticfiles/            — Compiled static files
src/                    — Generated source
__pycache__/            — Python cache
*.pyc, *.pyo           — Compiled Python
.env                    — Environment variables
.env.local             — Local env overrides
db.sqlite3             — Local database
.vscode/               — IDE settings
.idea/                 — IDE settings
node_modules/          — Node packages (if frontend build)
*.log                  — Log files
.coverage              — Test coverage
htmlcov/               — Coverage reports
.pytest_cache/         — Pytest cache
dist/, build/          — Build artifacts
```

## 📋 Summary

### ✅ DO COMMIT TO GIT
- All Django app code (models, views, forms, urls, admin)
- All migration files (migrations/)
- All templates (HTML)
- All static source files (CSS, JS in assets/)
- Configuration files (settings, urls, wsgi, asgi)
- Locale/translation files (.po files)
- Documentation (README, CLAUDE.md)
- requirements.txt
- .gitignore
- .env.example

### ❌ DO NOT COMMIT
- Virtual environment (/venv)
- Compiled static files (/staticfiles)
- Generated source files (/src if compiled)
- Database files (db.sqlite3)
- Media uploads (/media)
- .env (use .env.example)
- IDE/editor configs (.vscode, .idea)
- Python cache (__pycache__, *.pyc)
- Log files
- Test coverage reports
