from django.conf import settings
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,

)
from drf_spectacular.utils import extend_schema
from .serializers import LogoutResponseSerializer
from .throttles import AuthenticationThrottle, TokenRefreshThrottle, LoginAttemptThrottle

@extend_schema(tags=["Authentication"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint with rate limiting and failed attempt tracking.
    Implements security measures to prevent brute force attacks.
    """
    throttle_classes = [AuthenticationThrottle, LoginAttemptThrottle]

    def check_failed_attempts(self, email, ip_address):
        """
        Check if account should be locked due to too many failed attempts.
        Raises ValidationError if account is locked.
        """
        if not email:
            return 0

        # Track failed attempts per email
        email_key = f'failed_login_{email}'
        # Track failed attempts per IP
        ip_key = f'failed_login_ip_{ip_address}'

        email_attempts = cache.get(email_key, 0)
        ip_attempts = cache.get(ip_key, 0)

        # Lock account after 5 failed attempts (15 minute lockout)
        if email_attempts >= 5:
            raise ValidationError({
                'detail': 'Account temporarily locked due to too many failed login attempts. Please try again in 15 minutes.'
            })

        # Also check IP-based lockout (prevent distributed attacks)
        if ip_attempts >= 10:
            raise ValidationError({
                'detail': 'Too many failed login attempts from this IP address. Please try again later.'
            })

        return email_attempts

    def increment_failed_attempts(self, email, ip_address):
        """Increment failed login attempt counters."""
        if email:
            email_key = f'failed_login_{email}'
            attempts = cache.get(email_key, 0) + 1
            cache.set(email_key, attempts, timeout=900)  # 15 minute lockout

        ip_key = f'failed_login_ip_{ip_address}'
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, timeout=3600)  # 1 hour IP lockout

    def clear_failed_attempts(self, email, ip_address):
        """Clear failed login attempt counters on successful login."""
        if email:
            email_key = f'failed_login_{email}'
            cache.delete(email_key)

        ip_key = f'failed_login_ip_{ip_address}'
        cache.delete(ip_key)

    def post(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        security_logger = logging.getLogger('security')

        email = request.data.get('email', 'unknown')
        ip_address = self.get_client_ip(request)

        try:
            # Check for account lockout before attempting authentication
            self.check_failed_attempts(email, ip_address)

            logger.info(f"JWT login attempt for: {email}")

            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                logger.info(f"JWT authentication successful for: {email}")
                security_logger.info(
                    f"Successful login: email={email}, ip={ip_address}"
                )

                # Clear failed attempts on successful login
                self.clear_failed_attempts(email, ip_address)

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
                logger.warning(f"JWT authentication failed with status {response.status_code} for: {email}")
                security_logger.warning(
                    f"Failed login attempt: email={email}, ip={ip_address}, status={response.status_code}"
                )

                # Increment failed attempts on authentication failure
                self.increment_failed_attempts(email, ip_address)

            return response

        except ValidationError:
            # Re-raise validation errors (account lockout messages)
            raise
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            logger.error(f"Request data keys: {list(request.data.keys()) if hasattr(request, 'data') else 'No data'}")
            security_logger.error(
                f"Login error: email={email}, ip={ip_address}, error={str(e)}"
            )

            # Increment failed attempts on exceptions
            self.increment_failed_attempts(email, ip_address)

            # Re-raise the exception to maintain normal error handling
            raise

    def get_client_ip(self, request):
        """Get client IP address from request, considering proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@extend_schema(tags=["Authentication"])
class CustomTokenRefreshView(TokenRefreshView):
    """
    Token refresh endpoint with rate limiting.
    Limits refresh token requests to prevent abuse.
    """
    throttle_classes = [TokenRefreshThrottle]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            # Create a mutable copy of request.data if needed
            if hasattr(request.data, '_mutable'):
                request.data._mutable = True
            request.data['refresh'] = refresh_token
            if hasattr(request.data, '_mutable'):
                request.data._mutable = False

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
@permission_classes([IsAdminUser])  # SECURITY: Restricted to admin users only
def debug_auth_status(request):
    """
    Debug endpoint to check authentication system status.

    SECURITY:
    - Restricted to admin users only
    - Disabled in production
    - Minimal information exposure
    """
    import logging

    logger = logging.getLogger(__name__)

    # SECURITY: Disable in production
    if not settings.DEBUG:
        logger.warning(
            f"Debug endpoint access attempt in production by user {request.user.email}"
        )
        return Response(
            {'error': 'Not available in production'},
            status=status.HTTP_404_NOT_FOUND
        )

    logger.info(f"Debug auth status endpoint accessed by admin: {request.user.email}")

    try:
        # Minimal information exposure - only essential debug info
        return Response({
            'status': 'ok',
            'auth_system': 'ready',
            'message': 'Authentication system is operational'
        })

    except Exception as e:
        logger.error(f"Debug auth status error: {str(e)}")
        return Response({
            'status': 'error',
            'auth_system': 'failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
