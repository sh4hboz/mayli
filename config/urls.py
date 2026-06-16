from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.sitemaps.views import sitemap
from website.sitemaps import StaticViewSitemap
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

sitemaps = {'static': StaticViewSitemap}

urlpatterns = [
    # Admin URL .env (ADMIN_URL) orqali maxfiy yo'lga ko'chirilishi mumkin.
    path(settings.ADMIN_URL, admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('careers/', RedirectView.as_view(url='/contact/', permanent=True)),

    # DRF + Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT auth (BOSQICH 0.5)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', include('website.robots_urls')),

    # Telegram webhook (BOSQICH 0.7)
    path('', include('notifications.urls')),
]

# Website (tilli) — BIRINCHI, / va /menu/ ni egallaydi
urlpatterns += i18n_patterns(
    path('', include('website.urls')),
    prefix_default_language=False,
)

# Dashboard app (chat va kelajakdagi panel sahifalari)
urlpatterns += [
    path('dashboard/', include('dashboard.urls')),
]

# Restobar — oxirgi (login, dashboard asosiy, profile, call-waiter va h.k.)
urlpatterns += [
    path('', include('restobar.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Use staticfiles app for automatic static file serving
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns = staticfiles_urlpatterns() + urlpatterns
