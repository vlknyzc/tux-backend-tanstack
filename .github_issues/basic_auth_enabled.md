---
title: "[AUDIT] [HIGH] BasicAuthentication enabled in local settings"
labels: ["security", "high", "authentication"]
assignees: []
---

## Description

BasicAuthentication is enabled in local development settings, which presents a security risk if these settings are accidentally used in production or if the development environment is exposed.

## Location

- **File**: `main/local_settings.py`
- **Lines**: 248-253
- **Setting**: `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`

## Issue Details

### Current Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',  # ⚠️ Security risk
    ],
    # ...
}
```

### Problems

1. **Weak Authentication**: BasicAuth transmits credentials in base64-encoded (not encrypted) format
2. **No Token Expiration**: BasicAuth credentials don't expire automatically
3. **Risk of Misconfiguration**: If local_settings.py is accidentally used in production
4. **Development Environment Exposure**: If dev environment is accessible, BasicAuth is vulnerable

## Why This Matters

1. **Weak Security**: BasicAuth is easily intercepted and decoded
2. **Credential Exposure**: Credentials transmitted in every request
3. **No Expiration**: Unlike JWT tokens, BasicAuth credentials don't expire
4. **Production Risk**: If settings are misconfigured, BasicAuth could be enabled in production
5. **Compliance**: May violate security compliance requirements

## Attack Scenarios

### Scenario 1: Credential Interception
```bash
# Attacker intercepts BasicAuth header
Authorization: Basic dXNlckBleGFtcGxlLmNvbTpwYXNzd29yZA==
# Decodes to: user@example.com:password
```

### Scenario 2: Accidental Production Deployment
If `local_settings.py` is accidentally used in production, BasicAuth would be enabled, creating a security vulnerability.

## Suggested Fix

### Option 1: Remove BasicAuthentication (Recommended)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        # Removed BasicAuthentication
    ],
    # ... rest of settings
}
```

### Option 2: Conditional BasicAuth (If Needed for Testing)

If BasicAuth is required for specific testing scenarios, enable it conditionally:

```python
import os

# Build authentication classes conditionally
auth_classes = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.SessionAuthentication',
]

# Only add BasicAuth if explicitly enabled via environment variable
if os.environ.get('ENABLE_BASIC_AUTH', 'False').lower() == 'true':
    auth_classes.append('rest_framework.authentication.BasicAuthentication')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': auth_classes,
    # ... rest of settings
}
```

### Option 3: Use Different Settings for Different Environments

Ensure production settings (`production_settings.py`) don't include BasicAuth:

```python
# main/production_settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.CustomJWTAuthentication',  # ✅ Custom JWT only
    ],
    # No BasicAuthentication in production
}
```

## Additional Recommendations

1. **Verify Production Settings**: Ensure `production_settings.py` doesn't include BasicAuth
2. **Document Authentication Methods**: Document which authentication methods are supported
3. **Add Tests**: Add tests to ensure BasicAuth is not enabled in production
4. **Environment Detection**: Add checks to prevent BasicAuth in production
5. **Security Headers**: Ensure proper security headers are set (already configured)

## Testing

Add a test to verify BasicAuth is not enabled in production:

```python
# tests/test_security.py
from django.test import TestCase
from django.conf import settings

class AuthenticationSecurityTestCase(TestCase):
    def test_basic_auth_not_in_production(self):
        """Ensure BasicAuthentication is not enabled in production."""
        if not settings.DEBUG:
            auth_classes = settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']
            basic_auth = 'rest_framework.authentication.BasicAuthentication'
            self.assertNotIn(
                basic_auth,
                auth_classes,
                "BasicAuthentication should not be enabled in production"
            )
```

## Migration Path

1. **Immediate**: Remove BasicAuthentication from `local_settings.py`
2. **Verify**: Ensure all development/testing workflows still work with JWT/Session auth
3. **Update Docs**: Document that BasicAuth is no longer supported
4. **Monitor**: Check for any errors related to BasicAuth removal

## Severity

**HIGH** - Weak authentication method enabled, potential production security risk

## Related Issues

- Rate limiting not configured (#rate-limiting-issue)
- Debug endpoint security issue (#debug-endpoint-issue)

