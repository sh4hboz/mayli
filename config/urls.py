from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.sitemaps.views import sitemap
from website.sitemaps import StaticViewSitemap, NewsSitemap, DishSitemap
from website.robots_urls import llms_txt
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

sitemaps = {'static': StaticViewSitemap, 'news': NewsSitemap, 'dishes': DishSitemap}

urlpatterns = [
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
    path('llms.txt', llms_txt),

    # Telegram webhook (BOSQICH 0.7)
    path('', include('notifications.urls')),

    # Buyurtma API (tilsiz — savat/OTP/buyurtma yaratish)
    path('', include('orders.urls')),

    # Bron API (tilsiz — stol bo'shligi/OTP/bron yaratish)
    path('', include('reservations.urls')),
]

# Admin + dashboard + xodim auth — FAQAT dev'da (DASHBOARD_HOST bo'sh) shu apex
# urlconf'ida ochiladi. Prod'da DASHBOARD_HOST to'ldirilgan bo'lsa, ular ALOHIDA
# manage host urlconf'ida (config.urls_manage) bo'ladi — ommaviy domende butunlay
# yo'q (tabiiy 404). Host'ni HostSeparationMiddleware aniqlaydi.
if not settings.DASHBOARD_HOST:
    urlpatterns += [
        # Admin maxfiy yo'lda (ADMIN_URL).
        path(settings.ADMIN_URL, admin.site.urls),
        # Dashboard — dev'da /dashboard/ prefiksida.
        path('dashboard/', include('dashboard.urls')),
    ]

# Website (tilli) — / va /menu/ ni egallaydi
urlpatterns += i18n_patterns(
    path('', include('website.urls')),
    prefix_default_language=False,
)

if not settings.DASHBOARD_HOST:
    # Restobar (login, logout, xodimlar) — dev'da apex'da, oxirgi.
    urlpatterns += [
        path('', include('restobar.urls')),
    ]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Use staticfiles app for automatic static file serving
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns = staticfiles_urlpatterns() + urlpatterns
