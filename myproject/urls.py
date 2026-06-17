"""
URL configuration for myproject project.
"""
from django.contrib import admin
from django.urls import path, include
from management.views import serve_frontend

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('management.urls')),
]

urlpatterns += [
    path('', serve_frontend),
    path('<path:path>', serve_frontend),
]