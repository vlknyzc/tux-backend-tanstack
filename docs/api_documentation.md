# TUX Backend - Multi-Tenant API Documentation

## Overview

The TUX Backend is a multi-tenant Django application that manages naming conventions and string generation for different clients. Each client has their own isolated workspace with data separation.

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

The application uses subdomain-based workspace routing:

- `client1.yourdomain.com` → Client 1's workspace
- `client2.yourdomain.com` → Client 2's workspace

### Access Control

- **Regular Users**: Can only access workspaces they're assigned to
- **Superusers**: Can access all workspaces across all clients
- **Workspace Roles**: admin, user, viewer (different permission levels)

### Workspace Detection

The system automatically detects the current workspace from the subdomain and filters all data accordingly.

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

- **Versioned (Recommended)**: `https://client1.yourdomain.com/api/v1/`
- **Legacy**: `https://client1.yourdomain.com/api/`
- Alternative clients: `https://client2.yourdomain.com/api/v1/`

### Development

- **Versioned (Recommended)**: `http://client1.localhost:8000/api/v1/`
- **Legacy**: `http://client1.localhost:8000/api/`

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

#### Update User

```http
PATCH /api/v1/users/{user_id}/
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "Name",
  "is_active": true
}
```

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

#### Assign User to Workspace

```http
POST /api/v1/workspace-users/
Content-Type: application/json

{
  "user": 3,
  "workspace": 1,
  "role": "user",
  "is_active": true
}
```

#### Update User Role in Workspace

```http
PATCH /api/v1/workspace-users/{assignment_id}/
Content-Type: application/json

{
  "role": "admin",
  "is_active": true
}
```

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
```

**Response:**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Client 1",
      "status": "active",
      "description": "Client 1 workspace",
      "created_at": "2024-01-01T00:00:00Z",
      "created_by": 1
    }
  ]
}
```

#### Create Workspace (Superuser Only)

```http
POST /api/v1/workspaces/
Content-Type: application/json

{
  "name": "New Client",
  "description": "New client workspace",
  "status": "active"
}
```

### 3. Platforms

Manage data platforms. Platforms are global resources shared across all workspaces.

**Note**: Platforms represent different advertising or data platforms (e.g., Meta, Google Ads, Snowflake). They are shared across all workspaces, allowing consistent platform definitions while maintaining workspace-specific rules and data.

#### List Platforms

```http
GET /api/v1/platforms/
```

**Query Parameters:**

- `id`: Filter by platform ID
- `name`: Filter by platform name

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
    }
  ]
}
```

#### Create Platform

```http
POST /api/v1/platforms/
Content-Type: application/json

{
  "name": "BigQuery",
  "platform_type": "data_warehouse",
  "slug": "bigquery",
  "icon_name": "bigquery"
}
```

### 5. Dimensions

Manage naming dimensions for rules.

#### List Dimensions

```http
GET /dimensions/
```

**Query Parameters:**

- `dimension_type`: Filter by type (e.g., "environment", "data_classification")
- `is_required`: Filter by required status (true/false)

**Response:**

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "dimension_type": "environment",
      "description": "Data environment classification",
      "is_required": true,
      "workspace": 1
    }
  ]
}
```

#### Create Dimension

```http
POST /dimensions/
Content-Type: application/json

{
  "name": "Data Classification",
  "dimension_type": "data_classification",
  "description": "Classification of data sensitivity",
  "is_required": true
}
```

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
```

**Query Parameters:**

- `platform`: Filter by platform ID
- `field_level`: Filter by hierarchy level (1, 2, 3, etc.)

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
    }
  ]
}
```

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

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost/tux_db
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=client1.yourdomain.com,client2.yourdomain.com

# Optional
DEBUG=False
CACHE_URL=redis://localhost:6379/1
CORS_ALLOWED_ORIGINS=https://client1.yourdomain.com
```

### Database Migrations

```bash
# For new deployments (clean migrations)
python manage.py migrate

# Create initial workspace
python manage.py create_workspace "Client 1" --admin-email admin@client1.com
```

**Note**: The migrations have been squashed for clean deployments. New instances will use the optimized `0001_initial.py` migration that represents the final state of all model changes.

## Testing

### Test Workspaces

Development environments include test workspaces:

- `test1.localhost:8000` → Test Workspace 1
- `test2.localhost:8000` → Test Workspace 2

### Sample API Calls

```bash
# Test authentication
curl -H "Authorization: Token abc123" \
     https://client1.yourdomain.com/api/v1/workspaces/

# Test workspace isolation
curl -H "Authorization: Token abc123" \
     https://client1.yourdomain.com/api/v1/dimensions/

# Test API versioning
curl -H "Authorization: Token abc123" \
     https://client1.yourdomain.com/api/v1/version/

# Test health endpoint
curl https://client1.yourdomain.com/api/v1/health/
```

## Support & Contact

- **API Issues**: api-support@yourcompany.com
- **Documentation**: docs@yourcompany.com
- **Emergency**: emergency@yourcompany.com

---

_Last Updated: 2024-01-01_
_API Version: 1.0_

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
