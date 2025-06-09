# User Management API

## Overview

Manage users and their workspace assignments. User management is restricted based on roles:

- **Superusers**: Can manage all users and assignments
- **Workspace Admins**: Can manage users within their workspaces
- **Regular Users**: Can view users in their workspaces and update their own profile

## Base URL

```
/api/v1/users/
```

## User Endpoints

### List Users

```http
GET /api/v1/users/
Authorization: Bearer your-jwt-token
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

### Get User Details

```http
GET /api/v1/users/{user_id}/
Authorization: Bearer your-jwt-token
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

### Create User (Superuser Only)

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

### Update User (Partial Update)

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

### Update User (Full Update)

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

### Delete User (Superuser Only)

```http
DELETE /api/v1/users/{user_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

**Note**: Deleting a user will also remove all their workspace assignments.

### Get User Authorizations

```http
GET /api/v1/users/{user_id}/authorizations/
Authorization: Bearer your-jwt-token
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

### Get Current User Info

```http
GET /api/v1/users/me/
Authorization: Bearer your-jwt-token
```

Returns the current authenticated user's information.

## Workspace-User Assignments

### Base URL

```
/api/v1/workspace-users/
```

Manage user assignments to workspaces and their roles.

### List Workspace Assignments

```http
GET /api/v1/workspace-users/
Authorization: Bearer your-jwt-token
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

### Get Workspace Assignment Details

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

### Assign User to Workspace

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

### Update User Role in Workspace (Partial Update)

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

### Update User Assignment (Full Update)

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

### Remove User from Workspace

```http
DELETE /api/v1/workspace-users/{assignment_id}/
Authorization: Bearer your-jwt-token
```

**Response (204 No Content):** Empty body

### Bulk Assign Users (Superuser Only)

```http
POST /api/v1/workspace-users/bulk_assign/
Authorization: Bearer your-jwt-token
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

### Workspace Assignment Summary

```http
GET /api/v1/workspace-users/workspace_summary/
Authorization: Bearer your-jwt-token
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

## User Roles & Permissions

### Role Types

- **admin**: Full management access within the workspace

  - Can create/update/delete all workspace data
  - Can manage other users within the workspace
  - Can configure workspace settings

- **user**: Read/write access to workspace data

  - Can create/update their own data
  - Can read all workspace data
  - Cannot manage other users

- **viewer**: Read-only access to workspace data
  - Can only view workspace data
  - Cannot create or modify any data

### Permission Matrix

| Action              | Superuser | Workspace Admin  | User               | Viewer       |
| ------------------- | --------- | ---------------- | ------------------ | ------------ |
| List users          | ✅ All    | ✅ Workspace     | ✅ Workspace       | ✅ Workspace |
| View user details   | ✅ All    | ✅ Workspace     | ✅ Own + Workspace | ✅ Workspace |
| Create user         | ✅ All    | ❌               | ❌                 | ❌           |
| Update user         | ✅ All    | ✅ Workspace     | ✅ Own             | ❌           |
| Delete user         | ✅ All    | ❌               | ❌                 | ❌           |
| Assign to workspace | ✅ All    | ✅ Own workspace | ❌                 | ❌           |
| Change user role    | ✅ All    | ✅ Own workspace | ❌                 | ❌           |

## Error Handling

### Common Errors

#### User Not Found (404)

```json
{
  "error": "User not found",
  "details": "User with ID 999 does not exist"
}
```

#### Insufficient Permissions (403)

```json
{
  "error": "Access denied",
  "details": "You don't have permission to modify this user"
}
```

#### Duplicate Email (400)

```json
{
  "error": "Validation failed",
  "field_errors": {
    "email": ["User with this email already exists."]
  }
}
```

#### Invalid Workspace Assignment (400)

```json
{
  "error": "Invalid workspace assignment",
  "details": "User cannot be assigned to workspace they already belong to"
}
```

### Validation Rules

- **Email**: Must be unique and valid format
- **Password**: Minimum 8 characters (on creation)
- **Role**: Must be one of: admin, user, viewer
- **Workspace**: Must exist and be accessible to requesting user

---

_Last Updated: 2025-06-08_
_API Version: 1.0_
