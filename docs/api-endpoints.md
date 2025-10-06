# tuxonomy.com API Endpoints

This document provides a comprehensive list of all available API endpoints in the tuxonomy.com system.

## Base URL Structure

All API endpoints follow the versioned pattern:

- **Base URL**: `/api/{version}/`
- **Supported Versions**: `v1`, `v2`
- **Authentication**: JWT Bearer token required for most endpoints

## Authentication Endpoints

### JWT Token Management

- **POST** `/api/{version}/token/` - Obtain JWT access token
- **POST** `/api/{version}/token/refresh/` - Refresh JWT access token

### User Authentication (Djoser)

- **POST** `/api/{version}/jwt/create/` - Custom JWT token creation
- **POST** `/api/{version}/jwt/refresh/` - Custom JWT token refresh
- **POST** `/api/{version}/jwt/verify/` - Verify JWT token
- **POST** `/api/{version}/logout/` - User logout

### User Management

- **GET** `/api/{version}/users/` - List users
- **POST** `/api/{version}/users/` - Create user
- **GET** `/api/{version}/users/{id}/` - Get user details
- **PUT** `/api/{version}/users/{id}/` - Update user
- **PATCH** `/api/{version}/users/{id}/` - Partial update user
- **DELETE** `/api/{version}/users/{id}/` - Delete user

### Workspace User Management

- **GET** `/api/{version}/workspace-users/` - List workspace users
- **POST** `/api/{version}/workspace-users/` - Add user to workspace
- **GET** `/api/{version}/workspace-users/{id}/` - Get workspace user details
- **PUT** `/api/{version}/workspace-users/{id}/` - Update workspace user
- **PATCH** `/api/{version}/workspace-users/{id}/` - Partial update workspace user
- **DELETE** `/api/{version}/workspace-users/{id}/` - Remove user from workspace

## Core Data Endpoints

### Workspaces

- **GET** `/api/{version}/workspaces/` - List workspaces
- **POST** `/api/{version}/workspaces/` - Create workspace
- **GET** `/api/{version}/workspaces/{id}/` - Get workspace details
- **PUT** `/api/{version}/workspaces/{id}/` - Update workspace
- **PATCH** `/api/{version}/workspaces/{id}/` - Partial update workspace
- **DELETE** `/api/{version}/workspaces/{id}/` - Delete workspace

### Platforms

- **GET** `/api/{version}/platforms/` - List platforms
- **POST** `/api/{version}/platforms/` - Create platform
- **GET** `/api/{version}/platforms/{id}/` - Get platform details
- **PUT** `/api/{version}/platforms/{id}/` - Update platform
- **PATCH** `/api/{version}/platforms/{id}/` - Partial update platform
- **DELETE** `/api/{version}/platforms/{id}/` - Delete platform

### Dimensions

- **GET** `/api/{version}/dimensions/` - List dimensions
- **POST** `/api/{version}/dimensions/` - Create dimension
- **GET** `/api/{version}/dimensions/{id}/` - Get dimension details
- **PUT** `/api/{version}/dimensions/{id}/` - Update dimension
- **PATCH** `/api/{version}/dimensions/{id}/` - Partial update dimension
- **DELETE** `/api/{version}/dimensions/{id}/` - Delete dimension

### Dimension Values

- **GET** `/api/{version}/dimension-values/` - List dimension values
- **POST** `/api/{version}/dimension-values/` - Create dimension value
- **GET** `/api/{version}/dimension-values/{id}/` - Get dimension value details
- **PUT** `/api/{version}/dimension-values/{id}/` - Update dimension value
- **PATCH** `/api/{version}/dimension-values/{id}/` - Partial update dimension value
- **DELETE** `/api/{version}/dimension-values/{id}/` - Delete dimension value

### Fields

- **GET** `/api/{version}/fields/` - List fields
- **POST** `/api/{version}/fields/` - Create field
- **GET** `/api/{version}/fields/{id}/` - Get field details
- **PUT** `/api/{version}/fields/{id}/` - Update field
- **PATCH** `/api/{version}/fields/{id}/` - Partial update field
- **DELETE** `/api/{version}/fields/{id}/` - Delete field

## Rules and Configuration

### Rules

- **GET** `/api/{version}/rules/` - List rules
- **POST** `/api/{version}/rules/` - Create rule
- **GET** `/api/{version}/rules/{id}/` - Get rule details
- **PUT** `/api/{version}/rules/{id}/` - Update rule
- **PATCH** `/api/{version}/rules/{id}/` - Partial update rule
- **DELETE** `/api/{version}/rules/{id}/` - Delete rule

### Rule Details

- **GET** `/api/{version}/rule-details/` - List rule details
- **POST** `/api/{version}/rule-details/` - Create rule detail
- **GET** `/api/{version}/rule-details/{id}/` - Get rule detail
- **PUT** `/api/{version}/rule-details/{id}/` - Update rule detail
- **PATCH** `/api/{version}/rule-details/{id}/` - Partial update rule detail
- **DELETE** `/api/{version}/rule-details/{id}/` - Delete rule detail

