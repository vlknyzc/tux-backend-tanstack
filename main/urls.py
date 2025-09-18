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
import os


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


@csrf_exempt
@never_cache  
@transaction.non_atomic_requests
def debug_django_status(request):
    """Minimal Django diagnostic endpoint."""
    try:
        # Test basic Django functionality
        from django.conf import settings
        
        # Get basic info without database access
        debug_info = {
            'django_ready': True,
            'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown'),
            'debug_mode': getattr(settings, 'DEBUG', 'unknown'),
            'secret_key_set': bool(getattr(settings, 'SECRET_KEY', None)),
            'allowed_hosts_count': len(getattr(settings, 'ALLOWED_HOSTS', [])),
        }
        
        # Try to import critical modules
        try:
            from users.models import UserAccount
            debug_info['user_model'] = 'OK'
        except Exception as e:
            debug_info['user_model'] = f'ERROR: {str(e)}'
        
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            debug_info['jwt_import'] = 'OK'
        except Exception as e:
            debug_info['jwt_import'] = f'ERROR: {str(e)}'
        
        # Return as plain text to avoid JSON serialization issues
        content = '\n'.join([f'{k}: {v}' for k, v in debug_info.items()])
        
        return HttpResponse(
            content=content,
            status=200,
            content_type='text/plain'
        )
        
    except Exception as e:
        # Catch any error and return it as plain text
        error_content = f'DJANGO_ERROR: {str(e)}\nTRACEBACK: {str(e.__class__.__name__)}'
        
        return HttpResponse(
            content=error_content,
            status=500,
            content_type='text/plain'
        )


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('health/', health_check_endpoint, name='health_check'),  # Railway health check endpoint
    path('debug-status/', debug_django_status, name='debug_status'),  # Django diagnostic endpoint

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

# Serve static files
if settings.DEBUG:
    # Development: serve static files directly
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
else:
    # Production: WhiteNoise will handle static files
    # But we can also add a fallback pattern for admin static files
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
