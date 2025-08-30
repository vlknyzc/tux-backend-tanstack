from django.conf import settings
from rest_framework.authentication import BaseAuthentication

# Import JWT authentication with error handling to prevent circular imports
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except ImportError:
    # Fallback if there are import issues during startup
    JWTAuthentication = None


class CustomJWTAuthentication(BaseAuthentication):
    """Custom JWT Authentication that handles cookies and headers."""
    
    def __init__(self):
        # Initialize the base JWT authentication if available
        if JWTAuthentication:
            self._jwt_auth = JWTAuthentication()
        else:
            self._jwt_auth = None
    
    def authenticate(self, request):
        """Authenticate using JWT tokens from cookies or headers."""
        if not self._jwt_auth:
            return None
            
        try:
            # First try header authentication (standard JWT)
            header_result = self._jwt_auth.authenticate(request)
            if header_result:
                return header_result
            
            # If no header token, try cookie authentication
            raw_token = request.COOKIES.get(getattr(settings, 'AUTH_COOKIE', 'access'))
            if raw_token:
                # Validate the token from cookie
                validated_token = self._jwt_auth.get_validated_token(raw_token)
                user = self._jwt_auth.get_user(validated_token)
                return (user, validated_token)
            
            return None
            
        except Exception:
            # Return None for any authentication failures
            return None
    
    def get_header(self, request):
        """Get JWT header if available."""
        if self._jwt_auth:
            return self._jwt_auth.get_header(request)
        return None
    
    def get_raw_token(self, header):
        """Get raw token from header."""
        if self._jwt_auth:
            return self._jwt_auth.get_raw_token(header)
        return None
    
    def get_validated_token(self, raw_token):
        """Validate token."""
        if self._jwt_auth:
            return self._jwt_auth.get_validated_token(raw_token)
        return None
    
    def get_user(self, validated_token):
        """Get user from validated token."""
        if self._jwt_auth:
            return self._jwt_auth.get_user(validated_token)
        return None
    
    def authenticate_header(self, request):
        """Return the authentication header for 401 responses."""
        return 'Bearer'
