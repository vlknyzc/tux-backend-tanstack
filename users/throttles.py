"""
Custom throttle classes for authentication endpoints.
Implements rate limiting to prevent brute force attacks and credential stuffing.
"""

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class AuthenticationThrottle(AnonRateThrottle):
    """
    Rate limiting for authentication endpoints.
    Limits login attempts to 5 per minute per IP address.
    """
    scope = 'auth'
    rate = '5/minute'


class TokenRefreshThrottle(AnonRateThrottle):
    """
    Rate limiting for token refresh endpoint.
    Limits token refresh to 10 per minute per IP address.
    """
    scope = 'token_refresh'
    rate = '10/minute'


class RegistrationThrottle(AnonRateThrottle):
    """
    Rate limiting for registration endpoint.
    Limits registration to 3 per hour per IP address.
    """
    scope = 'registration'
    rate = '3/hour'


class LoginAttemptThrottle(SimpleRateThrottle):
    """
    Advanced rate limiting by IP + email combination.
    Provides more granular control over login attempts per user.
    """
    scope = 'login_attempt'

    def get_cache_key(self, request, view):
        """
        Generate cache key based on IP address and email.
        This prevents attackers from trying multiple accounts from same IP.
        """
        if request.user.is_authenticated:
            return None  # Only throttle unauthenticated requests

        email = request.data.get('email', '')
        ip = self.get_ident(request)

        if not email:
            # Fallback to IP-only if no email provided
            return f'throttle_login_attempt_{ip}'

        return f'throttle_login_attempt_{ip}_{email}'


class InvitationValidationThrottle(AnonRateThrottle):
    """
    Rate limiting for invitation validation endpoint.
    Limits validation attempts to 10 per hour per IP address to prevent
    token enumeration attacks.
    """
    scope = 'invitation_validation'
    rate = '10/hour'
