# TUX Backend - API Documentation (Legacy)

**📢 Notice**: This documentation has been split into multiple files for better organization. Please refer to the individual API documentation files for detailed information:

- **[Main Documentation Index](README.md)** - Complete documentation structure
- **[API Overview](api-overview.md)** - Authentication, multi-tenancy, versioning
- **[Development Setup](development-setup.md)** - CORS, environment setup, testing
- **[Migration Guide](migration-guide.md)** - Subdomain to flexible workspace migration
- **[User Management API](api-users.md)** - User accounts and workspace assignments
- **[Workspace Management API](api-workspaces.md)** - Workspace management and settings

## Quick Reference

### Base URLs

- **Development**: `http://localhost:8000/api/v1/`
- **Production**: `https://yourdomain.com/api/v1/`

### Authentication

All endpoints require authentication via JWT tokens or session authentication:

```
Authorization: Bearer your-jwt-token
```

## Multi-Tenancy

### Workspace Context

The TUX Backend implements flexible workspace access that supports multiple deployment models:

- **User-Based Access**: Users are assigned to specific workspaces through workspace assignments
- **Role-Based Permissions**: Each workspace assignment includes a role (admin, user, viewer)
- **API-Driven Selection**: Workspaces can be selected via API parameters or authentication context
- **Legacy Subdomain Support**: Optional subdomain routing for backwards compatibility

### Access Control

- **Regular Users**: Can only access workspaces they're explicitly assigned to
- **Superusers**: Can access all workspaces across the entire system
- **Workspace Roles**:
  - `admin` - Full management access within the workspace
  - `user` - Read/write access to workspace data
  - `viewer` - Read-only access to workspace data

### Workspace Selection

The system provides multiple ways to specify workspace context:

1. **Authentication Context**: User's default or available workspaces
2. **API Parameters**: Workspace selection via query parameters or request headers
3. **Subdomain Routing** (Optional): `client1.yourdomain.com` for backwards compatibility
4. **Direct Access**: Explicit workspace specification in API calls

**Note**: The system no longer requires subdomain-based routing and supports direct API access with workspace context provided through user authentication and explicit workspace selection.

## API Versioning

The TUX Backend API uses URL path versioning to manage different API versions. This ensures backward compatibility while allowing for future enhancements.

### Supported Versions

- **v1**: Current stable version with all documented features
- **v2**: Future version (planned) with enhanced features and optimizations

### Version Detection

The API version is specified in the URL path:

- **Versioned**: `/api/v1/endpoint/` (recommended)
- **Legacy**: `/api/endpoint/` (defaults to v1, maintained for backward compatibility)

## Base URLs

### Production

- **Primary API**: `https://yourdomain.com/api/v1/`
- **Legacy**: `https://yourdomain.com/api/`
- **Subdomain Support** (Optional): `https://client1.yourdomain.com/api/v1/`

### Development

- **Primary API (Recommended)**: `http://localhost:8000/api/v1/`
- **Legacy**: `http://localhost:8000/api/`
- **Subdomain Testing** (Optional): `http://client1.localhost:8000/api/v1/`

### Workspace Access Methods

1. **Direct API Access** (Recommended):

   - Use primary API endpoint with authentication
   - Workspace context determined by user permissions
   - Frontend can list and select available workspaces

2. **Subdomain Access** (Legacy/Optional):
   - Maintains backwards compatibility
   - Automatic workspace detection from subdomain
   - Useful for existing deployments

**Note**: The system supports both direct API access (recommended for new implementations) and optional subdomain routing (for backwards compatibility). When using direct API access, workspace context is managed through user authentication and explicit workspace selection rather than subdomain detection.

## Migration from Subdomain-Based Access

### For Existing Applications

If you're migrating from a subdomain-based implementation:

1. **Update API Base URLs**:

   - **Old**: `https://client1.yourdomain.com/api/v1/`
   - **New**: `https://yourdomain.com/api/v1/`

2. **Implement Workspace Selection**:

   - Add workspace listing via `/api/v1/workspaces/`
   - Add workspace switcher in your frontend
   - Store selected workspace in application state

3. **Update Authentication Flow**:

   - Users authenticate once for all accessible workspaces
   - Frontend manages workspace context switching
   - API automatically filters data based on user permissions

4. **Optional**: Keep subdomain support for backwards compatibility during transition

### Frontend Implementation Example

```javascript
// 1. Get user's accessible workspaces after authentication
async function loadWorkspaces() {
  const response = await fetch("/api/v1/workspaces/", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
}

// 2. User can switch between workspaces
function selectWorkspace(workspaceId) {
  // Store in app state, localStorage, etc.
  setCurrentWorkspace(workspaceId);
  // Reload workspace-specific data
  loadWorkspaceData();
}

// 3. API calls work with any accessible workspace
async function loadDimensions() {
  const response = await fetch("/api/v1/dimensions/", {
    headers: { Authorization: `Bearer ${token}` },
  });
  // Response automatically filtered by user's workspace access
  return response.json();
}
```

## Workspace Access & Context

### How Workspace Access Works

1. **User Authentication**: Users authenticate with the API using JWT tokens or session authentication
2. **Workspace Discovery**: Authenticated users can list their accessible workspaces via `/api/v1/workspaces/`
3. **Context Selection**: Frontend applications can switch between workspaces as needed
4. **Data Filtering**: API automatically filters data based on user's workspace permissions

### API Workspace Context

#### Listing Available Workspaces

```http
GET /api/v1/workspaces/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Client A Workspace",
      "status": "active",
      "description": "Main workspace for Client A"
    },
    {
      "id": 2,
      "name": "Client B Workspace",
      "status": "active",
      "description": "Main workspace for Client B"
    }
  ]
}
```

