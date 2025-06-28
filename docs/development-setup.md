# Development Setup & Testing

## CORS Configuration

The TUX Backend is configured to support cross-origin requests from frontend applications running on different ports.

### Development CORS Settings

For development environments, the following origins are automatically allowed:

- `http://localhost:3000` (React/Next.js default)
- `http://127.0.0.1:3000`
- `http://localhost:8000` (Django development server)
- `http://127.0.0.1:8000`

### Supported CORS Methods

- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`

### Supported CORS Headers

- `accept`, `accept-encoding`, `authorization`, `content-type`
- `dnt`, `origin`, `user-agent`, `x-csrftoken`, `x-requested-with`

### CORS Configuration for Frontend

When making requests from your frontend application (e.g., React app on localhost:3000), you can:

1. **Make direct API calls** to `http://localhost:8000/api/v1/`
2. **Include authentication headers** without CORS issues
3. **Use credentials** in requests (`credentials: 'include'`)

**Example JavaScript fetch:**

```javascript
// Health check request
const response = await fetch("http://localhost:8000/api/v1/health/", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
  },
});

// Authenticated request
const response = await fetch("http://localhost:8000/api/v1/workspaces/", {
  method: "GET",
  headers: {
    "Content-Type": "application/json",
    Authorization: "Bearer your-jwt-token",
  },
  credentials: "include",
});
```

## CSRF Protection

For development environments, CSRF protection is configured to work with frontend applications:

### CSRF Trusted Origins

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8000`
- `http://127.0.0.1:8000`

### CSRF Settings

- **CSRF_COOKIE_SECURE**: `False` (allows non-HTTPS in development)
- **CSRF_COOKIE_HTTPONLY**: `False` (allows JavaScript access)
- **CSRF_COOKIE_SAMESITE**: `'Lax'` (permissive for development)

## Environment Configuration

### Development vs Production

| Setting                | Development            | Production    |
| ---------------------- | ---------------------- | ------------- |
| CORS_ALLOW_ALL_ORIGINS | `True`                 | `False`       |
| CORS_ALLOW_CREDENTIALS | `True`                 | `True`        |
| CSRF_COOKIE_SECURE     | `False`                | `True`        |
| DEBUG                  | `True`                 | `False`       |
| Workspace Middleware   | Bypassed for localhost | Always active |

### Environment Variables

#### Production Environment

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost/tux_db
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=client1.yourdomain.com,client2.yourdomain.com

# CORS Configuration (Production)
CORS_ALLOWED_ORIGINS=https://client1.yourdomain.com,https://client2.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://client1.yourdomain.com,https://client2.yourdomain.com

# Optional
DEBUG=False
CACHE_URL=redis://localhost:6379/1
```

#### Development Environment

```bash
# Required for development
SECRET_KEY=django-insecure-development-key-only
ALLOWED_HOSTS=localhost,127.0.0.1

# Development flags
DEBUG=True

# CORS automatically configured for:
# - http://localhost:3000 (frontend)
# - http://localhost:8000 (API)
# - http://127.0.0.1:3000
# - http://127.0.0.1:8000

# Database (SQLite for development)
# DATABASE_URL not required (uses sqlite3 by default)

# Optional development settings
AUTH_COOKIE_SECURE=False  # Allow non-HTTPS cookies
```

#### Development vs Production Differences

| Setting                  | Development                                  | Production                   |
| ------------------------ | -------------------------------------------- | ---------------------------- |
| **CORS**                 | Allow all origins + specific localhost ports | Specific domain origins only |
| **CSRF**                 | Non-secure cookies, JavaScript access        | Secure cookies, HTTP-only    |
| **DEBUG**                | `True`                                       | `False`                      |
| **Database**             | SQLite (file-based)                          | PostgreSQL (DATABASE_URL)    |
| **Workspace Middleware** | Bypassed for localhost                       | Always active                |
| **SSL/HTTPS**            | Not required                                 | Required (secure cookies)    |

## Testing

### Development Environment Testing

#### Localhost Testing (Recommended for Frontend Development)

Test API endpoints directly via localhost without subdomain requirements:

```bash
# Test health endpoint (no auth required)
curl http://localhost:8000/api/v1/health/

# Test version endpoint (no auth required)
curl http://localhost:8000/api/v1/version/

# Test protected endpoint (auth required)
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/api/v1/workspaces/

# Test CORS preflight request
curl -X OPTIONS \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: authorization,content-type" \
     http://localhost:8000/api/v1/workspaces/
```

#### Frontend Integration Testing

Test CORS and frontend connectivity from your frontend application:

```javascript
// Test health endpoint connectivity
async function testHealth() {
  try {
    const response = await fetch("http://localhost:8000/api/v1/health/");
    const data = await response.json();
    console.log("Health check:", data.status);
  } catch (error) {
    console.error("Network error:", error.message);
  }
}

