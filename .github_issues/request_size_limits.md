---
title: "[AUDIT] [HIGH] No request body size limits configured"
labels: ["security", "high", "performance", "dos"]
assignees: []
---

## Description

Django settings lack explicit request body size limits (`DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`), making the API vulnerable to DoS attacks through large request payloads.

## Location

- **Files**: 
  - `main/production_settings.py`
  - `main/local_settings.py`
- **Missing Settings**: `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`, `DATA_UPLOAD_MAX_NUMBER_FIELDS`

## Issue Details

### Current State

No explicit size limits are configured. Django defaults are:
- `DATA_UPLOAD_MAX_MEMORY_SIZE`: 2.5 MB (default)
- `FILE_UPLOAD_MAX_MEMORY_SIZE`: 2.5 MB (default)
- `DATA_UPLOAD_MAX_NUMBER_FIELDS`: 1000 (default)

### Vulnerable Endpoints

1. **Bulk Operations** (`/api/v1/workspaces/{id}/strings/bulk/`)
   - Can accept unlimited string creation requests
   - `master_data/serializers/bulk_operations.py:71-75` allows up to 1000 items, but no size limit

2. **Multi-Operations** (`/api/v1/workspaces/{id}/multi-operations/execute/`)
   - Can accept unlimited operations in a single request
   - No explicit size validation

3. **Batch Updates** (`master_data/serializers/batch_operations.py`)
   - `StringBatchUpdateRequestSerializer` allows up to 1000 updates
   - No request body size validation

### Example Attack Scenario

```python
# Attacker sends massive payload
import requests

large_payload = {
    "operations": [
        {
            "type": "create_string",
            "data": {
                "field": 1,
                "value": "x" * 1000000  # 1MB per string
            }
        }
    ] * 1000  # 1000 operations = 1GB payload
}

response = requests.post(
    '/api/v1/workspaces/1/multi-operations/execute/',
    json=large_payload,  # Could exhaust server memory
    headers={'Authorization': f'Bearer {token}'}
)
```

## Why This Matters

1. **DoS Attacks**: Large payloads can exhaust server memory
2. **Resource Exhaustion**: Unbounded requests can crash the server
3. **Performance Degradation**: Large requests slow down processing
4. **Cost Impact**: Increased memory usage increases hosting costs
5. **Application Crashes**: Can cause application failures under load

## Suggested Fix

### Step 1: Configure Request Size Limits

**For Production** (`main/production_settings.py`):

```python
# Request body size limits (in bytes)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Maximum number of fields

# For file uploads (if supported)
FILE_UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 50 MB per file
```

**For Local Development** (`main/local_settings.py`):

```python
# More lenient limits for development
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000
```

### Step 2: Add Custom Validation in Serializers

**Bulk Operations** (`master_data/serializers/bulk_operations.py`):

```python
import sys
from rest_framework import serializers

class StringBatchUpdateRequestSerializer(serializers.Serializer):
    updates = serializers.ListField(
        child=StringUpdateSerializer(),
        min_length=1,
        max_length=1000,
        help_text="List of string updates to apply"
    )
    
    def validate(self, attrs):
        """Validate request size."""
        # Estimate payload size
        import json
        payload_size = len(json.dumps(attrs).encode('utf-8'))
        max_size = 10 * 1024 * 1024  # 10 MB
        
        if payload_size > max_size:
            raise serializers.ValidationError(
                f"Request payload too large: {payload_size} bytes. Maximum allowed: {max_size} bytes"
            )
        
        return super().validate(attrs)
```

**Multi-Operations** (`master_data/serializers/batch_operations.py`):

```python
class MultiOperationSerializer(serializers.Serializer):
    operations = serializers.ListField(
        child=OperationSerializer(),
        min_length=1,
        max_length=500,  # Reduced from unlimited
    )
    
    def validate(self, attrs):
        """Validate request size and operation count."""
        operations = attrs.get('operations', [])
        
        # Limit total operations
        total_items = sum(
            len(op['data']) if isinstance(op.get('data'), list) else 1
            for op in operations
        )
        
        if total_items > 1000:
            raise serializers.ValidationError(
                f"Too many operations: {total_items}. Maximum allowed: 1000"
            )
        
        # Validate payload size
        import json
        payload_size = len(json.dumps(attrs).encode('utf-8'))
        max_size = 10 * 1024 * 1024  # 10 MB
        
        if payload_size > max_size:
            raise serializers.ValidationError(
                f"Request payload too large: {payload_size} bytes. Maximum allowed: {max_size} bytes"
            )
        
        return super().validate(attrs)
```

### Step 3: Add Middleware for Request Size Validation

Create `main/middleware.py` (add to existing file):

```python
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class RequestSizeLimitMiddleware(MiddlewareMixin):
    """Middleware to enforce request size limits."""
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
    
    def process_request(self, request):
        """Check request size before processing."""
        content_length = request.META.get('CONTENT_LENGTH')
        
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.MAX_REQUEST_SIZE:
                    logger.warning(
                        f"Request size limit exceeded: {content_length} bytes "
                        f"(limit: {self.MAX_REQUEST_SIZE} bytes) from {request.META.get('REMOTE_ADDR')}"
                    )
                    return JsonResponse(
                        {
                            'error': 'Request payload too large',
                            'max_size': self.MAX_REQUEST_SIZE,
                            'received_size': content_length
                        },
                        status=413  # Payload Too Large
                    )
            except (ValueError, TypeError):
                pass  # Invalid content length, let Django handle it
        
        return None
```

Add to `MIDDLEWARE` in settings:

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "main.middleware.RequestSizeLimitMiddleware",  # Add here
    # ... rest of middleware
]
```

### Step 4: Add Error Handling

Update views to return proper error responses:

```python
# In views with bulk operations
try:
    serializer = BulkStringCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
except serializers.ValidationError as e:
    if 'too large' in str(e).lower():
        return Response(
            {'error': 'Request payload exceeds size limit', 'details': str(e)},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )
    raise
```

## Additional Recommendations

1. **Monitor Request Sizes**: Log large requests for analysis
2. **Rate Limiting**: Combine with rate limiting (#rate-limiting-issue) for better protection
3. **Progressive Limits**: Different limits for different endpoints
4. **Compression**: Consider supporting request compression for legitimate large payloads
5. **Documentation**: Document size limits in API documentation

## Testing

Add tests to verify size limits:

```python
# tests/test_request_limits.py
from django.test import TestCase
from rest_framework.test import APIClient

class RequestSizeLimitTestCase(TestCase):
    def test_bulk_operation_size_limit(self):
        """Test that large bulk operations are rejected."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # Create payload exceeding limit
        large_payload = {
            'strings': [
                {'field': 1, 'value': 'x' * 1000000}  # 1MB per string
            ] * 20  # 20MB total
        }
        
        response = client.post(
            f'/api/v1/workspaces/{self.workspace.id}/strings/bulk/',
            data=large_payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, 413)  # Payload Too Large
```

## Severity

**HIGH** - Vulnerable to DoS attacks through large request payloads

## Related Issues

- Rate limiting not configured (#rate-limiting-issue)
- No input validation limits (#input-validation-issue)