#### Workspace-Specific Data Access

When accessing workspace-specific endpoints, the API automatically filters data based on:

1. **User's workspace assignments**: Only workspaces the user has access to
2. **User's role in each workspace**: admin, user, or viewer permissions
3. **Superuser status**: Superusers can access all workspaces

**Example - Getting dimensions for accessible workspaces:**

```http
GET /api/v1/dimensions/
Authorization: Bearer your-jwt-token
```

The response will only include dimensions from workspaces the user has access to.

#### Multi-Workspace Operations

For users with access to multiple workspaces, you can:

1. **Filter by workspace**: Use query parameters where supported
2. **Switch context**: Frontend manages workspace selection
3. **Batch operations**: Some endpoints support cross-workspace operations for superusers

## Development Setup & CORS Configuration

### Cross-Origin Resource Sharing (CORS)

The TUX Backend is configured to support cross-origin requests from frontend applications running on different ports.

#### Development CORS Settings

For development environments, the following origins are automatically allowed:

- `http://localhost:3000` (React/Next.js default)
- `http://127.0.0.1:3000`
- `http://localhost:8000` (Django development server)
- `http://127.0.0.1:8000`

#### Supported CORS Methods

- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`

#### Supported CORS Headers

- `accept`, `accept-encoding`, `authorization`, `content-type`
- `dnt`, `origin`, `user-agent`, `x-csrftoken`, `x-requested-with`

#### CORS Configuration for Frontend

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

### CSRF Protection

For development environments, CSRF protection is configured to work with frontend applications:

#### CSRF Trusted Origins

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8000`
- `http://127.0.0.1:8000`

#### CSRF Settings

- **CSRF_COOKIE_SECURE**: `False` (allows non-HTTPS in development)
- **CSRF_COOKIE_HTTPONLY**: `False` (allows JavaScript access)
- **CSRF_COOKIE_SAMESITE**: `'Lax'` (permissive for development)

### Development vs Production

| Setting                | Development            | Production    |
| ---------------------- | ---------------------- | ------------- |
| CORS_ALLOW_ALL_ORIGINS | `True`                 | `False`       |
| CORS_ALLOW_CREDENTIALS | `True`                 | `True`        |
| CSRF_COOKIE_SECURE     | `False`                | `True`        |
| DEBUG                  | `True`                 | `False`       |
| Workspace Middleware   | Bypassed for localhost | Always active |

### Troubleshooting CORS Issues

If you encounter CORS errors:

1. **Check the origin**: Ensure your frontend is running on `localhost:3000`
2. **Verify API URL**: Use `http://localhost:8000/api/v1/` (primary API endpoint)
3. **Check headers**: Ensure proper `Content-Type` and `Authorization` headers
4. **Network errors**: CORS issues manifest as network errors in browsers

**Common Error Resolution:**

- ❌ **"Network error - API server may be unreachable"**
- ✅ **Should see proper HTTP status codes (200, 401, 403, etc.)**

## Version Management

### API Version Information

Get information about the current API version and available features.

#### Get Version Information

```http
GET /api/v1/version/
```

**Response (v1):**

```json
{
  "version": "v1",
  "message": "Welcome to TUX Backend API v1",
  "features": [
    "Multi-tenant workspace support",
    "Basic string generation",
    "Rule management",
    "Field hierarchy support"
  ],
  "deprecated_features": [],
  "breaking_changes": []
}
```

**Response (v2):**

```json
{
  "version": "v2",
  "message": "Welcome to TUX Backend API v2",
  "features": [
    "Enhanced multi-tenant workspace support",
    "Advanced string generation with AI",
    "Advanced rule management with validation",
    "Complex field hierarchy support",
    "Real-time collaboration features",
    "Advanced caching and performance optimizations"
  ],
  "deprecated_features": [
    "Legacy string generation endpoints",
    "Simple rule validation"
  ],
  "breaking_changes": [
    "Modified response format for string generation",
    "Enhanced workspace access control",
    "New required fields in rule creation"
  ]
}
```

#### Health Check

```http
GET /api/v1/health/
```

**Response:**

```json
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2024-01-01T00:00:00Z",
  "database": "connected",
  "cache": "operational",
  "workspace_detection": "active"
}
```

## Core Endpoints

### 1. User Management

Manage users and their workspace assignments. User management is restricted based on roles:

- **Superusers**: Can manage all users and assignments
- **Workspace Admins**: Can manage users within their workspaces
- **Regular Users**: Can view users in their workspaces and update their own profile

#### List Users

```http
GET /api/v1/users/
```

**Query Parameters:**

