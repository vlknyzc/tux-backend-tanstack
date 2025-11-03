---
title: "[AUDIT] [CRITICAL] No rate limiting/throttling configured for API endpoints"
labels: ["security", "critical", "performance"]
assignees: []
---

## Description

The Django REST Framework configuration lacks rate limiting/throttling settings, making all API endpoints vulnerable to DoS attacks, brute force attempts, and resource exhaustion.

## Location

- **Files**:
  - `main/production_settings.py:256-271`
  - `main/local_settings.py:248-266`
- **Settings Key**: `REST_FRAMEWORK`

## Issue Details

### Current Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [...],
    'DEFAULT_PERMISSION_CLASSES': [...],
    # ⚠️ MISSING: 'DEFAULT_THROTTLE_CLASSES'
    # ⚠️ MISSING: 'DEFAULT_THROTTLE_RATES'
}
```

### Affected Endpoints

All API endpoints are vulnerable, including:

- Authentication endpoints (`/api/v1/users/jwt/create/`) - **Brute force attacks**
- Multi-operation endpoints (`/api/v1/workspaces/{id}/multi-operations/`) - **Resource exhaustion**
- Bulk operations (`/api/v1/workspaces/{id}/strings/bulk/`) - **DoS attacks**
- Project endpoints - **Data scraping**
- Any public endpoints (version, health checks)

## Why This Matters

1. **Brute Force Attacks**: Attackers can make unlimited login attempts
2. **DoS Attacks**: No protection against request flooding
3. **Resource Exhaustion**: Expensive operations can be repeatedly called
4. **Cost Impact**: Uncontrolled API usage can increase server costs
5. **Performance Degradation**: Legitimate users may experience slowdowns

## Attack Scenarios

### Scenario 1: Brute Force Login

```bash
# Attacker can make unlimited requests
for i in {1..10000}; do
  curl -X POST /api/v1/users/jwt/create/ \
    -d '{"email":"target@example.com","password":"guess'$i'"}'
done
```

### Scenario 2: Resource Exhaustion

```bash
# Repeatedly call expensive bulk operations
for i in {1..1000}; do
  curl -X POST /api/v1/workspaces/1/multi-operations/execute/ \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"operations": [...]}'  # Large payload
done
```

## Suggested Fix

### Step 1: Install django-ratelimit (Recommended)

```bash
pip install django-ratelimit
```

### Step 2: Configure Throttling in Settings

**For Production** (`main/production_settings.py`):

```python
REST_FRAMEWORK = {
    # ... existing settings ...

    # Rate limiting configuration
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',           # Anonymous users
        'user': '1000/hour',          # Authenticated users
        'login': '5/minute',          # Login attempts
        'bulk': '10/minute',          # Bulk operations
        'multi_ops': '20/minute',     # Multi-operation endpoints
    },
}
```

**For Local Development** (`main/local_settings.py`):

```python
REST_FRAMEWORK = {
    # ... existing settings ...

    # More lenient limits for development
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '10000/hour',
    },
}
```

### Step 3: Add Scoped Throttling to Sensitive Views

**Example: Authentication Endpoints** (`users/views.py`):

```python
from rest_framework.throttling import ScopedRateThrottle

class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_scope = 'login'
    throttle_classes = [ScopedRateThrottle]
    # ... rest of code
```

**Example: Bulk Operations** (`master_data/views/string_views.py`):

```python
from rest_framework.throttling import ScopedRateThrottle

class StringViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    throttle_scope = 'bulk'
    throttle_classes = [ScopedRateThrottle]

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_create(self, request, workspace_id=None):
        # ... existing code
```

**Example: Multi-Operations** (`master_data/views/multi_operations_views.py`):

```python
class MultiOperationsViewSet(WorkspaceValidationMixin, viewsets.ViewSet):
    throttle_scope = 'multi_ops'
    throttle_classes = [ScopedRateThrottle]
    # ... rest of code
```

### Step 4: Custom Throttle for IP-based Rate Limiting

Create `users/throttles.py`:

```python
from rest_framework.throttling import BaseThrottle
from django.core.cache import cache

class IPRateThrottle(BaseThrottle):
    """Custom throttle based on IP address."""
    scope = 'ip'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f'throttle_{self.scope}_{ident}'

    def allow_request(self, request, view):
        if self.rate is None:
            return True

        key = self.get_cache_key(request, view)
        if key is None:
            return True

        self.history = cache.get(key, [])
        self.now = self.timer()

        # Remove old entries
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return False

        self.history.insert(0, self.now)
        cache.set(key, self.history, self.duration)
        return True
```

## Additional Recommendations

1. **Monitor Throttle Hits**: Log when rate limits are exceeded for security monitoring
2. **Different Limits by Endpoint**: Critical endpoints (login, password reset) should have stricter limits
3. **Whitelist Internal IPs**: Allow higher limits for trusted internal IPs
4. **Graceful Error Messages**: Return proper 429 responses with Retry-After headers
5. **Consider Redis**: For distributed rate limiting in production

## Testing

Add tests to verify rate limiting works:

```python
# tests/test_rate_limiting.py
from rest_framework.test import APIClient
from django.test import TestCase

class RateLimitingTestCase(TestCase):
    def test_login_rate_limit(self):
        client = APIClient()
        # Make 6 requests (limit is 5/minute)
        for i in range(6):
            response = client.post('/api/v1/users/jwt/create/', {
                'email': 'test@example.com',
                'password': 'wrong'
            })

        # 6th request should be throttled
        self.assertEqual(response.status_code, 429)
```

## Severity

**CRITICAL** - No protection against DoS, brute force, or resource exhaustion attacks

## Related Issues

- Debug endpoint security issue (#debug-endpoint-issue)
- Missing request body size limits (#request-size-limits-issue)
