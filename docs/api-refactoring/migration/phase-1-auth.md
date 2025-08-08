# Phase 1: Authentication Consolidation

**Timeline:** Weeks 1-2  
**Priority:** 🔴 High  
**Breaking Changes:** ⚠️ Yes  
**Team Effort:** 1-2 developers

## Objective

Consolidate **10+ overlapping authentication endpoints** into **4 clean, standardized endpoints** while maintaining backward compatibility during transition.

## Current State Problems

### Duplicate Authentication Patterns
- **SimpleJWT**: `/api/v1/token/`, `/api/v1/token/refresh/`
- **Custom JWT**: `/api/v1/jwt/create/`, `/api/v1/jwt/refresh/`, `/api/v1/jwt/verify/`
- **Djoser**: Multiple user management endpoints
- **Custom User**: Additional user endpoints

### Client Confusion
- Developers don't know which endpoint to use
- Different error response formats
- Inconsistent token handling

## Target State

### 4 Standardized Auth Endpoints
| New Endpoint | Method | Purpose | Replaces |
|--------------|--------|---------|----------|
| `/api/v1/auth/login/` | POST | User login & JWT creation | `/token/`, `/jwt/create/` |
| `/api/v1/auth/refresh/` | POST | JWT token refresh | `/token/refresh/`, `/jwt/refresh/` |
| `/api/v1/auth/verify/` | POST | JWT token verification | `/jwt/verify/` |
| `/api/v1/auth/logout/` | POST | User logout & token invalidation | `/logout/` |

### 4 User Management Endpoints
| New Endpoint | Method | Purpose | Replaces |
|--------------|--------|---------|----------|
| `/api/v1/users/` | GET/POST/PUT/DELETE | User CRUD (admin only) | Djoser + custom users |
| `/api/v1/users/me/` | GET/PUT | Current user profile | Keep existing |
| `/api/v1/users/change-password/` | POST | Password change | `/users/set_password/` |
| `/api/v1/workspace-users/` | GET/POST/PUT/DELETE | Workspace assignments | Keep existing |

## Week 1: Implementation

### Day 1-2: Create New Auth Views

#### 1. Create Consolidated Auth Views
```python
# users/views/auth.py (new file)
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema

@extend_schema(
    request=LoginSerializer,
    responses={200: TokenSerializer, 400: ErrorSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """
    Unified login endpoint replacing /token/ and /jwt/create/
    
    Returns access and refresh tokens for valid credentials.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 hour
            })
        
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=RefreshTokenSerializer,
    responses={200: TokenSerializer, 400: ErrorSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_refresh(request):
    """
    Unified refresh endpoint replacing /token/refresh/ and /jwt/refresh/
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if serializer.is_valid():
        try:
            refresh_token = RefreshToken(serializer.validated_data['refresh_token'])
            return Response({
                'access_token': str(refresh_token.access_token),
                'refresh_token': str(refresh_token),
                'expires_in': 3600
            })
        except TokenError:
            return Response(
                {'error': 'Invalid refresh token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    request=TokenVerifySerializer,
    responses={200: TokenValidSerializer, 400: ErrorSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_verify(request):
    """
    JWT token verification endpoint
    """
    serializer = TokenVerifySerializer(data=request.data)
    if serializer.is_valid():
        try:
            token = AccessToken(serializer.validated_data['token'])
            return Response({
                'valid': True,
                'user_id': token['user_id'],
                'expires_at': datetime.fromtimestamp(token['exp'])
            })
        except TokenError:
            return Response(
                {'valid': False, 'error': 'Invalid token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={200: LogoutSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """
    User logout with token blacklisting
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({'message': 'Successfully logged out'})
    except TokenError:
        return Response(
            {'error': 'Invalid token'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
```