- `is_active`: Filter by active status (true/false)
- `is_staff`: Filter by staff status (true/false)
- `is_superuser`: Filter by superuser status (true/false)

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User",
      "full_name": "Admin User",
      "is_active": true,
      "is_staff": true,
      "is_superuser": true,
      "last_login": "2024-01-01T12:00:00Z",
      "workspace_count": 3,
      "primary_role": "superuser"
    },
    {
      "id": 2,
      "email": "john.doe@client1.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "is_active": true,
      "is_staff": false,
      "is_superuser": false,
      "last_login": "2024-01-01T10:30:00Z",
      "workspace_count": 2,
      "primary_role": "admin"
    }
  ]
}
```

#### Get User Details

```http
GET /api/v1/users/{user_id}/
```

**Response:**

```json
{
  "id": 2,
  "email": "john.doe@client1.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "last_login": "2024-01-01T10:30:00Z",
  "date_joined": "2023-12-01T09:00:00Z",
  "workspace_assignments": [
    {
      "id": 1,
      "workspace_id": 1,
      "workspace_name": "Client 1",
      "role": "admin",
      "is_active": true,
      "created": "2023-12-01T09:15:00Z",
      "updated": "2023-12-01T09:15:00Z"
    },
    {
      "id": 2,
      "workspace_id": 2,
      "workspace_name": "Client 2",
      "role": "user",
      "is_active": true,
      "created": "2023-12-15T14:30:00Z",
      "updated": "2023-12-15T14:30:00Z"
    }
  ],
  "accessible_workspaces_count": 2
}
```

#### Create User (Superuser Only)

```http
POST /api/v1/users/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false
}
```

**Response (201 Created):**

```json
{
  "id": 5,
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "full_name": "New User",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "last_login": null,
  "workspace_count": 0,
  "primary_role": "user"
}
```

#### Update User (Partial Update)

```http
PATCH /api/v1/users/{user_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "Name",
  "is_active": true
}
```

**Response (200 OK):**

```json
{
  "id": 2,
  "email": "john.doe@client1.com",
  "first_name": "Updated",
  "last_name": "Name",
  "full_name": "Updated Name",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "last_login": "2024-01-01T10:30:00Z",
  "workspace_count": 2,
  "primary_role": "admin"
}
```

#### Update User (Full Update)

```http
PUT /api/v1/users/{user_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "email": "john.doe@client1.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false
}
```

**Response (200 OK):** Same format as PATCH response.

#### Delete User (Superuser Only)

```http
DELETE /api/v1/users/{user_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Note**: Deleting a user will also remove all their workspace assignments.

#### Get User Authorizations

```http
GET /api/v1/users/{user_id}/authorizations/
```

**Response:**

```json
{
  "user_id": 2,
  "email": "john.doe@client1.com",
  "full_name": "John Doe",
  "is_superuser": false,
  "is_active": true,
  "workspace_authorizations": [
    {
      "workspace_id": 1,
      "workspace_name": "Client 1",
      "role": "admin",
      "is_active": true,
      "assigned_date": "2023-12-01T09:15:00Z",
      "permissions": ["read", "write", "delete", "manage_users"]
    },
    {
      "workspace_id": 2,
      "workspace_name": "Client 2",
      "role": "user",
      "is_active": true,
      "assigned_date": "2023-12-15T14:30:00Z",
      "permissions": ["read", "write"]
    }
  ],
  "total_workspaces": 2,
  "active_assignments": 2
}
```

#### Get Current User Info

```http
GET /api/v1/users/me/
```

Returns the current authenticated user's information.

### Workspace-User Assignments

Manage user assignments to workspaces and their roles.

#### List Workspace Assignments

```http
GET /api/v1/workspace-users/
```

**Query Parameters:**

- `workspace`: Filter by workspace ID
- `user`: Filter by user ID
- `role`: Filter by role (admin, user, viewer)
- `is_active`: Filter by active status

**Response:**

```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "user": 2,
      "user_email": "john.doe@client1.com",
      "user_name": "John Doe",
      "workspace": 1,
      "workspace_id": 1,
      "workspace_name": "Client 1",
      "role": "admin",
      "is_active": true,
      "created": "2023-12-01T09:15:00Z",
      "updated": "2023-12-01T09:15:00Z"
    }
  ]
}
```

#### Get Workspace Assignment Details

```http
GET /api/v1/workspace-users/{assignment_id}/
Authorization: Bearer your-jwt-token
```

**Response (200 OK):**

```json
{
  "id": 1,
  "user": 2,
  "user_email": "john.doe@client1.com",
  "user_name": "John Doe",
  "workspace": 1,
  "workspace_id": 1,
  "workspace_name": "Client 1",
  "role": "admin",
  "is_active": true,
  "created": "2023-12-01T09:15:00Z",
  "updated": "2023-12-01T09:15:00Z"
}
```

#### Assign User to Workspace

```http
POST /api/v1/workspace-users/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "user": 3,
  "workspace": 1,
  "role": "user",
  "is_active": true
}
```

**Response (201 Created):**

```json
{
  "id": 5,
  "user": 3,
  "user_email": "newuser@example.com",
  "user_name": "New User",
  "workspace": 1,
  "workspace_id": 1,
  "workspace_name": "Client 1",
  "role": "user",
  "is_active": true,
  "created": "2024-01-15T10:30:00Z",
  "updated": "2024-01-15T10:30:00Z"
}
```

#### Update User Role in Workspace (Partial Update)

```http
PATCH /api/v1/workspace-users/{assignment_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "role": "admin",
  "is_active": true
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "user": 2,
  "user_email": "john.doe@client1.com",
  "user_name": "John Doe",
  "workspace": 1,
  "workspace_id": 1,
  "workspace_name": "Client 1",
  "role": "admin",
  "is_active": true,
  "created": "2023-12-01T09:15:00Z",
  "updated": "2024-01-15T11:00:00Z"
}
```

#### Update User Assignment (Full Update)

```http
PUT /api/v1/workspace-users/{assignment_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "user": 2,
  "workspace": 1,
  "role": "admin",
  "is_active": true
}
```

**Response (200 OK):** Same format as PATCH response.

#### Remove User from Workspace

```http
DELETE /api/v1/workspace-users/{assignment_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

#### Bulk Assign Users (Superuser Only)

```http
POST /api/v1/workspace-users/bulk_assign/
Content-Type: application/json

{
  "user_ids": [3, 4, 5],
  "workspace_ids": [1, 2],
  "role": "user"
}
```

**Response:**

```json
{
  "success_count": 6,
  "error_count": 0,
  "assignments": [
    {
      "user_id": 3,
      "workspace_id": 1,
      "role": "user"
    },
    {
      "user_id": 3,
      "workspace_id": 2,
      "role": "user"
    }
  ],
  "errors": []
}
```

#### Workspace Assignment Summary

```http
GET /api/v1/workspace-users/workspace_summary/
```

**Response:**

```json
{
  "workspace_summaries": [
    {
      "workspace__id": 1,
      "workspace__name": "Client 1",
      "total_users": 5,
      "active_users": 4,
      "admin_count": 2,
      "user_count": 2,
      "viewer_count": 1
    },
    {
      "workspace__id": 2,
      "workspace__name": "Client 2",
      "total_users": 3,
      "active_users": 3,
      "admin_count": 1,
      "user_count": 2,
      "viewer_count": 0
    }
  ],
  "total_workspaces": 2
}
```

### 2. Workspaces

Manage client workspaces (admin-only for creation).

#### List Workspaces

```http
GET /api/v1/workspaces/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `status`: Filter by status (active, inactive)
- `search`: Search by name

**Response:**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Client 1",
      "slug": "client-1",
      "status": "active",
      "logo": null,
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z",
      "created_by": 1
    },
    {
      "id": 2,
      "name": "Client 2",
      "slug": "client-2",
      "status": "active",
      "logo": "/media/workspaces/client2-logo.png",
      "created": "2024-01-02T00:00:00Z",
      "last_updated": "2024-01-02T00:00:00Z",
      "created_by": 1
    }
  ]
}
```

#### Get Workspace Details

```http
GET /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "id": 1,
  "name": "Client 1",
  "slug": "client-1",
  "status": "active",
  "logo": null,
  "created": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-01T00:00:00Z",
  "created_by": 1,
  "user_count": 5,
  "active_users": 4
}
```

#### Create Workspace (Superuser Only)

```http
POST /api/v1/workspaces/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "New Client",
  "status": "active"
}
```

**Response (201 Created):**

```json
{
  "id": 3,
  "name": "New Client",
  "slug": "new-client",
  "status": "active",
  "logo": null,
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z",
  "created_by": 1
}
```

#### Update Workspace (Partial Update)

```http
PATCH /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Updated Client Name",
  "status": "active"
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "name": "Updated Client Name",
  "slug": "client-1",
  "status": "active",
  "logo": null,
  "created": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-15T11:00:00Z",
  "created_by": 1
}
```

#### Update Workspace (Full Update)

```http
PUT /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Complete Client Name",
  "status": "active"
}
```

**Response (200 OK):** Same format as PATCH response.

#### Delete Workspace (Superuser Only)

```http
DELETE /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a workspace will also delete all associated data (dimensions, rules, strings, etc.).

