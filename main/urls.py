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
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.db import transaction
import json
import datetime


def get_spectacular_views():
    """Lazy import for spectacular views to avoid circular imports."""
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
    return SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


@csrf_exempt
@never_cache
@transaction.non_atomic_requests
def health_check_endpoint(request):
    """Ultra-simple health check endpoint for Railway - no database dependency."""
    # Return plain text response to avoid any potential JSON/middleware issues
    response = HttpResponse(
        content='OK',
        status=200,
        content_type='text/plain'
    )
    # Ensure health check bypasses SSL redirect and caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Health-Check'] = 'railway'
    return response


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('health/', health_check_endpoint, name='health_check'),  # Railway health check endpoint

    # Browsable API auth
    path('api-auth/', include('rest_framework.urls')),

    # Versioned API endpoints with proper version capture
    re_path(r'^api/(?P<version>(v1|v2))/', include('master_data.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/', include('djoser.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/', include('users.urls')),

    # Admin and other endpoints
    path('admin/', admin.site.urls),
]

# Add API documentation patterns with lazy imports
SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView = get_spectacular_views()
urlpatterns += [
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
