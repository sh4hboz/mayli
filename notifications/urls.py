from django.urls import path

from . import views

# Telegram webhook — admin reply'larini qabul qiladi (chat ko'prigi).
# Secret URL'da: /telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>/
urlpatterns = [
    path('telegram/webhook/<secret>/', views.telegram_webhook, name='telegram_webhook'),
]
