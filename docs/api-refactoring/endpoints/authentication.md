# Authentication Endpoints Analysis

**Priority:** 🔴 High  
**Breaking Changes:** ⚠️ Yes  
**Implementation:** Phase 1 (Weeks 1-2)

## Current State Problems

The TUX Backend currently has **10+ overlapping authentication endpoints** from multiple libraries:

### 1. SimpleJWT Endpoints
| Current Endpoint | Method | Purpose | Status |
|------------------|---------|---------|--------|
| `/api/v1/token/` | POST | JWT token creation | ❌ Duplicate |
| `/api/v1/token/refresh/` | POST | JWT token refresh | ❌ Duplicate |

### 2. Custom JWT Endpoints  
| Current Endpoint | Method | Purpose | Status |
|------------------|---------|---------|--------|
| `/api/v1/jwt/create/` | POST | JWT token creation | ❌ Duplicate |
| `/api/v1/jwt/refresh/` | POST | JWT token refresh | ❌ Duplicate |
| `/api/v1/jwt/verify/` | POST | JWT token verification | ⚠️ Needed but misplaced |
| `/api/v1/logout/` | POST | User logout | ⚠️ Needed but misplaced |

### 3. Djoser User Endpoints
| Current Endpoint | Method | Purpose | Status |
|------------------|---------|---------|--------|
| `/api/v1/users/` | GET/POST | User management | ❌ Duplicate functionality |
| `/api/v1/users/me/` | GET/PUT | Current user profile | ✅ Keep |
| `/api/v1/users/set_password/` | POST | Password change | ❌ Duplicate |
| `/api/v1/users/reset_password/` | POST | Password reset | ❌ Duplicate |
| `/api/v1/users/reset_password_confirm/` | POST | Password reset confirm | ❌ Duplicate |
| `/api/v1/users/activation/` | POST | User activation | ❌ Duplicate |

### 4. Custom User Management
| Current Endpoint | Method | Purpose | Status |
|------------------|---------|---------|--------|
| `/api/v1/users/` | GET/POST/PUT/DELETE | User CRUD | ❌ Duplicate with Djoser |
| `/api/v1/workspace-users/` | GET/POST/PUT/DELETE | Workspace assignments | ✅ Keep (unique functionality) |

## Issues Identified

1. **Functional Duplication**: Same functionality exposed through 2-3 different endpoints
2. **Client Confusion**: Developers don't know which endpoint to use
3. **Maintenance Burden**: Multiple code paths for same functionality
4. **Security Inconsistency**: Different validation/security patterns
5. **Documentation Scattered**: Auth docs spread across multiple sections

## Recommendations

### ✅ Consolidate to Single Auth Pattern

**Target State: 4 Clean Authentication Endpoints**

| New Endpoint | Method | Purpose | Replaces |
|--------------|---------|---------|----------|
| `/api/v1/auth/login/` | POST | User login & JWT creation | `/token/`, `/jwt/create/` |
| `/api/v1/auth/refresh/` | POST | JWT token refresh | `/token/refresh/`, `/jwt/refresh/` |
| `/api/v1/auth/verify/` | POST | JWT token verification | `/jwt/verify/` |
| `/api/v1/auth/logout/` | POST | User logout & token invalidation | `/logout/` |

### ✅ Streamlined User Management

| New Endpoint | Method | Purpose | Replaces |
|--------------|---------|---------|----------|
| `/api/v1/users/` | GET/POST/PUT/DELETE | User CRUD (admin only) | Djoser + custom users endpoints |
| `/api/v1/users/me/` | GET/PUT | Current user profile | Keep existing (works well) |
| `/api/v1/users/change-password/` | POST | Password change | `/users/set_password/` |
| `/api/v1/workspace-users/` | GET/POST/PUT/DELETE | Workspace assignments | Keep existing (unique) |

## Implementation Plan

### Step 1: Create New Auth Views (Week 1)
```python
# users/views.py - New consolidated auth views
class AuthLoginView(APIView):
    """Single login endpoint replacing /token/ and /jwt/create/"""
    
class AuthRefreshView(APIView): 
    """Single refresh endpoint replacing /token/refresh/ and /jwt/refresh/"""
    
class AuthVerifyView(APIView):
    """JWT verification endpoint"""
    
class AuthLogoutView(APIView):
    """Logout with token blacklisting"""
```

### Step 2: Add New URL Patterns (Week 1)
```python
# users/urls.py
urlpatterns = [
    # New auth endpoints
    path('auth/login/', AuthLoginView.as_view(), name='auth-login'),
    path('auth/refresh/', AuthRefreshView.as_view(), name='auth-refresh'), 
    path('auth/verify/', AuthVerifyView.as_view(), name='auth-verify'),
    path('auth/logout/', AuthLogoutView.as_view(), name='auth-logout'),
    
    # Streamlined user management
    path('users/change-password/', ChangePasswordView.as_view()),
    
    # Keep existing
    path('users/me/', UserProfileView.as_view()),
    path('workspace-users/', WorkspaceUserViewSet.as_view()),
]
```

### Step 3: Dual Endpoint Support (Week 2)
- Keep old endpoints active with deprecation warnings
- Add response headers: `X-Deprecated: true`, `X-Use-Instead: /api/v1/auth/login/`
- Log usage of deprecated endpoints

### Step 4: Update Documentation (Week 2)
- Single auth section in API docs
- Clear migration examples
- Update Swagger/OpenAPI schemas

## Breaking Change Migration

### Client Impact Assessment
- **High Impact**: All client applications need auth endpoint updates
- **Medium Impact**: User management endpoints change
- **Low Impact**: Workspace-user assignments unchanged

### Migration Timeline
1. **Month 1**: Deploy dual endpoints with warnings
2. **Months 2-3**: Client SDK updates and testing  
3. **Months 4-6**: Client application migration
4. **Month 6**: Remove deprecated endpoints

### Backward Compatibility
```python
# Example deprecation response
{
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here", 
    "_deprecated": {
        "warning": "This endpoint is deprecated",
        "use_instead": "/api/v1/auth/login/",
        "removal_date": "2025-12-01"
    }
}
```

## Testing Strategy

### New Endpoint Tests
- [ ] Login functionality with correct JWT generation
- [ ] Refresh token rotation and validation  
- [ ] Token verification accuracy
- [ ] Logout with proper token invalidation
- [ ] Error handling and validation

### Regression Tests  
- [ ] Existing client flows still work during transition
- [ ] User management permissions unchanged
- [ ] Workspace assignment functionality preserved

## Success Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Auth endpoints | 10+ | 4 | URL count |
| Client confusion | High | None | Support tickets |
| Code maintenance | 3 libraries | 1 pattern | Lines of code |
| API documentation | 4 sections | 1 section | Doc pages |

## Risk Mitigation

1. **Gradual Rollout**: Deploy new endpoints first, deprecate old ones later
2. **Monitoring**: Track usage of old vs new endpoints
3. **Rollback Plan**: Keep old endpoints for emergency rollback
4. **Communication**: Clear migration timeline to client teams

---

**Next:** Review [core-resources.md](core-resources.md) for CRUD endpoint analysis.