### 3. Platforms

Manage data platforms. Platforms are global resources shared across all workspaces.

**Note**: Platforms represent different advertising or data platforms (e.g., Meta, Google Ads, Snowflake). They are shared across all workspaces, allowing consistent platform definitions while maintaining workspace-specific rules and data.

#### List Platforms

```http
GET /api/v1/platforms/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `platform_type`: Filter by platform type
- `name`: Search by platform name
- `search`: General search across name and type

**Response:**

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Snowflake",
      "platform_type": "data_warehouse",
      "slug": "snowflake",
      "icon_name": "snowflake",
      "created_by": null,
      "created_by_name": null,
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "BigQuery",
      "platform_type": "data_warehouse",
      "slug": "bigquery",
      "icon_name": "bigquery",
      "created_by": 1,
      "created_by_name": "Admin User",
      "created": "2024-01-02T00:00:00Z",
      "last_updated": "2024-01-02T00:00:00Z"
    }
  ]
}
```

#### Get Platform Details

```http
GET /api/v1/platforms/{platform_id}/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "id": 1,
  "name": "Snowflake",
  "platform_type": "data_warehouse",
  "slug": "snowflake",
  "icon_name": "snowflake",
  "created_by": null,
  "created_by_name": null,
  "created": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-01T00:00:00Z",
  "field_count": 3
}
```

#### Create Platform

```http
POST /api/v1/platforms/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "BigQuery",
  "platform_type": "data_warehouse",
  "icon_name": "bigquery"
}
```

**Response (201 Created):**

```json
{
  "id": 3,
  "name": "BigQuery",
  "platform_type": "data_warehouse",
  "slug": "bigquery",
  "icon_name": "bigquery",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z"
}
```

#### Update Platform (Partial Update)

```http
PATCH /api/v1/platforms/{platform_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Google BigQuery",
  "icon_name": "google-bigquery"
}
```

**Response (200 OK):**

```json
{
  "id": 2,
  "name": "Google BigQuery",
  "platform_type": "data_warehouse",
  "slug": "bigquery",
  "icon_name": "google-bigquery",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-02T00:00:00Z",
  "last_updated": "2024-01-15T11:00:00Z"
}
```

#### Update Platform (Full Update)

```http
PUT /api/v1/platforms/{platform_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Google BigQuery",
  "platform_type": "data_warehouse",
  "icon_name": "google-bigquery"
}
```

**Response (200 OK):** Same format as PATCH response.

#### Delete Platform

