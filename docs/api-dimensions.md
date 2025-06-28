# Dimensions API

## Overview

Manage naming dimensions and their values. Dimensions are workspace-specific resources that define the categorization system for naming conventions (e.g., Environment, Region, Data Classification).

**Key Concepts:**

- **Dimensions**: Categories for organizing naming conventions (Environment, Region, etc.)
- **Dimension Values**: Specific values within each dimension (prod, dev, staging, etc.)
- **Workspace-Specific**: Each workspace has its own set of dimensions
- **Hierarchical**: Dimensions can have parent-child relationships

## Base URL

```
/api/v1/dimensions/
```

## Workspace Context

Dimensions are **workspace-specific** resources. This means:

1. **Automatic Filtering**: API automatically shows only dimensions from workspaces the user has access to
2. **Workspace Assignment**: Each dimension belongs to exactly one workspace
3. **User Access**: Users can only see/modify dimensions in workspaces they're assigned to
4. **Multi-Workspace Users**: Users with access to multiple workspaces see dimensions from all their accessible workspaces

### Workspace Filtering Examples

#### Single Workspace User

If a user only has access to Workspace 1:

```http
GET /api/v1/dimensions/
# Returns only dimensions from Workspace 1
```

#### Multi-Workspace User

If a user has access to Workspaces 1 and 2:

```http
GET /api/v1/dimensions/
# Returns dimensions from both Workspace 1 and 2

GET /api/v1/dimensions/?workspace=1
# Returns only dimensions from Workspace 1
```

#### Superuser

Superusers see dimensions from all workspaces:

```http
GET /api/v1/dimensions/
# Returns dimensions from all workspaces

GET /api/v1/dimensions/?workspace=3
# Can access any workspace, even if not explicitly assigned
```

## Dimensions Endpoints

### List Dimensions

```http
GET /api/v1/dimensions/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `workspace`: Filter by specific workspace ID (optional, defaults to user's accessible workspaces)
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
      "workspace": 1,
      "workspace_name": "Client 1",
      "created_by": 1,
      "created_by_name": "Admin User",
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Region",
      "slug": "region",
      "description": "Geographic region classification",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "workspace": 1,
      "workspace_name": "Client 1",
      "created_by": 1,
      "created_by_name": "Admin User",
      "created": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Dimension Details

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

### Create Dimension

```http
POST /api/v1/dimensions/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "name": "Data Classification",
  "description": "Classification of data sensitivity",
  "type": "list",
  "status": "active",
  "parent": null,
  "workspace": 1
}
```

**Note**:

- If `workspace` is not specified, the dimension is created in the user's primary/current workspace
- Users can only create dimensions in workspaces they have admin or user permissions for
- The workspace must be one the user has access to

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
  "workspace": 1,
  "workspace_name": "Client 1",
  "created_by": 1,
  "created_by_name": "Admin User",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z"
}
```

### Update Dimension (Partial Update)

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

### Update Dimension (Full Update)

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

### Delete Dimension

```http
DELETE /api/v1/dimensions/{dimension_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a dimension will also delete all its dimension values and may affect rules that use it.

## Workspace-Specific Operations

### How Workspace Assignment Works

1. **During Creation**: Dimension is assigned to the specified workspace (or user's current workspace)
2. **Automatic Filtering**: API queries automatically filter by user's accessible workspaces
3. **Cross-Workspace**: Users with multiple workspace access see dimensions from all their workspaces
4. **Workspace Switching**: Frontend can filter by specific workspace using `?workspace=X` parameter

### Multi-Workspace Response Example

For a user with access to multiple workspaces:

```http
GET /api/v1/dimensions/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "count": 4,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "workspace": 1,
      "workspace_name": "Client 1",
      "description": "Client 1 environment classification"
    },
    {
      "id": 2,
      "name": "Environment",
      "workspace": 2,
      "workspace_name": "Client 2",
      "description": "Client 2 environment classification"
    },
    {
      "id": 3,
      "name": "Data Classification",
      "workspace": 1,
      "workspace_name": "Client 1",
      "description": "Client 1 data sensitivity levels"
    }
  ]
}
```

### Filtering by Specific Workspace

```http
GET /api/v1/dimensions/?workspace=1
Authorization: Bearer your-jwt-token
```

**Response (only dimensions from Workspace 1):**

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "workspace": 1,
      "workspace_name": "Client 1"
    },
    {
      "id": 3,
      "name": "Data Classification",
      "workspace": 1,
      "workspace_name": "Client 1"
    }
  ]
}
```

