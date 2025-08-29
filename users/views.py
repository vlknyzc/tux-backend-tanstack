from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,

)
from drf_spectacular.utils import extend_schema
from .serializers import LogoutResponseSerializer

@extend_schema(tags=["Authentication"])
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"JWT login attempt for: {request.data.get('email', 'no email provided')}")
            
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                logger.info("JWT authentication successful")
                access_token = response.data["access"]
                refresh_token = response.data["refresh"]

                response.set_cookie(
                    'access',
                    access_token,
                    max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                    path=settings.AUTH_COOKIE_PATH,
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,

                )

                response.set_cookie(
                    'refresh',
                    refresh_token,
                    max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGE,
                    path=settings.AUTH_COOKIE_PATH,
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,
                )
            else:
                logger.warning(f"JWT authentication failed with status {response.status_code}")
                logger.warning(f"Response data: {response.data}")

            return response
            
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            logger.error(f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}")
            
            # Re-raise the exception to maintain normal error handling
            raise

@extend_schema(tags=["Authentication"])
class CustomTokenRefreshView(TokenRefreshView):
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data["access"]

            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response

@extend_schema(tags=["Authentication"])
class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get('access')

        if access_token:
            request.data['token'] = access_token

        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Authentication"])
class LogoutView(APIView):
    serializer_class = LogoutResponseSerializer

    
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access')
        response.delete_cookie('refresh')

        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth_status(request):
    """Debug endpoint to check authentication system status."""
    import logging
    from django.contrib.auth import get_user_model
    
    logger = logging.getLogger(__name__)
    logger.info("Debug auth status endpoint called")
    
    try:
        User = get_user_model()
        user_count = User.objects.count()
        
        # Test JWT token generation
        from rest_framework_simplejwt.tokens import RefreshToken
        
        if user_count > 0:
            sample_user = User.objects.first()
            try:
                refresh = RefreshToken.for_user(sample_user)
                access = refresh.access_token
                jwt_test = "✅ JWT generation works"
            except Exception as jwt_error:
                jwt_test = f"❌ JWT generation failed: {str(jwt_error)}"
        else:
            jwt_test = "⚠️ No users available for JWT test"
        
        return Response({
            'status': 'ok',
            'auth_system': 'ready',
            'user_count': user_count,
            'jwt_test': jwt_test,
            'user_model': str(User),
            'secret_key_length': len(settings.SECRET_KEY) if hasattr(settings, 'SECRET_KEY') else 0,
        })
        
    except Exception as e:
        logger.error(f"Debug auth status error: {str(e)}")
        return Response({
            'status': 'error',
            'error': str(e),
            'auth_system': 'failed'
        }, status=500)
