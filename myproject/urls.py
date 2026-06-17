"""
URL configuration for myproject project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('management.urls')),
]

urlpatterns += [
    path('', serve, {'path': 'dist/index.html', 'document_root': settings.STATICFILES_DIRS[0]}),
    path('<path:path>', serve, {'path': 'dist/index.html', 'document_root': settings.STATICFILES_DIRS[0]}),
]