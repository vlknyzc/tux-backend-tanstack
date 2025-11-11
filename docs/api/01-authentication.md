# Authentication API

Authentication in Tuxonomy uses **JWT (JSON Web Tokens)** for secure API access.

---

## Endpoints

### 1. Login (Get Token)

**POST** `/api/v1/token/`

Authenticate user and receive access and refresh tokens.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "workspaces": [
      {
        "id": 1,
        "name": "ACME Corp",
        "slug": "acme-corp",
        "role": "admin"
      }
    ]
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "No active account found with the given credentials"
}
```

**Token Lifetime**:
- Access Token: 60 minutes
- Refresh Token: 24 hours

---

### 2. Refresh Token

**POST** `/api/v1/token/refresh/`

Get a new access token using a refresh token.

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 3. Verify Token

**POST** `/api/v1/token/verify/`

Check if a token is valid.

**Request**:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

## Using Tokens in Requests

### Authorization Header

Include the access token in all API requests:

```http
GET /api/v1/workspaces/1/projects/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Example with cURL

```bash
curl -X GET \
  'http://localhost:8000/api/v1/workspaces/1/projects/' \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...' \
  -H 'Content-Type: application/json'
```

### Example with JavaScript (Fetch)

```javascript
const response = await fetch('http://localhost:8000/api/v1/workspaces/1/projects/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

const projects = await response.json();
```

### Example with Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

const projects = await api.get('/workspaces/1/projects/');
```

---

## Token Refresh Strategy

Implement automatic token refresh in your frontend:

```javascript
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

async function refreshAccessToken() {
  const response = await fetch('http://localhost:8000/api/v1/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });

  if (response.ok) {
    const data = await response.json();
    accessToken = data.access;
    localStorage.setItem('access_token', accessToken);
    return accessToken;
  } else {
    // Refresh token expired - redirect to login
    window.location.href = '/login';
  }
}

// Axios interceptor example
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const newToken = await refreshAccessToken();
      originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
      return api(originalRequest);
    }

    return Promise.reject(error);
  }
);
```

---

## Security Best Practices

### 1. Token Storage

**Browser**:
- Store tokens in `localStorage` or `sessionStorage`
- Never store tokens in cookies without HttpOnly flag
- Consider using memory-only storage for high-security apps

**Mobile**:
- Use secure storage (Keychain/KeyStore)
- Never store in plain SharedPreferences/UserDefaults

### 2. Token Transmission

- Always use HTTPS in production
- Never send tokens in URL parameters
- Always use Authorization header

### 3. Token Expiration

- Access tokens expire in 60 minutes
- Implement automatic refresh before expiration
- Handle 401 errors gracefully

### 4. Logout

Clear tokens on logout:

```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  // Redirect to login
  window.location.href = '/login';
}
```

---

## Error Handling

### Common Authentication Errors

| Status | Error | Meaning | Action |
|--------|-------|---------|--------|
| 401 | `Token is invalid or expired` | Access token expired | Refresh token |
| 401 | `No active account found` | Wrong credentials | Show error to user |
| 401 | `Token has been revoked` | User logged out server-side | Redirect to login |
| 400 | `Email is required` | Missing field | Show validation error |

### Example Error Handler

```javascript
async function handleAuthError(error) {
  if (error.response?.status === 401) {
    const errorCode = error.response.data?.code;

    if (errorCode === 'token_not_valid') {
      // Try to refresh token
      try {
        await refreshAccessToken();
        // Retry original request
        return true;
      } catch (refreshError) {
        // Redirect to login
        logout();
        return false;
      }
    } else {
      // Invalid credentials or other auth error
      showError('Authentication failed. Please check your credentials.');
      return false;
    }
  }
}
```

---

## Rate Limiting

Authentication endpoints are rate-limited:

- **Login**: 10 requests per minute per IP
- **Refresh**: 20 requests per minute per user
- **Verify**: 100 requests per minute per user

**Rate Limit Response** (429):
```json
{
  "detail": "Request was throttled. Expected available in 45 seconds."
}
```

---

## Testing Authentication

### Get Token

```bash
curl -X POST http://localhost:8000/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```

### Use Token

```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X GET http://localhost:8000/api/v1/workspaces/ \
  -H "Authorization: Bearer $TOKEN"
```

### Refresh Token

```bash
REFRESH="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:8000/api/v1/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}"
```