```http
DELETE /api/v1/platforms/{platform_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a platform will also delete all associated fields and may affect rules that depend on it.

### 5. Dimensions

Manage naming dimensions for rules.

#### List Dimensions

```http
GET /api/v1/dimensions/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `type`: Filter by dimension type
- `status`: Filter by status (active, inactive)
- `search`: Search by name or description

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "slug": "environment",
      "description": "Data environment classification",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "created_by": 1,
      "created_by_name": "Admin User",
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z",
      "workspace": 1
    }
  ]
}
```

#### Get Dimension Details

```http
GET /api/v1/dimensions/{dimension_id}/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "id": 1,
  "name": "Environment",
  "slug": "environment",
  "description": "Data environment classification",
  "type": "list",
  "parent": null,
  "parent_name": null,
  "status": "active",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-01T00:00:00Z",
  "workspace": 1,
  "value_count": 3
}
```

#### Create Dimension

```http
POST /api/v1/dimensions/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Data Classification",
  "description": "Classification of data sensitivity",
  "type": "list",
  "status": "active",
  "parent": null
}
```

**Response (201 Created):**

```json
{
  "id": 2,
  "name": "Data Classification",
  "slug": "data-classification",
  "description": "Classification of data sensitivity",
  "type": "list",
  "parent": null,
  "parent_name": null,
  "status": "active",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z",
  "workspace": 1
}
```

#### Update Dimension (Partial Update)

```http
PATCH /api/v1/dimensions/{dimension_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "description": "Updated description for data classification",
  "status": "active"
}
```

**Response (200 OK):**

```json
{
  "id": 2,
  "name": "Data Classification",
  "slug": "data-classification",
  "description": "Updated description for data classification",
  "type": "list",
  "parent": null,
  "parent_name": null,
  "status": "active",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T11:00:00Z",
  "workspace": 1
}
```

#### Update Dimension (Full Update)

```http
PUT /api/v1/dimensions/{dimension_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Data Classification",
  "description": "Updated description for data classification",
  "type": "list",
  "status": "active",
  "parent": null
}
```

**Response (200 OK):** Same format as PATCH response.

#### Delete Dimension

```http
DELETE /api/v1/dimensions/{dimension_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a dimension will also delete all its dimension values and may affect rules that use it.

### 6. Dimension Values

Manage possible values for dimensions.

#### List Dimension Values

```http
GET /dimension-values/
```

**Query Parameters:**

- `dimension`: Filter by dimension ID
- `value`: Search by value text

**Response:**

```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "dimension": 1,
      "value": "prod",
      "description": "Production environment",
      "is_active": true,
      "workspace": 1
    }
  ]
}
```

### 4. Fields

Manage data fields for platforms. Fields are global resources shared across all workspaces.

**Note**: Fields define the hierarchical structure for naming conventions (e.g., Database → Schema → Table). They are platform-specific but workspace-agnostic, meaning all workspaces can use the same field definitions for a given platform.

#### List Fields

```http
GET /api/v1/fields/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `platform`: Filter by platform ID
- `field_level`: Filter by hierarchy level (1, 2, 3, etc.)
- `search`: Search by field name

**Response:**

```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "name": "Database",
      "field_level": 1,
      "platform": 1,
      "platform_name": "Snowflake",
      "next_field": 2,
      "next_field_name": "Schema",
      "created_by": null,
      "created_by_name": null,
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Schema",
      "field_level": 2,
      "platform": 1,
      "platform_name": "Snowflake",
      "next_field": 3,
      "next_field_name": "Table",
      "created_by": 1,
      "created_by_name": "Admin User",
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Get Field Details

```http
GET /api/v1/fields/{field_id}/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "id": 1,
  "name": "Database",
  "field_level": 1,
  "platform": 1,
  "platform_name": "Snowflake",
  "next_field": 2,
  "next_field_name": "Schema",
  "created_by": null,
  "created_by_name": null,
  "created": "2024-01-01T00:00:00Z",
  "last_updated": "2024-01-01T00:00:00Z"
}
```

#### Create Field

```http
POST /api/v1/fields/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Table",
  "field_level": 3,
  "platform": 1,
  "next_field": null
}
```

**Response (201 Created):**

```json
{
  "id": 3,
  "name": "Table",
  "field_level": 3,
  "platform": 1,
  "platform_name": "Snowflake",
  "next_field": null,
  "next_field_name": null,
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z"
}
```

#### Update Field (Partial Update)

```http
PATCH /api/v1/fields/{field_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Data Table",
  "next_field": 4
}
```

**Response (200 OK):**

```json
{
  "id": 3,
  "name": "Data Table",
  "field_level": 3,
  "platform": 1,
  "platform_name": "Snowflake",
  "next_field": 4,
  "next_field_name": "Column",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T11:00:00Z"
}
```

#### Update Field (Full Update)

```http
PUT /api/v1/fields/{field_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Data Table",
  "field_level": 3,
  "platform": 1,
  "next_field": null
}
```

**Response (200 OK):** Same format as PATCH response.

#### Delete Field

```http
DELETE /api/v1/fields/{field_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a field may affect rules and naming conventions that depend on it.

### 7. Rules

Manage naming rules and conventions.

#### List Rules

```http
GET /rules/
```

**Query Parameters:**

- `platform`: Filter by platform ID
- `status`: Filter by status (active, inactive, draft)
- `is_default`: Filter default rules (true/false)

**Response:**

```json
{
  "count": 4,
  "results": [
    {
      "id": 1,
      "name": "Standard Database Naming",
      "platform": 1,
      "status": "active",
      "is_default": true,
      "description": "Standard naming convention for databases",
      "workspace": 1
    }
  ]
}
```

#### Rule Actions

##### Set Default Rule

```http
POST /rules/{rule_id}/set_default/
```

##### Get Rule Validation

```http
GET /rules/{rule_id}/validate_configuration/
```

##### Rule Preview

```http
POST /rules/{rule_id}/preview/
Content-Type: application/json

{
  "field_id": 1,
  "sample_values": {
    "environment": "prod",
    "data_classification": "public"
  }
}
```

##### Clone Rule

```http
POST /rule-nested/{rule_id}/clone/
Content-Type: application/json

{
  "name": "Cloned Rule Name",
  "description": "Description for cloned rule"
}
```

### 8. Rule Details

Manage detailed dimension configurations for rules.

#### List Rule Details

```http
GET /rule-details/
```

**Query Parameters:**

- `rule`: Filter by rule ID
- `field`: Filter by field ID
- `dimension_order`: Filter by order

**Response:**

```json
{
  "count": 6,
  "results": [
    {
      "id": 1,
      "rule": 1,
      "field": 1,
      "dimension": 1,
      "prefix": "db_",
      "suffix": "",
      "delimiter": "_",
      "dimension_order": 1,
      "is_required": true,
      "workspace": 1
    }
  ]
}
```

### 9. Strings

Manage generated naming strings.

#### List Strings

```http
GET /strings/
```

**Query Parameters:**

- `field`: Filter by field ID
- `rule_id`: Filter by rule ID
- `is_auto_generated`: Filter auto-generated strings
- `has_conflicts`: Filter strings with conflicts

**Response:**

```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "field": 1,
      "rule": 1,
      "value": "db_prod_customer_data",
      "is_auto_generated": true,
      "parent": null,
      "workspace": 1
    }
  ]
}
```

#### String Actions

##### Generate String

```http
POST /strings/generate/
Content-Type: application/json