### Nested Rules

- **GET** `/api/{version}/rule-nested/` - List nested rules
- **POST** `/api/{version}/rule-nested/` - Create nested rule
- **GET** `/api/{version}/rule-nested/{id}/` - Get nested rule details
- **PUT** `/api/{version}/rule-nested/{id}/` - Update nested rule
- **PATCH** `/api/{version}/rule-nested/{id}/` - Partial update nested rule
- **DELETE** `/api/{version}/rule-nested/{id}/` - Delete nested rule

### Rule Configuration

- **GET** `/api/{version}/rules/{rule_id}/configuration/` - Get rule configuration
- **GET** `/api/{version}/rules/{rule_id}/lightweight/` - Get lightweight rule view
- **GET** `/api/{version}/rules/{rule_id}/fields/{field_id}/` - Get field-specific rule
- **POST** `/api/{version}/rules/{rule_id}/validation/` - Validate rule
- **POST** `/api/{version}/rules/generation-preview/` - Preview rule generation

### Cache Management

- **POST** `/api/{version}/rules/cache/invalidate/` - Invalidate rule cache
- **GET** `/api/{version}/rules/{rule_id}/metrics/` - Get rule performance metrics

## Main API Endpoints (Workspace-Scoped)

### Submissions

- **GET** `/api/{version}/workspaces/{workspace_id}/submissions/` - List submissions
- **POST** `/api/{version}/workspaces/{workspace_id}/submissions/` - Create submission
- **GET** `/api/{version}/workspaces/{workspace_id}/submissions/{id}/` - Get submission
- **PUT** `/api/{version}/workspaces/{workspace_id}/submissions/{id}/` - Update submission
- **PATCH** `/api/{version}/workspaces/{workspace_id}/submissions/{id}/` - Partial update submission
- **DELETE** `/api/{version}/workspaces/{workspace_id}/submissions/{id}/` - Delete submission

### Strings

- **GET** `/api/{version}/workspaces/{workspace_id}/strings/` - List strings
- **POST** `/api/{version}/workspaces/{workspace_id}/strings/` - Create string
- **GET** `/api/{version}/workspaces/{workspace_id}/strings/{id}/` - Get string
- **DELETE** `/api/{version}/workspaces/{workspace_id}/strings/{id}/` - Delete string

### String Details

- **GET** `/api/{version}/workspaces/{workspace_id}/string-details/` - List string details
- **POST** `/api/{version}/workspaces/{workspace_id}/string-details/` - Create string detail
- **GET** `/api/{version}/workspaces/{workspace_id}/string-details/{id}/` - Get string detail
- **PUT** `/api/{version}/workspaces/{workspace_id}/string-details/{id}/` - Update string detail
- **PATCH** `/api/{version}/workspaces/{workspace_id}/string-details/{id}/` - Partial update string detail
- **DELETE** `/api/{version}/workspaces/{workspace_id}/string-details/{id}/` - Delete string detail

## Nested Resource Endpoints

### Submission Strings

- **GET** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/` - List submission strings
- **POST** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/` - Add string to submission
- **GET** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/{string_id}/` - Get submission string
- **DELETE** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/{string_id}/` - Remove string from submission

### String Details (Nested)

- **GET** `/api/{version}/workspaces/{workspace_id}/strings/{string_id}/details/` - List string details
- **POST** `/api/{version}/workspaces/{workspace_id}/strings/{string_id}/details/` - Create string detail
- **GET** `/api/{version}/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/` - Get string detail
- **PATCH** `/api/{version}/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/` - Update string detail
- **DELETE** `/api/{version}/workspaces/{workspace_id}/strings/{string_id}/details/{detail_id}/` - Delete string detail

## Bulk Operations

### String Bulk Operations

- **POST** `/api/{version}/workspaces/{workspace_id}/strings/bulk/` - Bulk create strings
- **POST** `/api/{version}/workspaces/{workspace_id}/string-details/bulk/` - Bulk create string details
- **PATCH** `/api/{version}/workspaces/{workspace_id}/string-details/bulk/` - Bulk update string details
- **DELETE** `/api/{version}/workspaces/{workspace_id}/string-details/bulk/` - Bulk delete string details

### Multi-Operation Endpoint (Atomic Transactions)

- **POST** `/api/{version}/workspaces/{workspace_id}/multi-operations/execute/` - Execute multiple operations atomically
- **POST** `/api/{version}/workspaces/{workspace_id}/multi-operations/validate/` - Validate operations without executing

#### Supported Operation Types

**String Operations:**

- `create_string` - Create new string with details
- `update_string` - Update existing string
- `delete_string` - Delete string and related details
- `update_string_parent` - Update string parent relationship

**String Detail Operations:**

- `create_string_detail` - Create new string detail
- `update_string_detail` - Update existing string detail
- `delete_string_detail` - Delete string detail