## Dimension Types

### Available Types

- **list**: Predefined list of values (most common)
- **freetext**: User can enter any text value
- **number**: Numeric values only
- **date**: Date values
- **boolean**: True/false values

### Type-Specific Behavior

#### List Type

- Values must be predefined via dimension values
- Strict validation against allowed values
- Most commonly used for categories

#### Freetext Type

- Users can enter any text value
- No predefined values required
- Useful for names, descriptions, etc.

#### Number Type

- Only numeric values allowed
- Can specify min/max ranges
- Useful for IDs, counts, etc.

## Bulk Operations

### Bulk Create Dimensions

```http
POST /api/v1/dimensions/bulk_create/
Authorization: Bearer your-jwt-token
Content-Type: application/json

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

**Response:**

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
    }
  ],
  "errors": []
}
```

## Dimension Values API

### Base URL

```
/api/v1/dimension-values/
```

Manage specific values within dimensions.

### List Dimension Values

```http
GET /api/v1/dimension-values/
Authorization: Bearer your-jwt-token
```

**Query Parameters:**

- `dimension`: Filter by dimension ID
- `value`: Search by value text
- `is_active`: Filter by active status

**Response:**

```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "valid_from": "2023-01-01T00:00:00Z",
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
      "last_updated": "2023-12-01T10:00:00Z",
      "is_active": true,
      "workspace": 1
    }
  ]
}
```

### Get Dimension Value Details

```http
GET /api/v1/dimension-values/{value_id}/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "id": 1,
  "valid_from": "2023-01-01T00:00:00Z",
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
  "last_updated": "2023-12-01T10:00:00Z",
  "is_active": true,
  "workspace": 1
}
```

### Create Dimension Value

```http
POST /api/v1/dimension-values/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "dimension": 1,
  "value": "staging",
  "label": "Staging",
  "utm": "staging",
  "description": "Staging environment",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": null,
  "parent": null
}
```

**Response (201 Created):**

```json
{
  "id": 4,
  "valid_from": "2024-01-01T00:00:00Z",
  "description": "Staging environment",
  "value": "staging",
  "valid_until": null,
  "label": "Staging",
  "utm": "staging",
  "dimension": 1,
  "dimension_name": "Environment",
  "dimension_parent_name": null,
  "dimension_parent": null,
  "parent": null,
  "parent_name": null,
  "parent_value": null,
  "created_by": 1,
  "created_by_name": "John Doe",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:00:00Z",
  "is_active": true,
  "workspace": 1
}
```

### Update Dimension Value (Partial Update)

```http
PATCH /api/v1/dimension-values/{value_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "label": "Staging Environment",
  "description": "Updated staging environment description"
}
```

**Response (200 OK):** Same format as create response with updated fields.

### Update Dimension Value (Full Update)

```http
PUT /api/v1/dimension-values/{value_id}/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "dimension": 1,
  "value": "staging",
  "label": "Staging Environment",
  "utm": "staging",
  "description": "Updated staging environment description",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": null,
  "parent": null
}
```

**Response (200 OK):** Same format as PATCH response.

### Delete Dimension Value

```http
DELETE /api/v1/dimension-values/{value_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

### Bulk Create Dimension Values

```http
POST /api/v1/dimension-values/bulk_create/
Authorization: Bearer your-jwt-token
Content-Type: application/json

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

