# Issue #6: Rate Limiting Implementation

## Overview
Implemented comprehensive rate limiting and security measures for authentication endpoints to prevent brute force attacks and credential stuffing, addressing GitHub issue #6.

## Files Created/Modified

### 1. New Files Created

#### `users/throttles.py`
Custom throttle classes for authentication endpoints:
- **AuthenticationThrottle**: 5 attempts per minute for login endpoint
- **TokenRefreshThrottle**: 10 attempts per minute for token refresh
- **RegistrationThrottle**: 3 attempts per hour for registration
- **LoginAttemptThrottle**: Granular rate limiting by IP + email combination

### 2. Modified Files

#### `users/views.py`
Enhanced authentication views with:
- **Rate Limiting**: Applied throttle classes to login and token refresh endpoints
- **Failed Login Tracking**: Tracks failed attempts per email and IP address
- **Account Lockout**: Locks accounts after 5 failed attempts (15-minute lockout)
- **IP-based Protection**: Prevents distributed attacks with IP-level rate limiting
- **Security Logging**: Comprehensive logging of login attempts, successes, and failures
- **Automatic Cleanup**: Clears failed attempt counters on successful login

#### `main/local_settings.py`
Added DRF throttling configuration:
```python
'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
],
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'auth': '5/minute',
    'token_refresh': '10/minute',
    'registration': '3/hour',
    'login_attempt': '5/minute',
}
```

Added security logging configuration with dedicated security logger.

#### `main/production_settings.py`
Same throttling and logging configuration as local settings for production environment.

#### `users/tests.py`
Comprehensive test suite with 13 tests covering:
- Login rate limiting
- Account lockout after failed attempts
- Failed attempt counter management
- IP-based rate limiting
- Token refresh rate limiting
- Security logging functionality
- Throttle class configuration

## Security Features Implemented

### 1. Rate Limiting
- **Login Endpoint**: 5 attempts per minute per IP
- **Token Refresh**: 10 attempts per minute
- **Registration**: 3 attempts per hour (ready for future use)

### 2. Account Lockout
- **Trigger**: 5 failed login attempts per email
- **Duration**: 15 minutes
- **IP Lockout**: 10 failed attempts per IP (1 hour)
- **Auto-reset**: Counters clear on successful login

### 3. Security Logging
- **Successful Logins**: Logs email and IP address
- **Failed Attempts**: Logs email, IP, and reason
- **Errors**: Logs authentication errors with context
- **Dedicated Logger**: Separate 'security' logger for easy monitoring

### 4. Attack Prevention
- **Brute Force**: Rate limiting prevents rapid password guessing
- **Credential Stuffing**: Account lockout limits attempts per user
- **Distributed Attacks**: IP-based limiting prevents attacks from multiple sources
- **Account Enumeration**: Consistent error messages

## Implementation Details

### Cache Usage
- Uses Django's cache framework for tracking failed attempts
- Keys: `failed_login_{email}` and `failed_login_ip_{ip_address}`
- Automatic expiration: 15 minutes (email), 1 hour (IP)

### Response Codes
- **429 Too Many Requests**: Rate limit exceeded
- **400 Bad Request**: Account locked or validation error
- **401 Unauthorized**: Invalid credentials

### Client IP Detection
Properly handles proxy headers (X-Forwarded-For) for accurate IP detection behind load balancers or proxies.

## Testing
All 13 tests pass successfully:
- ✅ test_authentication_throttle_rate
- ✅ test_registration_throttle_rate
- ✅ test_token_refresh_throttle_rate
- ✅ test_login_rate_limiting
- ✅ test_account_lockout_after_failed_attempts
- ✅ test_successful_login_clears_failed_attempts
- ✅ test_ip_based_rate_limiting
- ✅ test_token_refresh_rate_limiting
- ✅ test_failed_attempt_counter_increments
- ✅ test_failed_attempt_counter_clears_on_success
- ✅ test_account_lockout_message
- ✅ test_successful_login_is_logged
- ✅ test_failed_login_is_logged

## Usage

### For Developers
No changes needed to existing client code. Rate limiting is transparent and returns standard HTTP status codes.

### For Operations
Monitor security logs for:
- Repeated failed login attempts (potential attacks)
- Account lockouts
- Unusual patterns in login attempts

### Rate Limit Headers
DRF throttling automatically includes headers in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds until rate limit resets (on 429 responses)

## Benefits
1. **Security**: Significantly reduces risk of brute force attacks
2. **Account Protection**: Automatic lockout prevents unauthorized access
3. **Visibility**: Comprehensive logging enables security monitoring
4. **Performance**: Prevents resource exhaustion from attack attempts
5. **Compliance**: Implements security best practices (OWASP recommendations)

## Future Enhancements (Optional)
- [ ] CAPTCHA after 3 failed attempts
- [ ] Email notifications for account lockouts
- [ ] Dashboard for security monitoring
- [ ] IP whitelist/blacklist management
- [ ] Adaptive rate limiting based on user behavior

## References
- OWASP: Brute Force Attacks
- CWE-307: Improper Restriction of Excessive Authentication Attempts
- Django REST Framework Throttling Documentation
- GitHub Issue #6