{
  "submission_id": 1,
  "field_id": 1,
  "dimension_values": {
    "environment": "prod",
    "data_classification": "public"
  }
}
```

##### Bulk Generate Strings

```http
POST /strings/bulk_generate/
Content-Type: application/json

{
  "submission_id": 1,
  "generation_requests": [
    {
      "field_id": 1,
      "dimension_values": {"environment": "prod"}
    },
    {
      "field_id": 2,
      "dimension_values": {"environment": "test"}
    }
  ]
}
```

##### Check Naming Conflicts

```http
POST /strings/check_conflicts/
Content-Type: application/json

{
  "rule_id": 1,
  "field_id": 1,
  "proposed_value": "db_prod_test_data"
}
```

##### Get String Hierarchy

```http
GET /strings/{string_id}/hierarchy/
```

### 10. Submissions

Manage data submissions for string generation.

#### List Submissions

```http
GET /submissions/
```

**Query Parameters:**

- `status`: Filter by submission status
- `submission_date`: Filter by date

**Response:**

```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "status": "completed",
      "submission_date": "2024-01-01",
      "workspace": 1
    }
  ]
}
```

### 11. Nested Submissions

Manage submissions with embedded strings and details.

#### Create Nested Submission

```http
POST /nested-submissions/
Content-Type: application/json

{
  "rule": 1,
  "status": "draft",
  "submission_strings": [
    {
      "field": 1,
      "value": "db_prod_customer_data",
      "string_details": [
        {
          "dimension": 1,
          "dimension_value": 1,
          "prefix": "db_",
          "delimiter": "_",
          "dimension_order": 1
        }
      ]
    }
  ]
}
```

## Rule Configuration Endpoints

### Advanced Rule Management

These endpoints provide optimized data for complex rule configuration interfaces.

#### Lightweight Rule Data

```http
GET /rules/{rule_id}/lightweight/
```

**Response:** Minimal rule data for list views.

#### Field-Specific Rule Data

```http
GET /rules/{rule_id}/fields/{field_id}/
```

**Response:** Rule configuration specific to a field.

#### Rule Validation Summary

```http
GET /rules/{rule_id}/validation/
```

**Response:** Comprehensive validation status.

#### Generation Preview

```http
POST /rules/generation-preview/
Content-Type: application/json

{
  "rule_id": 1,
  "field_id": 1,
  "sample_values": {
    "environment": "prod",
    "data_classification": "public"
  }
}
```

#### Cache Management

```http
POST /rules/cache/invalidate/
Content-Type: application/json

{
  "rule_ids": [1, 2, 3]
}
```

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied to workspace
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "Description of the error",
  "details": "Additional error details",
  "field_errors": {
    "field_name": ["Field-specific error message"]
  }
}
```

### Workspace Access Errors

```json
{
  "error": "Access denied to this workspace"
}
```

```json
{
  "error": "No workspace context available"
}
```

## Pagination

All list endpoints support pagination:

### Request

```http
GET /api/v1/endpoint/?page=2&page_size=20
```

### Response

```json
{
  "count": 100,
  "next": "http://client1.yourdomain.com/api/v1/endpoint/?page=3",
  "previous": "http://client1.yourdomain.com/api/v1/endpoint/?page=1",
  "results": [...]
}
```

## Filtering & Search

### Query Parameters

Most endpoints support filtering via query parameters:

- Field-based filters: `field=value`
- Range filters: `created_at_gte=2024-01-01`
- Boolean filters: `is_active=true`
- Search: `search=keyword`

### Example

```http
GET /dimensions/?dimension_type=environment&is_required=true&search=prod
```

## Rate Limiting

API requests are rate-limited:

- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Caching

### Response Caching

- **Rule configuration data**: 15 minutes
- **Dimension data**: 30 minutes
- **Static data**: 1 hour

### Cache Headers

```
Cache-Control: max-age=900
ETag: "abc123def456"
```

## WebSocket Support (Future)

Real-time updates for:

- Rule validation status
- String generation progress
- Conflict detection

## SDKs & Integration

### JavaScript/TypeScript SDK

