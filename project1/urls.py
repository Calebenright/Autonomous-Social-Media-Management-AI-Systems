from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler500, handler404
from dashboard.views import error500, error404
from django.contrib import sitemaps
from django.contrib.sitemaps.views import sitemap
from app1.sitemaps import StaticViewSitemap, FirebaseArticleSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'articles': FirebaseArticleSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("", include("app1.urls")),
    path("", include('dashboard.urls')),
    path("", include('admin_panel.urls')),
    path("", include('funnel.urls')),
    path("", include('service.urls')),
    path("", include('agency_panel.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler500 = error500
handler404 = error404