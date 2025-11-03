---
title: "[AUDIT] [HIGH] Database logging at DEBUG level in production settings"
labels: ["security", "high", "logging"]
assignees: []
---

## Description

Production settings configure database query logging at DEBUG level, which can expose sensitive information including SQL queries, user data, and potentially credentials in logs.

## Location

- **File**: `main/production_settings.py`
- **Lines**: 456-464
- **Setting**: `LOGGING` configuration

## Issue Details

### Current Configuration

```python
LOGGING = {
    # ... other loggers ...
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if os.environ.get('RAILWAY_DEPLOYMENT_ID') else 'ERROR',
            'propagate': False,
        },
        'django.db.backends.postgresql': {
            'handlers': ['console'],
            'level': 'DEBUG' if os.environ.get('RAILWAY_DEPLOYMENT_ID') else 'WARNING',
            'propagate': False,
        },
    },
}
```

### Problems

1. **Conditional DEBUG Logging**: Uses DEBUG level when `RAILWAY_DEPLOYMENT_ID` is set, which is likely in production
2. **Console Handler**: Logs go to console/stdout, which may be stored in log aggregation systems
3. **SQL Query Exposure**: DEBUG level logs all SQL queries, including:
   - Parameter values (potentially passwords, tokens, PII)
   - Table names and schema structure
   - Query patterns that reveal business logic
4. **No Filtering**: No filtering of sensitive data from logs

## Why This Matters

1. **Information Disclosure**: SQL queries may contain sensitive data
2. **Credential Exposure**: If passwords or tokens are logged, they could be compromised
3. **Compliance Issues**: GDPR/CCPA violations if PII is logged
4. **Attack Surface**: Logs may be accessible to unauthorized users
5. **Performance Impact**: DEBUG logging has performance overhead

## Example of Exposed Data

```sql
-- DEBUG logging might expose:
SELECT * FROM users_useraccount WHERE email = 'user@example.com' AND password = 'hashed_password';
-- Or worse, if using raw queries:
SELECT * FROM users_useraccount WHERE email = 'user@example.com' AND password = 'plaintext_password';
```

## Suggested Fix

### Option 1: Use WARNING Level (Recommended)

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Changed from DEBUG
            'propagate': False,
        },
        'django.db.backends.postgresql': {
            'handlers': ['console'],
            'level': 'WARNING',  # Changed from DEBUG
            'propagate': False,
        },
    },
}
```

### Option 2: Environment-Based Configuration

```python
import os

# Determine log level based on environment
DB_LOG_LEVEL = 'DEBUG' if os.environ.get('DJANGO_ENV') == 'DEVELOPMENT' else 'WARNING'

LOGGING = {
    # ... other config ...
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': DB_LOG_LEVEL,
            'propagate': False,
        },
        'django.db.backends.postgresql': {
            'handlers': ['console'],
            'level': DB_LOG_LEVEL,
            'propagate': False,
        },
    },
}
```

### Option 3: Custom Filter to Sanitize Sensitive Data

Create `main/logging_filters.py`:

```python
import re
import logging

class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from log records."""
    
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\']+)', r'password="***"'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\']+)', r'token="***"'),
        (r'api_key["\']?\s*[:=]\s*["\']?([^"\']+)', r'api_key="***"'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\']+)', r'secret="***"'),
        (r'email["\']?\s*[:=]\s*["\']?([^"\']+)', r'email="***"'),  # Optional: mask emails
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
            record.msg = msg
        return True
```

Then update settings:

```python
LOGGING = {
    # ... other config ...
    'filters': {
        'sensitive_data': {
            '()': 'main.logging_filters.SensitiveDataFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['sensitive_data'],  # Add filter
        },
    },
}
```

## Additional Recommendations

1. **Audit Existing Logs**: Review existing logs for exposed sensitive data
2. **Rotate Credentials**: If credentials were logged, rotate them immediately
3. **Log Retention Policy**: Implement log retention and deletion policies
4. **Access Control**: Ensure log storage has proper access controls
5. **Monitoring**: Set up alerts for unusual database query patterns
6. **Separate Debug Environment**: Use separate environment variables for debug logging

## Immediate Action Required

⚠️ **CRITICAL**: Check if database credentials or sensitive data were logged. If so:
1. Rotate database passwords immediately
2. Review log storage access controls
3. Audit logs for exposed sensitive information
4. Update credentials in environment variables

## Testing

Verify logging level in production:

```python
# Add to a management command or startup check
import logging
db_logger = logging.getLogger('django.db.backends')
assert db_logger.level >= logging.WARNING, "Database logging should be WARNING or higher in production"
```

## Severity

**HIGH** - Potential exposure of sensitive data and credentials in production logs

## Related Issues

- Debug endpoint security issue (#debug-endpoint-issue)
- Missing security headers (#security-headers-issue)