**Response:**

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "value": "prod",
      "label": "Production",
      "dimension": 1,
      "dimension_name": "Environment"
    }
  ],
  "errors": []
}
```

## Hierarchical Dimensions

### Parent-Child Relationships

Dimensions can have hierarchical relationships:

```json
{
  "id": 2,
  "name": "Sub-Environment",
  "parent": 1,
  "parent_name": "Environment",
  "description": "Specific environment sub-categories"
}
```

### Hierarchical Values

Dimension values can also have parent-child relationships:

```json
{
  "id": 5,
  "value": "prod-east",
  "label": "Production East",
  "parent": 1,
  "parent_value": "prod",
  "dimension": 2
}
```

### Get Dimension Hierarchy

```http
GET /api/v1/dimensions/{dimension_id}/hierarchy/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "dimension": {
    "id": 1,
    "name": "Environment",
    "level": 1
  },
  "children": [
    {
      "id": 2,
      "name": "Sub-Environment",
      "level": 2,
      "parent": 1
    }
  ],
  "values": [
    {
      "id": 1,
      "value": "prod",
      "children": [
        {
          "id": 5,
          "value": "prod-east",
          "parent": 1
        }
      ]
    }
  ]
}
```

## Dimension Analytics

### Get Dimension Usage

```http
GET /api/v1/dimensions/{dimension_id}/usage/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "dimension_id": 1,
  "dimension_name": "Environment",
  "usage_stats": {
    "total_values": 5,
    "active_values": 4,
    "rules_using": 12,
    "strings_generated": 1250
  },
  "value_usage": [
    {
      "value_id": 1,
      "value": "prod",
      "usage_count": 850,
      "last_used": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### Workspace Dimension Summary

```http
GET /api/v1/dimensions/workspace_summary/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "workspace_id": 1,
  "dimension_summary": {
    "total_dimensions": 12,
    "active_dimensions": 10,
    "total_values": 45,
    "active_values": 42,
    "by_type": {
      "list": 8,
      "freetext": 3,
      "number": 1
    }
  },
  "recent_activity": [
    {
      "dimension_id": 1,
      "dimension_name": "Environment",
      "action": "value_created",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Access Control

### Permission Matrix

| Operation              | Superuser | Workspace Admin | User         | Viewer       |
| ---------------------- | --------- | --------------- | ------------ | ------------ |
| List dimensions        | ✅ All    | ✅ Workspace    | ✅ Workspace | ✅ Workspace |
| View dimension details | ✅ All    | ✅ Workspace    | ✅ Workspace | ✅ Workspace |
| Create dimension       | ✅ All    | ✅ Workspace    | ❌           | ❌           |
| Update dimension       | ✅ All    | ✅ Workspace    | ❌           | ❌           |
| Delete dimension       | ✅ All    | ✅ Workspace    | ❌           | ❌           |
| List dimension values  | ✅ All    | ✅ Workspace    | ✅ Workspace | ✅ Workspace |
| Create dimension value | ✅ All    | ✅ Workspace    | ✅ Workspace | ❌           |
| Update dimension value | ✅ All    | ✅ Workspace    | ✅ Workspace | ❌           |
| Delete dimension value | ✅ All    | ✅ Workspace    | ❌           | ❌           |

## Error Handling

### Common Errors

#### Dimension Not Found (404)

```json
{
  "error": "Dimension not found",
  "details": "Dimension with ID 999 does not exist or you don't have access to it"
}
```

#### Invalid Dimension Type (400)

```json
{
  "error": "Invalid dimension type",
  "details": "Dimension type must be one of: list, freetext, number, date, boolean"
}
```

#### Circular Reference (400)

```json
{
  "error": "Circular reference detected",
  "details": "Dimension cannot be its own parent or create a circular hierarchy"
}
```

#### Value Constraint Violation (400)

```json
{
  "error": "Value constraint violation",
  "details": "Value 'invalid' is not allowed for dimension type 'number'"
}
```

### Validation Rules

#### Dimension Validation

- **Name**: Must be unique within workspace, 2-100 characters
- **Type**: Must be valid dimension type
- **Slug**: Auto-generated from name, must be unique
- **Parent**: Cannot create circular references

#### Dimension Value Validation

- **Value**: Must comply with dimension type constraints
- **Dimension**: Must exist and be accessible
- **Valid From/Until**: Must be valid dates, valid_until > valid_from
- **Parent**: Must exist and belong to same dimension

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
