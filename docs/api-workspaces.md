# Workspace Management API

## Overview

Manage client workspaces and their settings. Workspace management permissions:

- **Superusers**: Can create, update, and delete all workspaces
- **Workspace Admins**: Can update their assigned workspaces
- **Regular Users**: Can view their assigned workspaces

## Base URL

```
/api/v1/workspaces/
```

## Workspace Endpoints

### List Workspaces

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

### Get Workspace Details

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

### Create Workspace (Superuser Only)

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

### Update Workspace (Partial Update)

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

### Update Workspace (Full Update)

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

### Delete Workspace (Superuser Only)

```http
DELETE /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a workspace will also delete all associated data (dimensions, rules, strings, etc.).

## Workspace Status Management

### Available Status Values

- **active**: Workspace is operational and accessible
- **inactive**: Workspace is disabled but data is preserved
- **archived**: Workspace is archived (read-only)
- **deleted**: Workspace is marked for deletion

### Status Transitions

```http
PATCH /api/v1/workspaces/{workspace_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "status": "inactive"
}
```

**Valid Transitions:**

- `active` → `inactive`, `archived`
- `inactive` → `active`, `archived`
- `archived` → `active` (with admin approval)
- Any status → `deleted` (superuser only)

## Workspace Configuration

### Workspace Settings

Advanced workspace configuration for administrators:

```http
GET /api/v1/workspaces/{workspace_id}/settings/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "workspace_id": 1,
  "settings": {
    "features": {
      "string_generation": true,
      "rule_validation": true,
      "bulk_operations": true
    },
    "limits": {
      "max_dimensions": 100,
      "max_rules": 50,
      "max_strings_per_rule": 1000
    },
    "permissions": {
      "allow_user_registration": false,
      "require_admin_approval": true,
      "enable_api_access": true
    }
  }
}
```

### Update Workspace Settings

```http
PUT /api/v1/workspaces/{workspace_id}/settings/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "settings": {
    "features": {
      "string_generation": true,
      "rule_validation": true,
      "bulk_operations": false
    },
    "limits": {
      "max_dimensions": 50,
      "max_rules": 25,
      "max_strings_per_rule": 500
    }
  }
}
```

## Workspace Analytics

### Get Workspace Statistics

```http
GET /api/v1/workspaces/{workspace_id}/analytics/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "workspace_id": 1,
  "analytics": {
    "users": {
      "total": 5,
      "active": 4,
      "by_role": {
        "admin": 2,
        "user": 2,
        "viewer": 1
      }
    },
    "data": {
      "dimensions": 12,
      "dimension_values": 45,
      "rules": 8,
      "strings": 156
    },
    "activity": {
      "last_string_generated": "2024-01-15T14:30:00Z",
      "last_rule_updated": "2024-01-14T09:15:00Z",
      "total_api_calls_today": 234
    }
  }
}
```

### Workspace Usage Summary

```http
GET /api/v1/workspaces/usage_summary/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "summary": [
    {
      "workspace_id": 1,
      "workspace_name": "Client 1",
      "user_count": 5,
      "dimension_count": 12,
      "rule_count": 8,
      "string_count": 156,
      "last_activity": "2024-01-15T14:30:00Z",
      "status": "active"
    },
    {
      "workspace_id": 2,
      "workspace_name": "Client 2",
      "user_count": 3,
      "dimension_count": 8,
      "rule_count": 5,
      "string_count": 89,
      "last_activity": "2024-01-14T16:45:00Z",
      "status": "active"
    }
  ],
  "totals": {
    "total_workspaces": 2,
    "total_users": 8,
    "total_dimensions": 20,
    "total_rules": 13,
    "total_strings": 245
  }
}
```

## Logo Management

### Upload Workspace Logo

```http
POST /api/v1/workspaces/{workspace_id}/logo/
Authorization: Bearer your-jwt-token
Content-Type: multipart/form-data

{
  "logo": <file>
}
```

**Response (200 OK):**

```json
{
  "logo_url": "/media/workspaces/client1-logo.png",
  "message": "Logo uploaded successfully"
}
```

### Delete Workspace Logo

```http
DELETE /api/v1/workspaces/{workspace_id}/logo/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**File Requirements:**

- **Formats**: PNG, JPG, JPEG, SVG
- **Maximum Size**: 2MB
- **Recommended Dimensions**: 200x200px (square)

## Workspace Templates

### Create Workspace from Template

```http
POST /api/v1/workspaces/from_template/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "New Client from Template",
  "template_id": 1,
  "copy_data": true,
  "copy_users": false
}
```

**Response (201 Created):**

```json
{
  "workspace": {
    "id": 4,
    "name": "New Client from Template",
    "slug": "new-client-from-template",
    "status": "active",
    "created": "2024-01-15T15:00:00Z"
  },
  "copied_data": {
    "dimensions": 12,
    "dimension_values": 45,
    "rules": 8
  },
  "message": "Workspace created successfully from template"
}
```

### List Workspace Templates

```http
GET /api/v1/workspaces/templates/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Standard Client Template",
      "description": "Default template with common dimensions and rules",
      "dimension_count": 12,
      "rule_count": 8,
      "created": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## Bulk Operations

### Bulk Update Workspace Status

```http
POST /api/v1/workspaces/bulk_update_status/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "workspace_ids": [1, 2, 3],
  "status": "inactive"
}
```

**Response:**

```json
{
  "success_count": 3,
  "error_count": 0,
  "updated_workspaces": [
    {
      "id": 1,
      "name": "Client 1",
      "new_status": "inactive"
    },
    {
      "id": 2,
      "name": "Client 2",
      "new_status": "inactive"
    }
  ],
  "errors": []
}
```

## Access Control

### Workspace Permissions

Different operations require different permission levels:

| Operation              | Superuser | Workspace Admin | User        | Viewer      |
| ---------------------- | --------- | --------------- | ----------- | ----------- |
| List workspaces        | ✅ All    | ✅ Assigned     | ✅ Assigned | ✅ Assigned |
| View workspace details | ✅ All    | ✅ Assigned     | ✅ Assigned | ✅ Assigned |
| Create workspace       | ✅        | ❌              | ❌          | ❌          |
| Update workspace       | ✅ All    | ✅ Assigned     | ❌          | ❌          |
| Delete workspace       | ✅        | ❌              | ❌          | ❌          |
| Manage settings        | ✅ All    | ✅ Assigned     | ❌          | ❌          |
| View analytics         | ✅ All    | ✅ Assigned     | ❌          | ❌          |
| Upload logo            | ✅ All    | ✅ Assigned     | ❌          | ❌          |

### Workspace Context Filtering

For non-superusers, all workspace-related endpoints automatically filter results to only show workspaces the user has access to through their workspace assignments.

## Error Handling

### Common Errors

#### Workspace Not Found (404)

```json
{
  "error": "Workspace not found",
  "details": "Workspace with ID 999 does not exist or you don't have access to it"
}
```

#### Insufficient Permissions (403)

```json
{
  "error": "Access denied",
  "details": "You don't have permission to modify this workspace"
}
```

#### Invalid Status Transition (400)

```json
{
  "error": "Invalid status transition",
  "details": "Cannot change status from 'archived' to 'deleted' without admin approval"
}
```

#### Workspace Name Conflict (400)

```json
{
  "error": "Validation failed",
  "field_errors": {
    "name": ["Workspace with this name already exists."]
  }
}
```

### Validation Rules

- **Name**: Must be unique, 3-100 characters
- **Slug**: Auto-generated from name, must be unique
- **Status**: Must be one of: active, inactive, archived, deleted
- **Logo**: Must be valid image file, max 2MB

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
