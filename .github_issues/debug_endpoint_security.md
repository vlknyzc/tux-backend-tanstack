---
title: "[AUDIT] [CRITICAL] Debug endpoint exposes sensitive information"
labels: ["security", "critical", "bug"]
assignees: []
---

## Description

The `debug_auth_status` endpoint in `users/views.py` exposes sensitive system information without proper authentication or rate limiting. This endpoint is accessible via `AllowAny` permission, making it publicly accessible.

## Location

- **File**: `users/views.py`
- **Lines**: 117-160
- **URL Pattern**: `/api/v1/users/debug/auth-status/` (via `users/urls.py:38`)

## Issue Details

The endpoint exposes:

1. **User count** - Reveals system scale and user base size
2. **Secret key length** - Information about cryptographic key strength
3. **JWT generation capabilities** - System capabilities and potential attack vectors
4. **User model information** - Internal system architecture details

### Code Snippet

```python
@api_view(['GET'])
@permission_classes([AllowAny])  # ⚠️ PUBLIC ACCESS
def debug_auth_status(request):
    """Debug endpoint to check authentication system status."""
    # ...
    return Response({
        'status': 'ok',
        'auth_system': 'ready',
        'user_count': user_count,  # ⚠️ Sensitive
        'jwt_test': jwt_test,
        'user_model': str(User),
        'secret_key_length': len(settings.SECRET_KEY),  # ⚠️ Sensitive
    })
```

## Why This Matters

1. **Information Disclosure**: Attackers can gather reconnaissance data about the system
2. **Reconnaissance**: User count and system capabilities help attackers plan attacks
3. **No Rate Limiting**: Can be repeatedly queried to gather intelligence
4. **Production Risk**: If deployed to production, this endpoint is publicly accessible

## Suggested Fix

### Option 1: Require Authentication (Recommended)

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Require authentication
def debug_auth_status(request):
    # Only allow superusers or staff
    if not (request.user.is_superuser or request.user.is_staff):
        return Response({'error': 'Access denied'}, status=403)
    # ... rest of code
```

### Option 2: Remove Debug Endpoint (Best Practice)

- Remove the endpoint entirely if not needed
- If debugging is required, use Django's built-in debug toolbar or admin panel
- Or restrict to development environment only:

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth_status(request):
    if not settings.DEBUG:
        return Response({'error': 'Not available in production'}, status=404)
    # ... rest of code
```

### Option 3: Add IP Whitelist

- Restrict access to specific IP addresses (internal/admin IPs only)
- Use middleware or decorator to check IP whitelist

## Additional Recommendations

1. **Remove from production**: Ensure this endpoint is not accessible in production
2. **Add rate limiting**: If kept, add throttling to prevent abuse
3. **Sanitize output**: Remove sensitive information like secret key length
4. **Audit logging**: Log all access attempts for security monitoring

## Severity

**CRITICAL** - Exposes sensitive system information to unauthorized users

## Related Issues

- Rate limiting not configured (#rate-limiting-issue)
- Missing security headers (#security-headers-issue)
