"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),

    # Browsable API auth
    path('api-auth/', include('rest_framework.urls')),

    # Versioned API endpoints with proper version capture
    re_path(r'^api/(?P<version>(v1|v2))/', include('master_data.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/', include('djoser.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/', include('users.urls')),

    # API token authentication (versioned)
    # re_path(r'^api/(?P<version>(v1|v2))/token/$',
    #         TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # re_path(r'^api/(?P<version>(v1|v2))/token/refresh/$',
    #         TokenObtainPairView.as_view(), name="token_refresh"),

    # Admin and other endpoints
    path('admin/', admin.site.urls),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/',
         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/',
         SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve static files only during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
