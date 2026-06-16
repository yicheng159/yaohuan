"""
URL configuration for myproject project.
"""
from django.contrib import admin
from django.urls import path, re_path, include
from .views import index
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('management.urls')),
    re_path(r'^(?!admin/|api/).*$', index, name='vue-route'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)