#### 2. Create Auth Serializers
```python
# users/serializers/auth.py (new file)
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer(read_only=True)
    expires_in = serializers.IntegerField()

class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField()

class TokenValidSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    user_id = serializers.IntegerField(required=False)
    expires_at = serializers.DateTimeField(required=False)

class LogoutSerializer(serializers.Serializer):
    message = serializers.CharField()

class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    details = serializers.DictField(required=False)
```

### Day 3-4: Update URL Patterns

#### 3. Update users/urls.py
```python
# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.auth import auth_login, auth_refresh, auth_verify, auth_logout
from .views.user_management import (
    UserManagementViewSet, 
    WorkspaceUserManagementViewSet,
    UserProfileView,
    ChangePasswordView
)

# Router for management endpoints
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='user-management')
router.register(r'workspace-users', WorkspaceUserManagementViewSet, basename='workspace-user-management')

urlpatterns = [
    # New consolidated auth endpoints
    path('auth/login/', auth_login, name='auth-login'),
    path('auth/refresh/', auth_refresh, name='auth-refresh'),
    path('auth/verify/', auth_verify, name='auth-verify'),
    path('auth/logout/', auth_logout, name='auth-logout'),
    
    # User management endpoints
    path('', include(router.urls)),
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # TEMPORARY: Deprecated endpoints with warnings (remove in 6 months)
    path('jwt/create/', deprecated_jwt_create, name='deprecated-jwt-create'),
    path('jwt/refresh/', deprecated_jwt_refresh, name='deprecated-jwt-refresh'), 
    path('jwt/verify/', deprecated_jwt_verify, name='deprecated-jwt-verify'),
    path('logout/', deprecated_logout, name='deprecated-logout'),
]
```

#### 4. Update main/urls.py
```python
# main/urls.py
urlpatterns = [
    # ... existing patterns ...
    
    # Remove SimpleJWT endpoints (will be deprecated)
    # path('api/(?P<version>(v1|v2))/token/', TokenObtainPairView.as_view()),
    # path('api/(?P<version>(v1|v2))/token/refresh/', TokenRefreshView.as_view()),
    
    # Keep Djoser endpoints temporarily with deprecation warnings
    re_path(r'^api/(?P<version>(v1|v2))/', include('djoser.urls')),  # TEMPORARY
]
```

### Day 5: Add Backward Compatibility

#### 5. Create Deprecated Endpoint Wrappers
```python
# users/views/deprecated.py (new file)
import warnings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .auth import auth_login, auth_refresh, auth_verify, auth_logout

@api_view(['POST'])
def deprecated_jwt_create(request):
    """Deprecated: Use /api/v1/auth/login/ instead"""
    response = auth_login(request)
    
    # Add deprecation headers
    response['X-Deprecated'] = 'true'
    response['X-Use-Instead'] = '/api/v1/auth/login/'
    response['X-Removal-Date'] = '2025-12-01'
    
    # Add deprecation warning to response body
    if hasattr(response, 'data') and isinstance(response.data, dict):
        response.data['_deprecated'] = {
            'warning': 'This endpoint is deprecated',
            'use_instead': '/api/v1/auth/login/',
            'removal_date': '2025-12-01'
        }
    
    return response

@api_view(['POST'])  
def deprecated_jwt_refresh(request):
    """Deprecated: Use /api/v1/auth/refresh/ instead"""
    response = auth_refresh(request)
    
    response['X-Deprecated'] = 'true'
    response['X-Use-Instead'] = '/api/v1/auth/refresh/'
    response['X-Removal-Date'] = '2025-12-01'
    
    if hasattr(response, 'data') and isinstance(response.data, dict):
        response.data['_deprecated'] = {
            'warning': 'This endpoint is deprecated',
            'use_instead': '/api/v1/auth/refresh/',
            'removal_date': '2025-12-01'
        }
    
    return response

# Similar implementations for deprecated_jwt_verify and deprecated_logout
```

## Week 2: Testing & Documentation

### Day 6-8: Comprehensive Testing