// Test authenticated endpoint
async function testAuth() {
  try {
    const response = await fetch("http://localhost:8000/api/v1/workspaces/", {
      headers: {
        Authorization: "Bearer your-jwt-token",
        "Content-Type": "application/json",
      },
    });

    if (response.status === 401) {
      console.log("Endpoint accessible, authentication required");
    } else if (response.ok) {
      console.log("Authenticated request successful");
    }
  } catch (error) {
    console.error("Network/CORS error:", error.message);
  }
}
```

### Workspace Access Testing

#### Testing Multi-Workspace Access

Test workspace access and filtering with user authentication:

```bash
# Test workspace listing (shows user's accessible workspaces)
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/api/v1/workspaces/

# Test workspace-filtered data (dimensions, rules, etc.)
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/api/v1/dimensions/

# Test user workspace assignments
curl -H "Authorization: Bearer your-jwt-token" \
     http://localhost:8000/api/v1/workspace-users/
```

#### Legacy Subdomain Testing (Optional)

For testing legacy subdomain-based workspace detection:

```bash
# Test subdomain-based workspace detection (if enabled)
curl -H "Authorization: Bearer abc123" \
     http://client1.localhost:8000/api/v1/workspaces/

curl -H "Authorization: Bearer abc123" \
     http://client2.localhost:8000/api/v1/workspaces/
```

#### Test Workspaces

Development environments support flexible workspace testing:

- **Direct API Access**: `localhost:8000` - Access via user authentication
- **Legacy Subdomain** (Optional): `client1.localhost:8000` - Subdomain-based access
- **Admin Panel**: `localhost:8000/admin/` - Full workspace management

### CORS Testing

Verify CORS configuration is working properly:

```bash
# Test CORS headers in response
curl -H "Origin: http://localhost:3000" \
     http://localhost:8000/api/v1/health/ -I

# Expected CORS headers in response:
# access-control-allow-origin: http://localhost:3000
# access-control-allow-credentials: true
# access-control-allow-methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
```

### Common Testing Scenarios

#### ✅ Expected Behaviors

1. **Health/Version endpoints**: Return 200 OK with JSON data
2. **Protected endpoints without auth**: Return 401 Unauthorized
3. **CORS preflight requests**: Return 200 OK with proper headers
4. **Frontend requests**: No network errors, proper HTTP status codes

#### ❌ Troubleshooting Issues

1. **"Network error - API server may be unreachable"**

   - Check CORS configuration
   - Verify frontend is on `localhost:3000`
   - Use primary API endpoint: `localhost:8000/api/v1/`

2. **404 Not Found**

   - Check API URL path (`/api/v1/endpoint/`)
   - Verify endpoint exists in documentation

3. **403 Forbidden**

   - Check workspace access permissions
   - Verify user has proper workspace assignments
   - Ensure user has required role (admin/user/viewer) for the operation

4. **Empty Results**
   - User may not have access to any workspaces
   - Check user's workspace assignments via `/api/v1/workspace-users/`
   - Verify workspaces are active

## Database Migrations

### For New Deployments

```bash
# Run migrations (clean migrations)
python manage.py migrate

# Create initial workspace
python manage.py create_workspace "Client 1" --admin-email admin@client1.com
```

**Note**: The migrations have been squashed for clean deployments. New instances will use the optimized `0001_initial.py` migration that represents the final state of all model changes.

## Admin Panel Setup

### Creating Superuser

```bash
# Create admin user for development
python manage.py createsuperuser
# Email: admin@example.com
# Password: admin123 (development only)
```

### Admin Panel Access

- **URL**: `http://localhost:8000/admin/`
- **Features**: Complete user and workspace management
- **Demo Data**: Create test workspaces and users for development

## SDKs & Integration

### JavaScript/TypeScript SDK

```javascript
import { TuxAPI } from "@tux/api-client";

const api = new TuxAPI({
  baseURL: "http://localhost:8000/api/v1/",
  token: "your-auth-token",
});

// Get workspaces
const workspaces = await api.workspaces.list();

// Create platform
const platform = await api.platforms.create({
  name: "Snowflake",
  description: "Data warehouse platform",
});
```

### Python SDK

```python
from tux_api import TuxClient

client = TuxClient(
    base_url='http://localhost:8000/api/v1/',
    token='your-auth-token'
)

# Get dimensions
dimensions = client.dimensions.list()

# Generate string
string = client.strings.generate(
    submission_id=1,
    field_id=1,
    dimension_values={'environment': 'prod'}
)
```

---

_Last Updated: 2025-06-08_
_Environment: Development Ready_
