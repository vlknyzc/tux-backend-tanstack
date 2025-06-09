# TUX Backend API Documentation

## Overview

The TUX Backend is a multi-tenant Django application that manages naming conventions and string generation for different clients. Each client has their own isolated workspace with data separation.

## Documentation Structure

### Core API Documentation

- **[API Overview & Authentication](api-overview.md)** - Basic API information, authentication, and multi-tenancy
- **[Development Setup](development-setup.md)** - CORS configuration, environment setup, and testing
- **[Migration Guide](migration-guide.md)** - Transitioning from subdomain-based to flexible workspace access

### API Endpoints

- **[User Management API](api-users.md)** - User accounts, authentication, and permissions
- **[Workspace Management API](api-workspaces.md)** - Workspaces and user assignments
- **[Platform & Fields API](api-platforms-fields.md)** - Platform and field hierarchy management
- **[Dimensions API](api-dimensions.md)** - Naming dimensions and dimension values
- **[Rules API](api-rules.md)** - Naming rules and rule configurations
- **[Strings API](api-strings.md)** - String generation and management

## Quick Start

1. **Authentication**: All API endpoints require authentication via JWT tokens or session authentication
2. **Base URL**: `http://localhost:8000/api/v1/` (development) or `https://yourdomain.com/api/v1/` (production)
3. **Workspace Access**: Users are assigned to workspaces with specific roles (admin, user, viewer)
4. **API Versioning**: Use versioned endpoints (`/api/v1/`) for all requests

## Key Features

- **Flexible Workspace Access**: No longer requires subdomain-based routing
- **Role-Based Permissions**: Granular access control within workspaces
- **Global Resources**: Platforms and fields shared across workspaces
- **Complete CRUD Operations**: Full GET, POST, PUT, PATCH, DELETE support
- **CORS Ready**: Configured for frontend integration

## API Standards

### Request Format

```http
GET /api/v1/endpoint/
Authorization: Bearer your-jwt-token
Content-Type: application/json
```

### Response Format

```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Example",
      "created": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### HTTP Status Codes

- `200 OK` - Successful GET/PUT/PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found

## Support

- **API Issues**: Check the troubleshooting sections in each documentation file
- **Development**: See [Development Setup](development-setup.md) for local development
- **Migration**: See [Migration Guide](migration-guide.md) for upgrading from older versions

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
_Documentation: Modular Structure_
