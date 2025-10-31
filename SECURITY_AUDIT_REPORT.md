# Security & Code Quality Audit Report
**Date:** 2025-10-29
**Auditor:** Claude Code
**Repository:** tux-backend (Django REST API)
**Total Files Analyzed:** 123 Python files
**Lines of Code:** ~13,420 (views/serializers/services)

---

## Executive Summary

This comprehensive audit identified **11 HIGH severity** and **15 MEDIUM severity** issues across security, code quality, and testing domains. While no CRITICAL vulnerabilities were found, several HIGH-priority security issues require immediate attention, particularly around CORS configuration, CSRF protection, rate limiting, and test coverage gaps.

**Key Findings:**
- ✅ No SQL injection vulnerabilities detected (Django ORM used correctly)
- ✅ No exposed credentials in codebase (.env.local properly gitignored)
- ✅ Dependencies are up-to-date with security patches
- ⚠️ High-severity security misconfigurations in development settings
- ⚠️ Minimal test coverage (8 test files for 86 production files)
- ⚠️ Poor type safety (only 23% of functions have type hints)
- ⚠️ No API rate limiting configured

---

## 🔴 HIGH SEVERITY ISSUES

### 1. CORS Allow All Origins Enabled in Development Settings
**Severity:** HIGH
**File:** `main/local_settings.py:199`
**Issue:** `CORS_ALLOW_ALL_ORIGINS = True` allows any origin to make authenticated requests.

**Risk:**
- If accidentally deployed to production, this opens the API to cross-origin attacks
- Credentials are allowed (`CORS_ALLOW_CREDENTIALS = True`), making this especially dangerous

**Fix:**
```python
# Remove CORS_ALLOW_ALL_ORIGINS completely
CORS_ALLOW_ALL_ORIGINS = False  # or remove this line entirely
# Keep only:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]
```

---

### 2. CSRF Cookie Not HTTP-Only in Development
**Severity:** HIGH
**File:** `main/local_settings.py:149`
**Issue:** `CSRF_COOKIE_HTTPONLY = False` allows JavaScript access to CSRF tokens.

**Risk:**
- XSS attacks can steal CSRF tokens
- Violates defense-in-depth principles

**Fix:**
```python
CSRF_COOKIE_HTTPONLY = True  # Even in development
```

---

### 3. No API Rate Limiting Configured
**Severity:** HIGH
**Files:** All API viewsets in `master_data/views/`
**Issue:** No throttling or rate limiting on any API endpoints.

**Risk:**
- API abuse and DoS attacks
- Brute force attacks on authentication endpoints
- Resource exhaustion