#### 6. Create Auth Test Suite
```python
# users/tests/test_auth_consolidation.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthConsolidationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_new_login_endpoint(self):
        """Test new consolidated login endpoint"""
        url = reverse('auth-login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertIn('expires_in', response.data)
    
    def test_new_refresh_endpoint(self):
        """Test new consolidated refresh endpoint"""
        # Get tokens from login
        login_url = reverse('auth-login')
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        login_response = self.client.post(login_url, login_data)
        refresh_token = login_response.data['refresh_token']
        
        # Test refresh
        refresh_url = reverse('auth-refresh')
        refresh_data = {'refresh_token': refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data)
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', refresh_response.data)
    
    def test_deprecated_endpoints_work(self):
        """Test that deprecated endpoints still work with warnings"""
        url = reverse('deprecated-jwt-create')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['X-Deprecated'], 'true')
        self.assertIn('_deprecated', response.data)
    
    def test_token_verification(self):
        """Test new token verification endpoint"""
        # Get token from login
        login_url = reverse('auth-login')
        login_response = self.client.post(login_url, {
            'username': 'testuser', 
            'password': 'testpass123'
        })
        access_token = login_response.data['access_token']
        
        # Verify token
        verify_url = reverse('auth-verify')
        verify_response = self.client.post(verify_url, {'token': access_token})
        
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['valid'])
    
    def test_logout_functionality(self):
        """Test logout with token blacklisting"""
        # Login and get tokens
        login_url = reverse('auth-login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Logout
        logout_url = reverse('auth-logout')
        logout_response = self.client.post(logout_url, {
            'refresh_token': login_response.data['refresh_token']
        })
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_response.data)
```

### Day 9-10: Update Documentation

#### 7. Update API Documentation
```python
# Update drf-spectacular schemas
SPECTACULAR_SETTINGS = {
    # ... existing settings ...
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'displayRequestDuration': True,
    },
    'PREPROCESSING_HOOKS': [
        'users.schema_processors.add_auth_deprecation_warnings'
    ],
}
```

#### 8. Create Migration Guide
```markdown
# Authentication Migration Guide

## New Endpoints (Use These)

### Login
**NEW:** `POST /api/v1/auth/login/`
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com"
  },
  "expires_in": 3600
}
```

### Deprecated Endpoints (Stop Using)

| Old Endpoint | New Endpoint | Status |
|-------------|-------------|--------|
| `POST /api/v1/token/` | `POST /api/v1/auth/login/` | Deprecated |
| `POST /api/v1/token/refresh/` | `POST /api/v1/auth/refresh/` | Deprecated |
| `POST /api/v1/jwt/create/` | `POST /api/v1/auth/login/` | Deprecated |
| `POST /api/v1/jwt/refresh/` | `POST /api/v1/auth/refresh/` | Deprecated |
```

## Rollout Plan

### Week 1 (Implementation)
- [ ] Create new auth views and serializers
- [ ] Update URL patterns with new endpoints
- [ ] Add backward compatibility wrappers
- [ ] Basic functionality testing

### Week 2 (Testing & Docs)
- [ ] Comprehensive test suite
- [ ] Update API documentation  
- [ ] Create migration guide for clients
- [ ] Performance testing

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Auth endpoints | 10+ | 4 | -60% reduction |
| Client confusion | High | Low | Developer feedback |
| Code maintenance | 3 libraries | 1 pattern | Lines of code |
| Response consistency | 60% | 95% | Standard format |

## Risk Mitigation

1. **Dual endpoint support** for 6 months
2. **Comprehensive testing** before deployment
3. **Gradual client migration** with timeline
4. **Monitoring** of endpoint usage
5. **Rollback plan** if issues arise

## Next Steps

After Phase 1 completion:
- Monitor deprecated endpoint usage
- Begin client migration notifications  
- Plan Phase 2: Resource naming consolidation

---

**Next:** [Phase 2: Resource Naming](phase-2-naming.md)