**Submission Operations:**

- `create_submission` - Create new submission
- `update_submission` - Update existing submission
- `delete_submission` - Delete submission and related strings

#### Example Requests

**Individual Operations:**

```json
POST /api/v1/workspaces/1/multi-operations/execute/
{
  "operations": [
    {
      "type": "update_string_detail",
      "data": {"id": 154, "dimension_value": 3}
    },
    {
      "type": "update_string_detail",
      "data": {"id": 157, "dimension_value_freetext": "2"}
    },
    {
      "type": "update_string_parent",
      "data": {"string_id": 88, "parent_id": 45}
    }
  ]
}
```

**Grouped Array Operations (Recommended):**

```json
POST /api/v1/workspaces/1/multi-operations/execute/
{
  "operations": [
    {
      "type": "update_string_detail",
      "data": [
        {"id": 154, "dimension_value": 3},
        {"id": 157, "dimension_value_freetext": "2"}
      ]
    },
    {
      "type": "update_string_parent",
      "data": {"string_id": 88, "parent_id": 45}
    }
  ]
}
```

#### Transaction Guarantees

- **Atomicity**: All operations succeed or all fail (rollback)
- **Consistency**: Database integrity maintained across operations
- **Isolation**: Operations execute as a single transaction
- **Durability**: Changes are permanent once committed

### Submission String Bulk Operations

- **POST** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/bulk/` - Bulk add strings to submission
- **DELETE** `/api/{version}/workspaces/{workspace_id}/submissions/{submission_id}/strings/bulk/` - Bulk remove strings from submission

## Propagation System

### Propagation Jobs

- **GET** `/api/{version}/propagation-jobs/` - List propagation jobs
- **GET** `/api/{version}/propagation-jobs/{id}/` - Get propagation job details

### Propagation Errors

- **GET** `/api/{version}/propagation-errors/` - List propagation errors
- **POST** `/api/{version}/propagation-errors/` - Create propagation error
- **GET** `/api/{version}/propagation-errors/{id}/` - Get propagation error details
- **PUT** `/api/{version}/propagation-errors/{id}/` - Update propagation error
- **PATCH** `/api/{version}/propagation-errors/{id}/` - Partial update propagation error
- **DELETE** `/api/{version}/propagation-errors/{id}/` - Delete propagation error

### Enhanced String Details

- **GET** `/api/{version}/enhanced-string-details/` - List enhanced string details
- **POST** `/api/{version}/enhanced-string-details/` - Create enhanced string detail
- **GET** `/api/{version}/enhanced-string-details/{id}/` - Get enhanced string detail
- **PUT** `/api/{version}/enhanced-string-details/{id}/` - Update enhanced string detail
- **PATCH** `/api/{version}/enhanced-string-details/{id}/` - Partial update enhanced string detail
- **DELETE** `/api/{version}/enhanced-string-details/{id}/` - Delete enhanced string detail

### Propagation Settings

- **GET** `/api/{version}/propagation-settings/` - List propagation settings
- **POST** `/api/{version}/propagation-settings/` - Create propagation setting
- **GET** `/api/{version}/propagation-settings/{id}/` - Get propagation setting
- **PUT** `/api/{version}/propagation-settings/{id}/` - Update propagation setting
- **PATCH** `/api/{version}/propagation-settings/{id}/` - Partial update propagation setting
- **DELETE** `/api/{version}/propagation-settings/{id}/` - Delete propagation setting

## System and Utility Endpoints

### API Information

- **GET** `/api/{version}/version/` - Get API version information
- **GET** `/api/{version}/health/` - API health check
- **GET** `/api/{version}/demo/` - Version demo endpoint

### Documentation

- **GET** `/api/schema/` - OpenAPI schema
- **GET** `/api/schema/swagger-ui/` - Swagger UI documentation
- **GET** `/api/schema/redoc/` - ReDoc documentation

### Admin

- **GET** `/admin/` - Django admin interface

## Authentication and Permissions

### Required Authentication

- Most endpoints require JWT Bearer token authentication
- Token format: `Authorization: Bearer <token>`
- Workspace-scoped endpoints require valid workspace access permissions

### Permission Levels

- **Superuser**: Full access to all workspaces and endpoints
- **Workspace User**: Access limited to assigned workspaces
- **Anonymous**: Limited read-only access (if configured)

## Rate Limiting and Caching

### Rate Limiting

- Default rate limits apply to all endpoints
- Authentication endpoints may have stricter limits

### Caching

- Rule cache invalidation endpoints available
- Performance metrics endpoints for monitoring

## Error Handling

### Standard HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **500**: Internal Server Error

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": "ERROR_CODE"
}
```

## Notes

- All endpoints support API versioning (v1, v2)
- Workspace-scoped endpoints require valid workspace_id parameter
- Bulk operations are available for improved performance
- Propagation system provides automated data flow management
- Comprehensive caching and performance monitoring available
