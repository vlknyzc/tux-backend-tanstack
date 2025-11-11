# Tuxonomy API Documentation

**Version**: v1
**Base URL**: `https://api.tuxonomy.com/api/v1` (Production) or `http://localhost:8000/api/v1` (Development)
**Authentication**: JWT Bearer Token

---

## Table of Contents

1. [Authentication](./01-authentication.md) - Login, token refresh, user management
2. [Workspaces](./02-workspaces.md) - Multi-tenant workspace management
3. [Projects](./03-projects.md) - Project CRUD, team members, approval workflows
4. [Strings](./04-strings.md) - String generation, CRUD operations, bulk operations
5. [String Registry](./05-string-registry.md) - External platform string validation and import
6. [Platforms & Entities](./06-platforms-entities.md) - Platform and entity management
7. [Dimensions](./07-dimensions.md) - Dimension and dimension value management
8. [Rules](./08-rules.md) - Business rule configuration and validation
9. [Propagation](./09-propagation.md) - String propagation and inheritance

---

## Quick Start

### 1. Authentication

All API requests require a JWT token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

Get a token by calling the login endpoint:

```bash
POST /api/v1/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

### 2. Common Request Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json  # For JSON payloads
Accept: application/json
```

### 3. Response Format

All responses follow this structure:

**Success (200-299)**:
```json
{
  "id": 123,
  "name": "Resource Name",
  "created": "2024-11-11T12:00:00Z",
  ...
}
```

**Error (400-599)**:
```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Specific error for this field"]
  }
}
```

---

## API Design Principles

### 1. Resource-Based URLs

URLs are organized hierarchically by resource:

```
/api/v1/workspaces/{workspace_id}/
/api/v1/workspaces/{workspace_id}/projects/{project_id}/
/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/
```

### 2. HTTP Methods

- `GET` - Retrieve resource(s)
- `POST` - Create new resource
- `PUT` - Update entire resource
- `PATCH` - Update partial resource
- `DELETE` - Delete resource

### 3. Workspace Isolation

Most resources are scoped to a workspace. The `workspace_id` in the URL ensures multi-tenant data isolation.

### 4. Pagination

List endpoints support pagination:

```
GET /api/v1/workspaces/1/projects/?page=2&page_size=20
```

Response includes pagination metadata:
```json
{
  "count": 100,
  "next": "http://api.tuxonomy.com/api/v1/workspaces/1/projects/?page=3",
  "previous": "http://api.tuxonomy.com/api/v1/workspaces/1/projects/?page=1",
  "results": [...]
}
```

### 5. Filtering & Search

List endpoints support filtering via query parameters:

```
GET /api/v1/workspaces/1/strings/?platform_id=5&status=active&search=campaign
```

---

## Rate Limits

| Endpoint Category | Rate Limit |
|-------------------|------------|
| Authentication | 10 requests/minute |
| String Registry CSV Upload | 10 uploads/hour |
| String Validation (single) | 100 requests/hour |
| Standard CRUD operations | 1000 requests/hour |

---

## Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Postman Collection

Import the Postman collection for easy testing:

**File**: `string-registry.postman_collection.json`

**Environment Variables to Set**:
- `base_url`: API base URL (e.g., `http://localhost:8000/api/v1`)
- `jwt_token`: Your JWT authentication token
- `workspace_id`: Your workspace ID
- `project_id`: Your project ID
- `platform_id`: Platform ID for testing
- `rule_id`: Rule ID for testing

---

## Common Workflows

### Creating a New Project String

1. **Create Project** → See [Projects API](./03-projects.md)
2. **Assign Platform to Project** → Include in project creation
3. **Create Strings** → See [Strings API](./04-strings.md)
4. **Validate & Generate** → See [String Registry API](./05-string-registry.md)

### Importing External Platform Strings

1. **Prepare CSV** → See [String Registry API](./05-string-registry.md#csv-format)
2. **Validate Strings** → `POST /string-registry/validate/`
3. **Review Results** → Check batch results in admin or export
4. **Import to Project** → `POST /string-registry/import-selected/`

---

## Support

For questions or issues:
- **Documentation**: Check individual endpoint documentation
- **Schema**: Download OpenAPI schema from `/api/schema/`
- **Swagger UI**: View interactive docs at `/api/schema/swagger-ui/`
- **ReDoc**: View documentation at `/api/schema/redoc/`

---

## Changelog

### November 2024
- ✅ Refactored ProjectString → String
- ✅ Added String Registry validation endpoints
- ✅ Enhanced external platform string import
- ✅ Improved bulk operations performance