```javascript
import { TuxAPI } from "@tux/api-client";

const api = new TuxAPI({
  baseURL: "https://client1.yourdomain.com/api/v1/",
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
    base_url='https://client1.yourdomain.com/api/v1/',
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

## Migration & Deployment

### API Version Migration

When migrating between API versions, follow these best practices:

#### Migrating from Legacy to v1

1. **Update Base URLs**: Replace `/api/` with `/api/v1/` in your client applications
2. **Test Endpoints**: Verify all endpoints work with the new versioned URLs
3. **Update Documentation**: Update any internal documentation to reference v1 endpoints

#### Preparing for v2 Migration (Future)

1. **Monitor Deprecation Notices**: Check `/api/v1/version/` for deprecated features
2. **Review Breaking Changes**: Understand what will change in v2 via the version endpoint
3. **Plan Migration**: Develop a timeline for migrating to v2 when available

#### Backward Compatibility

- Legacy `/api/` endpoints remain functional and default to v1 behavior
- No immediate action required for existing integrations
- Recommended to migrate to versioned URLs for future-proofing

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

### Database Migrations

```bash
# For new deployments (clean migrations)
python manage.py migrate

# Create initial workspace
python manage.py create_workspace "Client 1" --admin-email admin@client1.com
```

**Note**: The migrations have been squashed for clean deployments. New instances will use the optimized `0001_initial.py` migration that represents the final state of all model changes.

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

## Support & Contact

- **API Issues**: api-support@yourcompany.com
- **Documentation**: docs@yourcompany.com
- **Emergency**: emergency@yourcompany.com

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
_Workspace Access: Flexible (No Subdomain Requirement)_
_CORS Configuration: Updated_
_Development Setup: Enhanced_
_CRUD Examples: Complete (GET, POST, PUT, PATCH, DELETE)_

#### 3. Create Rule

**POST** `/api/rules/`

Creates a new rule.

**Request Body:**

```json
{
  "platform": number,
  "status": string,
  "name": string
}
```

#### 4. Update Rule

**PUT/PATCH** `/api/rules/{id}/`

Updates rule information.

**Request Body:** Same as Create Rule

### Rule Details API

#### Base URL

```
/api/rule-details/
```

#### 1. List Rule Details

**GET** `/api/rule-details/`

Retrieves a list of all rule details.

**Query Parameters:**

- `platform` (number, optional): Filter by platform ID
- `field` (number, optional): Filter by field ID

**Response Format:**

```json
[
  {
    "id": number,
    "rule": number,
    "rule_name": string,
    "platform_id": number,
    "platform_name": string,
    "field": number,
    "field_id": number,
    "field_name": string,
    "field_level": number,
    "next_field": string,
    "dimension": number,
    "dimension_name": string,
    "dimension_type": string,
    "dimension_order": number,
    "prefix": string,
    "suffix": string,
    "delimiter": string,
    "parent_dimension_name": string,
    "parent_dimension_id": number,
    "in_parent_field": boolean,
    "is_max_field_level": boolean
  }
]
```

#### 2. Get Single Rule Detail

**GET** `/api/rule-details/{id}/`

Retrieves detailed information about a specific rule detail.

**Response Format:** Same as List Rule Details

#### 3. Create Rule Detail

**POST** `/api/rule-details/`

Creates a new rule detail.

**Request Body:**

```json
{
  "rule": number,
  "field": number,
  "dimension": number,
  "dimension_order": number,
  "prefix": string,
  "suffix": string,
  "delimiter": string
}
```

#### 4. Update Rule Detail

**PUT/PATCH** `/api/rule-details/{id}/`

Updates rule detail information.

**Request Body:** Same as Create Rule Detail

### Nested Rules API

#### Base URL

```
/api/rules-nested/
```

#### 1. List Nested Rules

**GET** `/api/rules-nested/`

Retrieves a list of all rules with their associated details.

**Response Format:**

```json
[
  {
    "id": number,
    "name": string,
    "field_details": [
      {
        // Same structure as Rule Detail
      }
    ]
  }
]
```

## Strings API

### Base URL

```
/api/strings/
```

### Endpoints

#### 1. List Strings

**GET** `/api/strings/`

Retrieves a list of all strings.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `field` (number, optional): Filter by field ID
- `parent` (number, optional): Filter by parent string ID

**Response Format:**

```json
[
  {
    "id": number,
    "submission": number,
    "last_updated": string (datetime),
    "created": string (datetime),
    "field": number,
    "field_name": string,
    "field_level": number,
    "platform_id": number,
    "platform_name": string,
    "string_uuid": string,
    "value": string,
    "parent": number,
    "parent_uuid": string
  }
]
```

#### 2. Get Single String

**GET** `/api/strings/{id}/`

Retrieves detailed information about a specific string.

**Response Format:** Same as List Strings

#### 3. Create String

**POST** `/api/strings/`

Creates a new string.

**Request Body:**

```json
{
  "submission": number,
  "field": number,
  "string_uuid": string,
  "value": string,
  "parent": number,
  "parent_uuid": string
}
```

#### 4. Update String

**PUT/PATCH** `/api/strings/{id}/`

Updates string information.

**Request Body:** Same as Create String

### String Details API

#### Base URL

```
/api/string-details/
```

#### 1. List String Details

**GET** `/api/string-details/`

Retrieves a list of all string details.

**Query Parameters:**

- `string` (number, optional): Filter by string ID
- `rule` (number, optional): Filter by rule ID
- `dimension_value` (number, optional): Filter by dimension value ID

**Response Format:**

```json
[
  {
    "id": number,
    "submission_name": string,
    "string": number,
    "dimension_value_id": number,
    "dimension_value": string,
    "dimension_value_label": string,
    "dimension_value_freetext": string,
    "dimension_id": number,
    "created": string (datetime),
    "last_updated": string (datetime)
  }
]
```

#### 2. Get Single String Detail

**GET** `/api/string-details/{id}/`

Retrieves detailed information about a specific string detail.

**Response Format:** Same as List String Details

#### 3. Create String Detail

**POST** `/api/string-details/`

Creates a new string detail.

**Request Body:**

```json
{
  "string": number,
  "rule": number,
  "dimension_value_id": number,
  "dimension_value_freetext": string
}
```

**Notes:**

- For mastered dimensions:
  - `dimension_value_id` is required
  - `dimension_value_freetext` cannot be set
- For free text dimensions:
  - `dimension_value_id` cannot be set
  - `dimension_value_freetext` is used

#### 4. Update String Detail

**PUT/PATCH** `/api/string-details/{id}/`

Updates string detail information.

**Request Body:** Same as Create String Detail

## Dimensions API

### Base URL

```
/api/dimensions/
```

### Endpoints

#### 1. List Dimensions

**GET** `/api/dimensions/`

Retrieves a list of all dimensions.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `dimension_type` (string, optional): Filter by dimension type

**Response Format:**

```json
[
  {
    "id": number,
    "definition": string,
    "dimension_type": string,
    "dimension_type_label": string,
    "name": string,
    "parent": number,
    "parent_name": string,
    "status": string
  }
]
```

#### 2. Get Single Dimension

**GET** `/api/dimensions/{id}/`

Retrieves detailed information about a specific dimension.

**Response Format:** Same as List Dimensions

#### 3. Create Dimension

**POST** `/api/dimensions/`

Creates a new dimension.

**Request Body:**

```json
{
  "definition": string,
  "dimension_type": string,
  "name": string,
  "parent": number,
  "status": string
}
```

#### 4. Update Dimension

**PUT/PATCH** `/api/dimensions/{id}/`

Updates dimension information.

**Request Body:** Same as Create Dimension

#### 5. Bulk Create Dimensions

**POST** `/api/dimensions/bulk_create/`

Creates multiple dimensions in a single request with transaction safety.

**Request Body:**

```json
{
  "dimensions": [
    {
      "name": "Environment",
      "description": "Deployment environment",
      "type": "list",
      "status": "active",
      "parent": null
    },
    {
      "name": "Region",
      "description": "Geographic region",
      "type": "list",
      "status": "active",
      "parent": null
    }
  ]
}
```

**Response Format:**

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "slug": "environment",
      "description": "Deployment environment",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Region",
      "slug": "region",
      "description": "Geographic region",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    }
  ],
  "errors": []
}
```

