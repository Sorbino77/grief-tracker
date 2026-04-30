from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from config.views import DashboardView, HomeView, PrivacyView

urlpatterns = [
    # Public pages
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),

    # Admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/grief/", include("apps.grief.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/imports/", include("apps.imports.urls")),

    # API Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