**Fix:**
```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

### 4. Unsafe exec() Usage in Test Script
**Severity:** HIGH
**File:** `test_with_postgresql.py:73`
**Issue:** Uses `exec()` to execute file contents dynamically.

**Risk:**
- Arbitrary code execution if test file is compromised
- Bad security practice even in test code

**Fix:**
```python
# Replace exec() with proper module import
import importlib.util
spec = importlib.util.spec_from_file_location("test_migration", "test_migration.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

---

### 5. Inadequate Test Coverage for Critical Security Functions
**Severity:** HIGH
**Coverage:** Only 8 test files for 86+ production Python files
**Missing Tests:**
- No tests for authentication flows (`users/authentication.py`)
- No tests for workspace access control
- No tests for JWT token validation
- No tests for API endpoints (rule_views, string_views, etc.)
- No tests for propagation service

**Risk:**
- Security regressions go undetected
- Cannot verify authentication/authorization logic works correctly

**Fix:**
Create comprehensive test suite covering:
- Authentication and authorization
- Workspace isolation
- All API endpoints
- Input validation
- Error handling

---

### 6. Missing Input Validation on Workspace ID Query Parameters
**Severity:** HIGH
**Files:** Multiple ViewSets in `master_data/views/`
**Example:** `rule_views.py:88-109`, `dimension_views.py:114-125`

**Issue:** Workspace ID from query params converted to int without proper validation.

**Risk:**
- Insecure Direct Object Reference (IDOR) vulnerabilities
- Users might access other workspaces' data

**Current Code:**
```python
workspace = int(workspace)  # Line 94 in rule_views.py
```

**Fix:**
```python
try:
    workspace_id = int(workspace)
    # Validate workspace exists
    workspace_obj = Workspace.objects.get(id=workspace_id)
    # Validate user has access
    if not user.is_superuser and not user.has_workspace_access(workspace_id):
        raise PermissionDenied("Access denied to workspace")
except (ValueError, TypeError):
    return Response({'error': 'Invalid workspace ID'}, status=400)
except Workspace.DoesNotExist:
    return Response({'error': 'Workspace not found'}, status=404)
```

---

### 7. Broad Exception Catching Hides Security Issues
**Severity:** HIGH
**File:** `users/authentication.py:43`
**Issue:** Catches all exceptions silently in authentication flow.

```python
except Exception:
    # Return None for any authentication failures
    return None
```

**Risk:**
- Security exceptions (invalid tokens, tampering) are hidden
- Makes debugging and security monitoring difficult
- No logging of authentication failures

**Fix:**
```python
except InvalidToken as e:
    logger.warning(f"Invalid JWT token: {e}")
    return None
except Exception as e:
    logger.error(f"Unexpected authentication error: {e}")
    return None
```

---

### 8. Inconsistent Error Handling Across API Endpoints
**Severity:** HIGH
**Files:** Multiple view files
**Example:** `rule_views.py:173-177`, `dimension_views.py:448-452`

**Issue:** Some endpoints catch and handle exceptions, others let them bubble up inconsistently.

**Risk:**
- Information leakage in error messages
- Inconsistent API behavior
- Stack traces exposed to clients in some cases

**Fix:**
Create centralized exception handler:
```python
# In settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'master_data.utils.custom_exception_handler'
}
```

---

### 9. Poor Type Safety Coverage
**Severity:** HIGH
**Files:** Across entire codebase
**Statistics:** Only 156 functions with type hints out of 688 total (23% coverage)

**Issue:** Missing type hints in critical code:
- Service layer functions
- View methods
- Serializer methods
- Model methods

**Risk:**
- Runtime type errors
- Difficult to maintain and refactor
- IDE/tooling cannot catch bugs early

**Fix:**
Add type hints systematically, starting with:
```python
# Example from services/propagation_service.py
def propagate_changes(
    dimension_value_id: int,
    workspace_id: int
) -> Dict[str, Any]:
    ...
```

---

### 10. No Validation of File Upload Sizes
**Severity:** HIGH
**Files:** Serializers accepting file uploads
**Issue:** No max size limits on file fields.

**Risk:**
- DoS via large file uploads
- Disk space exhaustion
- Memory exhaustion

**Fix:**
```python
# In settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

---

### 11. Database Connection String Logging in Production
**Severity:** HIGH
**File:** `main/production_settings.py:456-463`
**Issue:** Django DB backend logging set to DEBUG in production when RAILWAY_DEPLOYMENT_ID is set.

**Risk:**
- Database passwords could be logged
- Connection strings exposed in logs

**Fix:**
```python
'django.db.backends': {
    'handlers': ['console'],
    'level': 'WARNING',  # Never DEBUG in production
    'propagate': False,
},
```

---

## 🟡 MEDIUM SEVERITY ISSUES

### 12. Inconsistent Naming Conventions
**Severity:** MEDIUM
**Files:** `master_data/views/`
**Issue:** Inconsistent mixin usage:
- Some use `WorkspaceMixin` (dimension_views.py:79)
- Others use `WorkspaceValidationMixin` (string_views.py:43)

**Fix:** Standardize on one mixin name and consolidate duplicate code.

---

### 13. AUTH_COOKIE_SECURE Environment Variable Parsing
**Severity:** MEDIUM
**File:** `main/local_settings.py:305`
**Issue:** `AUTH_COOKIE_SECURE = getenv("AUTH_COOKIE_SECURE", "True") == "True"`

**Risk:** Any value except exactly "True" becomes False, including typos.

**Fix:**
```python
AUTH_COOKIE_SECURE = getenv("AUTH_COOKIE_SECURE", "True").lower() in ('true', '1', 'yes')
```

---

### 14. No Pagination Limits Enforced
**Severity:** MEDIUM
**Files:** All ViewSets
**Issue:** No default pagination configured.

**Risk:**
- Large queries can overwhelm database
- Poor API performance

**Fix:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'MAX_PAGE_SIZE': 1000,
}
```

---

### 15. Secret Key Generation Inconsistent in Development
**Severity:** MEDIUM
**File:** `main/local_settings.py:26`
**Issue:** `get_random_secret_key()` generates new key on each startup if env var not set.

**Risk:**
- Sessions invalidated on restart
- JWTs invalidated on restart
- Confusing debugging experience

**Fix:** Document requirement or generate and save to file on first run.

---

### 16. Missing Logging for Security Events
**Severity:** MEDIUM
**Files:** Authentication and authorization code
**Issue:** No logging of:
- Failed login attempts
- Workspace access denials
- Permission errors

**Fix:** Add security event logging:
```python
import logging
security_logger = logging.getLogger('security')

# Log failed auth attempts
security_logger.warning(f"Failed login attempt for user: {email}")
```

---

### 17. No API Versioning Strategy Enforcement
**Severity:** MEDIUM
**File:** `main/settings.py:262-265`
**Issue:** API versioning configured but not enforced on all endpoints.

**Fix:** Ensure all endpoints properly use version prefixes and deprecated versions are handled gracefully.

---

### 18. Thread-Local Storage for Workspace Context
**Severity:** MEDIUM
**File:** `master_data/models/base.py:17-28`
**Issue:** Using thread-local storage for workspace context can lead to issues in async environments.

**Risk:**
- Race conditions in async contexts
- Workspace context leakage between requests
- Difficult to debug

**Fix:** Consider using context managers or request-scoped context instead.

---

### 19. No HSTS Configuration in Production
**Severity:** MEDIUM
**File:** `main/production_settings.py`
**Issue:** Missing HTTP Strict Transport Security headers.

**Fix:**
```python
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

### 20. Duplicate Code in Workspace Access Checks
**Severity:** MEDIUM
**Files:** Multiple ViewSets
**Issue:** Workspace validation logic duplicated across 15+ ViewSets.

**Fix:** Consolidate into single reusable mixin or decorator.

---

### 21. No Content Security Policy Headers
**Severity:** MEDIUM
**Files:** Settings files
**Issue:** No CSP headers configured for API responses.

**Fix:**
```python
# Add django-csp or custom middleware
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
```

---

### 22. Missing Index Optimization
**Severity:** MEDIUM
**Files:** Model files in `master_data/models/`
**Issue:** No database indexes defined on frequently queried foreign keys.

**Fix:** Add indexes:
```python
class Meta:
    indexes = [
        models.Index(fields=['workspace', 'created']),
        models.Index(fields=['workspace', 'status']),
    ]
```

---

### 23. No Request Size Limits
**Severity:** MEDIUM
**Issue:** No limits on request body size.

**Fix:**
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

---

### 24. Password Reset Token Lifetime Not Configured
**Severity:** MEDIUM
**File:** `main/local_settings.py:286-300`
**Issue:** Djoser password reset settings don't specify token lifetime.

**Fix:**
```python
DJOSER = {
    'PASSWORD_RESET_TOKEN_LIFETIME': 3600,  # 1 hour
    ...
}
```

---

### 25. No API Documentation Authentication Test
**Severity:** MEDIUM
**Files:** OpenAPI/Swagger configuration
**Issue:** API docs don't validate authentication is working.

---

### 26. Cache Key Collisions Possible
**Severity:** MEDIUM
**File:** Cache key generation in services
**Issue:** Simple cache key format could cause collisions.

**Fix:** Use namespaced cache keys with versioning.

---

## 🔵 LOW SEVERITY ISSUES

### 27. Inconsistent Docstring Coverage
**Severity:** LOW
**Issue:** Many functions lack docstrings.

---

### 28. Magic Numbers in Code
**Severity:** LOW
**Example:** Hardcoded timeouts, page sizes, etc.

---

### 29. No Pre-commit Hooks Configured
**Severity:** LOW
**Issue:** No automated code quality checks before commit.

---

### 30. Missing .editorconfig
**Severity:** LOW
**Issue:** No editor configuration for consistent formatting.

---

## ✅ POSITIVE FINDINGS

1. **No SQL Injection Vulnerabilities:** Django ORM used correctly throughout
2. **Environment Variables Secure:** .env.local properly gitignored
3. **Dependencies Up-to-Date:** urllib3 1.26.20 has latest security patches
4. **Password Hashing:** Using Django's secure password hashers
5. **CSRF Protection:** Enabled in production
6. **SSL/TLS:** Properly configured for production (Railway)
7. **Atomic Transactions:** Using `@transaction.atomic` appropriately
8. **Model-Level Validation:** Good use of model constraints

---

## 📊 STATISTICS

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test Files | 8 | 40+ | 🔴 |
| Test Coverage | Unknown (~10% est.) | >80% | 🔴 |
| Type Hint Coverage | 23% | >90% | 🔴 |
| ViewSets | 19 | - | - |
| Services | 12 | - | - |
| Models | 12 | - | - |
| Lines of Code | 13,420 | - | - |
| Security Vulns (High) | 11 | 0 | 🟡 |
| Security Vulns (Critical) | 0 | 0 | ✅ |

---

## 🎯 PRIORITY RECOMMENDATIONS

### Immediate (This Week)
1. ✅ Fix CORS_ALLOW_ALL_ORIGINS in local_settings.py
2. ✅ Enable CSRF_COOKIE_HTTPONLY
3. ✅ Add API rate limiting
4. ✅ Remove exec() from test script
5. ✅ Fix database logging level in production

### Short-term (This Month)
1. Add comprehensive test suite (target: 80% coverage)
2. Add type hints to all service layer functions
3. Consolidate workspace validation logic
4. Add security event logging
5. Fix inconsistent error handling

### Long-term (This Quarter)
1. Implement full type safety (mypy strict mode)
2. Add API integration tests
3. Set up continuous security scanning
4. Implement API versioning strategy fully
5. Add performance monitoring

---

## 🛠️ RECOMMENDED TOOLS

1. **Security:** `bandit`, `safety`, `pip-audit`
2. **Type Checking:** `mypy` with strict mode
3. **Testing:** `pytest`, `pytest-cov`, `pytest-django`
4. **Code Quality:** `pylint`, `flake8`, `black`
5. **Pre-commit:** `pre-commit` framework
6. **API Testing:** `tavern` or `pytest-rest`

---

## 📝 CONCLUSION

The tux-backend codebase demonstrates good security fundamentals (no SQL injection, proper ORM usage, environment variable handling) but has significant gaps in defense-in-depth measures, particularly around test coverage, type safety, and API hardening. Addressing the 11 HIGH severity issues should be the immediate priority, followed by systematic improvement of test coverage and type safety.

**Overall Risk Rating:** MEDIUM-HIGH
**Recommended Action:** Address all HIGH severity issues within 2 weeks