### Dimension Values API

#### Base URL

```
/api/dimension-values/
```

#### 1. List Dimension Values

**GET** `/api/dimension-values/`

Retrieves a list of all dimension values.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `dimension` (number, optional): Filter by dimension ID

**Response Format:**

```json
[
  {
    "id": number,
    "valid_from": string (datetime),
    "description": string,
    "value": string,
    "valid_until": string (datetime),
    "label": string,
    "utm": string,
    "dimension": number,
    "dimension_name": string,
    "dimension_parent_name": string,
    "dimension_parent": number,
    "parent": number,
    "parent_name": string,
    "parent_value": string,
    "created_by": number,
    "created_by_name": string,
    "created": string (datetime),
    "last_updated": string (datetime)
  }
]
```

#### 2. Get Single Dimension Value

**GET** `/api/dimension-values/{id}/`

Retrieves detailed information about a specific dimension value.

**Response Format:** Same as List Dimension Values

#### 3. Create Dimension Value

**POST** `/api/dimension-values/`

Creates a new dimension value.

**Request Body:**

```json
{
  "valid_from": string (datetime),
  "description": string,
  "value": string,
  "valid_until": string (datetime),
  "label": string,
  "utm": string,
  "dimension": number,
  "parent": number
}
```

#### 4. Update Dimension Value

**PUT/PATCH** `/api/dimension-values/{id}/`

Updates dimension value information.

**Request Body:** Same as Create Dimension Value

#### 5. Bulk Create Dimension Values

**POST** `/api/dimension-values/bulk_create/`

Creates multiple dimension values in a single request with transaction safety.

**Request Body:**

```json
{
  "dimension_values": [
    {
      "dimension": 1,
      "value": "prod",
      "label": "Production",
      "utm": "prod",
      "description": "Production environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    },
    {
      "dimension": 1,
      "value": "dev",
      "label": "Development",
      "utm": "dev",
      "description": "Development environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    }
  ]
}
```

**Response Format:**

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "valid_from": "2023-01-01",
      "description": "Production environment",
      "value": "prod",
      "valid_until": null,
      "label": "Production",
      "utm": "prod",
      "dimension": 1,
      "dimension_name": "Environment",
      "dimension_parent_name": null,
      "dimension_parent": null,
      "parent": null,
      "parent_name": null,
      "parent_value": null,
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    },
    {
      "id": 2,
      "valid_from": "2023-01-01",
      "description": "Development environment",
      "value": "dev",
      "valid_until": null,
      "label": "Development",
      "utm": "dev",
      "dimension": 1,
      "dimension_name": "Environment",
      "dimension_parent_name": null,
      "dimension_parent": null,
      "parent": null,
      "parent_name": null,
      "parent_value": null,
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    }
  ],
  "errors": []
}
```

**Error Response Example:**

```json
{
  "success_count": 1,
  "error_count": 1,
  "results": [
    // ... successful creations
  ],
  "errors": [
    {
      "index": 1,
      "dimension_value": "duplicate_value",
      "dimension_id": 1,
      "error": "UNIQUE constraint failed: master_data_dimensionvalue.dimension_id, master_data_dimensionvalue.value"
    }
  ]
}
```

## Workspaces API

### Base URL

```

```
