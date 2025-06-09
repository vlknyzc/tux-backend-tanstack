# Platform & Fields API

## Overview

Manage data platforms and their field hierarchies. Platforms and fields are global resources shared across all workspaces, allowing consistent platform definitions while maintaining workspace-specific configurations.

**Key Concepts:**

- **Platforms**: Data sources like Snowflake, BigQuery, Meta Ads
- **Fields**: Hierarchical naming structure (Database → Schema → Table → Column)
- **Global Resources**: Shared across workspaces for consistency
- **Field Levels**: Sequential hierarchy (1, 2, 3, etc.)

## Platforms API

### Base URL

```
/api/v1/platforms/
```

Platforms represent different advertising or data platforms (e.g., Meta, Google Ads, Snowflake). They are shared across all workspaces.

### List Platforms

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

### Get Platform Details

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

### Create Platform

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

### Update Platform (Partial Update)

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

### Update Platform (Full Update)

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

### Delete Platform

```http
DELETE /api/v1/platforms/{platform_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a platform will also delete all associated fields and may affect rules that depend on it.

## Platform Types

### Available Platform Types

- **data_warehouse**: Snowflake, BigQuery, Redshift
- **advertising**: Meta Ads, Google Ads, LinkedIn Ads
- **analytics**: Google Analytics, Adobe Analytics
- **crm**: Salesforce, HubSpot
- **database**: PostgreSQL, MySQL, MongoDB
- **other**: Custom or uncategorized platforms

### Platform Type Filtering

```http
GET /api/v1/platforms/?platform_type=data_warehouse
Authorization: Bearer your-jwt-token
```

## Fields API

### Base URL

```
/api/v1/fields/
```

Fields define the hierarchical structure for naming conventions (e.g., Database → Schema → Table). They are platform-specific but workspace-agnostic.

### List Fields

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

### Get Field Details

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

### Create Field

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

### Update Field (Partial Update)

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

### Update Field (Full Update)

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

### Delete Field

```http
DELETE /api/v1/fields/{field_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Warning**: Deleting a field may affect rules and naming conventions that depend on it.

## Field Hierarchy Management

### Understanding Field Levels

Field levels define the order in naming hierarchies:

1. **Level 1**: Typically the highest level (e.g., Database, Account)
2. **Level 2**: Second level (e.g., Schema, Campaign)
3. **Level 3**: Third level (e.g., Table, Ad Set)
4. **Level N**: Additional levels as needed

### Field Relationships

Fields can reference the next field in the hierarchy:

```json
{
  "id": 1,
  "name": "Database",
  "field_level": 1,
  "next_field": 2,
  "next_field_name": "Schema"
}
```

### Platform-Specific Field Hierarchies

#### Snowflake Example

```http
GET /api/v1/fields/?platform=1
```

**Response:**

```json
{
  "results": [
    { "id": 1, "name": "Database", "field_level": 1, "next_field": 2 },
    { "id": 2, "name": "Schema", "field_level": 2, "next_field": 3 },
    { "id": 3, "name": "Table", "field_level": 3, "next_field": 4 },
    { "id": 4, "name": "Column", "field_level": 4, "next_field": null }
  ]
}
```

#### Meta Ads Example

```http
GET /api/v1/fields/?platform=2
```

**Response:**

```json
{
  "results": [
    { "id": 5, "name": "Account", "field_level": 1, "next_field": 6 },
    { "id": 6, "name": "Campaign", "field_level": 2, "next_field": 7 },
    { "id": 7, "name": "Ad Set", "field_level": 3, "next_field": 8 },
    { "id": 8, "name": "Ad", "field_level": 4, "next_field": null }
  ]
}
```

## Bulk Operations

### Bulk Create Fields

Create multiple fields for a platform in one request:

```http
POST /api/v1/fields/bulk_create/
Authorization: Bearer your-jwt-token
Content-Type: application/json

{
  "platform": 1,
  "fields": [
    {"name": "Database", "field_level": 1},
    {"name": "Schema", "field_level": 2},
    {"name": "Table", "field_level": 3},
    {"name": "Column", "field_level": 4}
  ]
}
```

**Response:**

```json
{
  "success_count": 4,
  "error_count": 0,
  "created_fields": [
    {
      "id": 1,
      "name": "Database",
      "field_level": 1,
      "platform": 1
    }
  ],
  "errors": []
}
```

### Platform Field Templates

Get predefined field templates for common platforms:

```http
GET /api/v1/platforms/field_templates/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "templates": {
    "data_warehouse": [
      { "name": "Database", "field_level": 1 },
      { "name": "Schema", "field_level": 2 },
      { "name": "Table", "field_level": 3 },
      { "name": "Column", "field_level": 4 }
    ],
    "advertising": [
      { "name": "Account", "field_level": 1 },
      { "name": "Campaign", "field_level": 2 },
      { "name": "Ad Set", "field_level": 3 },
      { "name": "Ad", "field_level": 4 }
    ]
  }
}
```

## Platform & Field Relationships

### Get Platform with Fields

```http
GET /api/v1/platforms/{platform_id}/fields/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "platform": {
    "id": 1,
    "name": "Snowflake",
    "platform_type": "data_warehouse"
  },
  "fields": [
    {
      "id": 1,
      "name": "Database",
      "field_level": 1,
      "next_field": 2
    },
    {
      "id": 2,
      "name": "Schema",
      "field_level": 2,
      "next_field": 3
    }
  ],
  "hierarchy_chain": "Database → Schema → Table → Column"
}
```

### Field Usage Analytics

```http
GET /api/v1/fields/{field_id}/usage/
Authorization: Bearer your-jwt-token
```

**Response:**

```json
{
  "field_id": 1,
  "field_name": "Database",
  "usage_stats": {
    "total_rules": 12,
    "active_rules": 10,
    "workspaces_using": 5,
    "strings_generated": 1250
  },
  "recent_usage": [
    {
      "workspace_id": 1,
      "workspace_name": "Client 1",
      "rule_count": 3,
      "last_used": "2024-01-15T14:30:00Z"
    }
  ]
}
```

## Error Handling

### Common Errors

#### Platform Not Found (404)

```json
{
  "error": "Platform not found",
  "details": "Platform with ID 999 does not exist"
}
```

#### Field Level Conflict (400)

```json
{
  "error": "Field level conflict",
  "details": "Field level 2 already exists for this platform"
}
```

#### Invalid Field Hierarchy (400)

```json
{
  "error": "Invalid field hierarchy",
  "details": "next_field must have a higher field_level than current field"
}
```

#### Platform Dependencies (400)

```json
{
  "error": "Cannot delete platform",
  "details": "Platform has 5 associated fields and 12 active rules"
}
```

### Validation Rules

#### Platform Validation

- **Name**: Must be unique, 3-100 characters
- **Platform Type**: Must be valid type from predefined list
- **Slug**: Auto-generated from name, must be unique
- **Icon Name**: Optional, used for UI display

#### Field Validation

- **Name**: Must be unique within platform, 2-50 characters
- **Field Level**: Must be positive integer, unique within platform
- **Platform**: Must exist and be accessible
- **Next Field**: Must exist and have higher field_level if specified

## Permission Matrix

| Operation             | Superuser | Workspace Admin | User | Viewer |
| --------------------- | --------- | --------------- | ---- | ------ |
| List platforms        | ✅        | ✅              | ✅   | ✅     |
| View platform details | ✅        | ✅              | ✅   | ✅     |
| Create platform       | ✅        | ❌              | ❌   | ❌     |
| Update platform       | ✅        | ❌              | ❌   | ❌     |
| Delete platform       | ✅        | ❌              | ❌   | ❌     |
| List fields           | ✅        | ✅              | ✅   | ✅     |
| View field details    | ✅        | ✅              | ✅   | ✅     |
| Create field          | ✅        | ❌              | ❌   | ❌     |
| Update field          | ✅        | ❌              | ❌   | ❌     |
| Delete field          | ✅        | ❌              | ❌   | ❌     |

**Note**: Platforms and fields are global resources. Only superusers can modify them to ensure consistency across workspaces.

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
