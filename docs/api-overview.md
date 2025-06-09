# API Overview & Authentication

## Authentication & Authorization

All API endpoints require authentication via session-based authentication or token authentication.

### Headers Required

```
Authorization: Token <your-token>
# OR
Cookie: sessionid=<session-id>
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

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
