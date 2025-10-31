# Projects API - Frontend Integration Guide

**Version:** 1.0
**Last Updated:** 2025-10-31
**Base URL:** `/api/v1`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Project Management](#project-management)
6. [Project Approval](#project-approval)
7. [Platform Approval](#platform-approval)
8. [String Operations](#string-operations)
9. [Advanced Features (Phase 3)](#advanced-features-phase-3)
10. [TypeScript Types](#typescript-types)
11. [Code Examples](#code-examples)

---

## Overview

The Projects API provides complete project lifecycle management including:
- ✅ Project CRUD operations
- ✅ Team member management with roles
- ✅ Platform assignment to projects
- ✅ String generation within projects
- ✅ Dual-level approval workflow (project + platform)
- ✅ Activity tracking and audit trail
- ✅ Unlock, bulk update, and export capabilities

### Key Concepts

- **Project**: Container for organizing strings by platform
- **Platform Assignment**: Links a platform to a project
- **Project Member**: Team member with role (owner/editor/viewer)
- **Project String**: Generated naming string within a project/platform
- **Approval Workflow**: Draft → Pending → Approved/Rejected

---

## Authentication

All endpoints require JWT authentication.

```typescript
// Add token to request headers
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

**Permissions**:
- **Workspace Member**: Can view projects in their workspace
- **Project Owner/Editor**: Can create/update/delete strings
- **Workspace Admin**: Can approve/reject projects and platforms
- **Superuser**: Full access to everything

---

## Common Patterns

### URL Structure

All endpoints follow this pattern:
```
/api/v1/workspaces/{workspaceId}/projects/{projectId}/...
```

### Pagination

List endpoints return paginated results:

```typescript
{
  "count": 100,           // Total count
  "next": 2,             // Next page number (null if last page)
  "previous": null,      // Previous page number (null if first page)
  "results": [...]       // Array of results
}
```

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20 for projects, 50 for strings)

### Field Naming

- **API**: Uses `snake_case` (e.g., `created_by`, `platform_id`)
- **Frontend**: Convert to `camelCase` (e.g., `createdBy`, `platformId`)

### Timestamps

All timestamps are in ISO 8601 format:
```
"2025-10-31T14:30:00Z"
```

---

## Error Handling

### Standard Error Response

```typescript
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "details": {
    // Additional error context
  }
}
```

### HTTP Status Codes

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| `200` | OK | Successful GET/PUT/PATCH |
| `201` | Created | Successful POST |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Validation errors, invalid data |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | User doesn't have permission |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Duplicate or circular reference |
| `500` | Server Error | Internal server error |

### Common Errors

**Validation Error** (400):
```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": [
    {
      "field": "name",
      "code": "required",
      "message": "Name is required"
    }
  ]
}
```

**Permission Error** (403):
```json
{
  "error": "Permission Denied",
  "message": "You do not have permission to perform this action",
  "required_role": "owner"
}
```

**Conflict Error** (409):
```json
{
  "error": "Conflict",
  "message": "String has children and cannot be deleted",
  "details": {
    "string_id": 1,
    "children_count": 3
  }
}
```

---

## Project Management

### 1. List Projects

**Endpoint**: `GET /api/v1/workspaces/{workspaceId}/projects/`

**Query Parameters**:
- `status`: Filter by status (`planning`, `active`, `completed`, `archived`)
- `search`: Search by name or description
- `page`: Page number
- `page_size`: Items per page

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/?status=active&page=1&page_size=20
```

**Response** (200 OK):
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Black Friday 2024",
      "slug": "black-friday-2024",
      "description": "Annual Black Friday campaign...",
      "status": "active",
      "start_date": "2024-11-15T00:00:00Z",
      "end_date": "2024-11-29T00:00:00Z",
      "owner_id": 1,
      "owner_name": "Alice Johnson",
      "workspace": 1,
      "platform_assignments": [
        {
          "id": 1,
          "platform_id": 1,
          "platform_name": "Google Ads",
          "platform_slug": "google-ads",
          "assigned_members": [1],
          "string_count": 4,
          "last_updated": "2024-10-25T14:30:00Z",
          "approval_status": "draft"
        }
      ],
      "team_members": [
        {
          "user": {
            "id": 1,
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "avatar": null
          },
          "role": "owner"
        }
      ],
      "stats": {
        "total_strings": 10,
        "platforms_count": 3,
        "team_members_count": 3,
        "last_activity": "2024-10-26T09:15:00Z"
      },
      "created": "2024-10-15T10:00:00Z",
      "last_updated": "2024-10-26T09:15:00Z",
      "approval_status": "draft"
    }
  ]
}
```

---

### 2. Get Project Detail

**Endpoint**: `GET /api/v1/workspaces/{workspaceId}/projects/{projectId}/`

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/1/
```

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "Black Friday 2024",
  "slug": "black-friday-2024",
  "description": "Annual Black Friday campaign...",
  "status": "active",
  "start_date": "2024-11-15T00:00:00Z",
  "end_date": "2024-11-29T00:00:00Z",
  "owner_id": 1,
  "owner_name": "Alice Johnson",
  "workspace": 1,
  "platform_assignments": [...],
  "team_members": [...],
  "stats": {...},
  "created": "2024-10-15T10:00:00Z",
  "last_updated": "2024-10-26T09:15:00Z",
  "approval_status": "draft",
  "approval_history": [],
  "strings": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "Black Friday 2024",
      "platform_id": 1,
      "platform_name": "Google Ads",
      "field_id": 62,
      "field_name": "Campaign Name",
      "value": "Black Friday Sale 2024",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent_uuid": null,
      "rule": {
        "id": 3,
        "name": "Google Ads Campaign Rule"
      },
      "created_by": 1,
      "created_by_name": "Alice Johnson",
      "created": "2024-10-25T14:30:00Z",
      "last_updated": "2024-10-25T14:30:00Z",
      "field_level": 1
    }
  ],
  "activities": [
    {
      "id": 1,
      "project_id": 1,
      "type": "project_created",
      "description": "created the project",
      "user_id": 1,
      "user_name": "Alice Johnson",
      "user_avatar": null,
      "metadata": null,
      "created": "2024-10-15T10:00:00Z"
    }
  ]
}
```

---

### 3. Create Project

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/`

**Request Body**:
```json
{
  "name": "Summer Sale 2025",
  "description": "Planning phase for summer promotional campaign",
  "status": "planning",
  "start_date": "2025-06-01",
  "end_date": "2025-06-30",
  "workspace": 1,
  "platform_assignments": [
    {
      "platform_id": 1,
      "assigned_members": [1, 2]
    },
    {
      "platform_id": 2,
      "assigned_members": [2]
    }
  ],
  "team_members": [
    {
      "user_id": 1,
      "role": "owner"
    },
    {
      "user_id": 2,
      "role": "editor"
    }
  ]
}
```

**Validation Rules**:
- `name`: Required, 3-100 characters
- `description`: Optional, max 500 characters
- `status`: Must be one of: `planning`, `active`, `completed`, `archived`
- `end_date`: Must be >= `start_date` if both provided
- `team_members`: Must include at least one member with role `owner`

**Response** (201 Created):
```json
{
  "id": 4,
  "name": "Summer Sale 2025",
  "slug": "summer-sale-2025",
  "description": "Planning phase for summer promotional campaign",
  "status": "planning",
  "start_date": "2025-06-01T00:00:00Z",
  "end_date": "2025-06-30T00:00:00Z",
  "owner_id": 1,
  "owner_name": "Alice Johnson",
  "workspace": 1,
  "platform_assignments": [...],
  "team_members": [...],
  "stats": {
    "total_strings": 0,
    "platforms_count": 2,
    "team_members_count": 2,
    "last_activity": null
  },
  "created": "2025-10-31T10:00:00Z",
  "last_updated": "2025-10-31T10:00:00Z",
  "approval_status": "draft"
}
```

---

### 4. Update Project

**Endpoint**: `PUT /api/v1/workspaces/{workspaceId}/projects/{projectId}/`

**Request Body** (all fields optional):
```json
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "status": "active",
  "start_date": "2025-06-01",
  "end_date": "2025-06-30",
  "platform_assignments": [
    {
      "platform_id": 1,
      "assigned_members": [1, 2, 3]
    }
  ],
  "team_members": [
    {
      "user_id": 1,
      "role": "owner"
    },
    {
      "user_id": 2,
      "role": "editor"
    }
  ]
}
```

**Restrictions**:
- Cannot update if `approval_status` is `approved` (must unlock first)
- Cannot change `workspace` or `owner_id`

**Response** (200 OK): Same structure as Get Project Detail

---

### 5. Delete Project

**Endpoint**: `DELETE /api/v1/workspaces/{workspaceId}/projects/{projectId}/`

**Permissions**: Only project owners or workspace admins

**Response** (204 No Content): Empty body

**Side Effects**:
- Deletes all related strings (cascade)
- Deletes all platform assignments (cascade)
- Deletes all team members (cascade)
- Deletes all activities (cascade)
- Deletes all approval history (cascade)

---

## Project Approval

### 6. Submit Project for Approval

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/submit-for-approval/`

**Permissions**: Project owners or editors

**Requirements**: Project must be in `draft` or `rejected` status

**Request Body** (optional):
```json
{
  "comment": "Ready for review"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "approval_status": "pending_approval",
  "submitted_at": "2025-10-31T10:00:00Z",
  "submitted_by": 1
}
```

---

### 7. Approve Project

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/approve/`

**Permissions**: Workspace admins only

**Requirements**: Project must be in `pending_approval` status

**Request Body** (optional):
```json
{
  "comment": "Looks good!"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "approval_status": "approved",
  "approved_at": "2025-10-31T10:00:00Z",
  "approved_by": 2
}
```

---

### 8. Reject Project

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/reject/`

**Permissions**: Workspace admins only

**Requirements**: Project must be in `pending_approval` status

**Request Body** (required):
```json
{
  "reason": "Needs more details"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "approval_status": "rejected",
  "rejected_at": "2025-10-31T10:00:00Z",
  "rejected_by": 2,
  "rejection_reason": "Needs more details"
}
```

---

## Platform Approval

### 9. Submit Platform for Approval

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/submit-for-approval/`

**Permissions**: Platform assigned members OR project owners/editors

**Requirements**: Platform must be in `draft` or `rejected` status

**Request Body** (optional):
```json
{
  "comment": "Ready for review"
}
```

**Response** (200 OK):
```json
{
  "platform_assignment_id": 1,
  "approval_status": "pending_approval",
  "submitted_at": "2025-10-31T10:00:00Z",
  "submitted_by": 1
}
```

---

### 10. Approve Platform

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/approve/`

**Permissions**: Workspace admins only

**Requirements**: Platform must be in `pending_approval` status

**Request Body** (optional):
```json
{
  "comment": "Approved"
}
```

**Response** (200 OK):
```json
{
  "platform_assignment_id": 1,
  "approval_status": "approved",
  "approved_at": "2025-10-31T10:00:00Z",
  "approved_by": 2
}
```

---

### 11. Reject Platform

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/reject/`

**Permissions**: Workspace admins only

**Requirements**: Platform must be in `pending_approval` status

**Request Body** (required):
```json
{
  "reason": "Strings need review"
}
```

**Response** (200 OK):
```json
{
  "platform_assignment_id": 1,
  "approval_status": "rejected",
  "rejected_at": "2025-10-31T10:00:00Z",
  "rejected_by": 2,
  "rejection_reason": "Strings need review"
}
```

---

## String Operations

### 12. Bulk Create Strings

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk`

**Permissions**: Platform assigned members OR project owners/editors

**Request Body**:
```json
{
  "rule": 3,
  "starting_field": 62,
  "strings": [
    {
      "field": 62,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent_uuid": null,
      "value": "Black Friday Sale 2024",
      "details": [
        {
          "dimension": 1,
          "dimension_value": 5,
          "dimension_value_freetext": null
        },
        {
          "dimension": 2,
          "dimension_value": null,
          "dimension_value_freetext": "2024"
        }
      ]
    },
    {
      "field": 63,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "value": "Black Friday Sale 2024 - Ad Set 1",
      "details": [
        {
          "dimension": 1,
          "dimension_value": 5,
          "dimension_value_freetext": null
        },
        {
          "dimension": 2,
          "dimension_value": null,
          "dimension_value_freetext": "2024"
        },
        {
          "dimension": 3,
          "dimension_value": 10,
          "dimension_value_freetext": null
        }
      ]
    }
  ]
}
```

**Validation Rules**:
- `rule`: Must reference a valid Rule
- `starting_field`: Must belong to the rule's platform
- All `field` values must belong to the specified rule
- `parent_uuid`: Must reference a string in the **same platform** (or be null for level 1)
- `string_uuid`: Must be globally unique (use UUID4)
- For list dimensions: `dimension_value` must be set, `dimension_value_freetext` must be null
- For text dimensions: `dimension_value_freetext` must be set, `dimension_value` must be null

**Response** (201 Created):
```json
{
  "created_count": 2,
  "strings": [
    {
      "id": 1,
      "project_id": 1,
      "platform_id": 1,
      "field_id": 62,
      "rule_id": 3,
      "value": "Black Friday Sale 2024",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent_uuid": null,
      "created_by": 1,
      "created": "2025-10-31T10:00:00Z",
      "last_updated": "2025-10-31T10:00:00Z"
    },
    {
      "id": 2,
      "project_id": 1,
      "platform_id": 1,
      "field_id": 63,
      "rule_id": 3,
      "value": "Black Friday Sale 2024 - Ad Set 1",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "created_by": 1,
      "created": "2025-10-31T10:00:00Z",
      "last_updated": "2025-10-31T10:00:00Z"
    }
  ]
}
```

**Important Notes**:
- Frontend must generate UUIDs before sending (use `crypto.randomUUID()` or `uuid` library)
- Strings are created in order by field level (parents before children)
- Platform approval status does NOT block creation (can add strings incrementally)

---

### 13. List Strings for Platform

**Endpoint**: `GET /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings`

**Query Parameters**:
- `field`: Filter by field ID
- `parent_field`: Filter by parent field ID (returns parent strings for a given field level)
- `parent_uuid`: Filter by parent UUID (returns children of a specific parent)
- `search`: Search by string value
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50)

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/1/platforms/1/strings?field=62&page=1
```

**Response** (200 OK):
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "Black Friday 2024",
      "platform_id": 1,
      "platform_name": "Google Ads",
      "field_id": 62,
      "field_name": "Campaign Name",
      "rule_id": 3,
      "rule_name": "Google Ads Campaign Rule",
      "value": "Black Friday Sale 2024",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent_uuid": null,
      "created_by": 1,
      "created_by_name": "Alice Johnson",
      "created": "2024-10-25T14:30:00Z",
      "last_updated": "2024-10-25T14:30:00Z",
      "field_level": 1,
      "details": [
        {
          "id": 1,
          "dimension": 1,
          "dimension_name": "Campaign Type",
          "dimension_type": "list",
          "dimension_value_id": 5,
          "dimension_value_freetext": null,
          "dimension_value_display": "Sale",
          "dimension_value_label": "Sale Campaign",
          "is_inherited": false
        },
        {
          "id": 2,
          "dimension": 2,
          "dimension_name": "Year",
          "dimension_type": "text",
          "dimension_value_id": null,
          "dimension_value_freetext": "2024",
          "dimension_value_display": "2024",
          "dimension_value_label": "2024",
          "is_inherited": false
        }
      ]
    }
  ]
}
```

---

### 14. Get String Expanded Details

**Endpoint**: `GET /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/expanded`

**Use Case**: When user selects a parent string in grid builder, fetch expanded details to populate inherited dimension values

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/1/platforms/1/strings/1/expanded
```

**Response** (200 OK):
```json
{
  "id": 1,
  "project_id": 1,
  "project_name": "Black Friday 2024",
  "platform_id": 1,
  "platform_name": "Google Ads",
  "platform_slug": "google-ads",
  "field_id": 62,
  "field_name": "Campaign Name",
  "field_level": 1,
  "rule_id": 3,
  "rule_name": "Google Ads Campaign Rule",
  "value": "Black Friday Sale 2024",
  "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "parent_uuid": null,
  "created_by": 1,
  "created_by_name": "Alice Johnson",
  "created": "2024-10-25T14:30:00Z",
  "last_updated": "2024-10-25T14:30:00Z",
  "details": [
    {
      "id": 1,
      "dimension": 1,
      "dimension_id": 1,
      "dimension_name": "Campaign Type",
      "dimension_type": "list",
      "dimension_value": 5,
      "dimension_value_id": 5,
      "dimension_value_freetext": null,
      "dimension_value_display": "Sale",
      "dimension_value_label": "Sale Campaign",
      "is_inherited": false
    }
  ],
  "hierarchy_path": [
    {
      "id": 1,
      "value": "Black Friday Sale 2024",
      "field_level": 1
    }
  ],
  "can_have_children": true,
  "suggested_child_field": {
    "id": 63,
    "name": "Ad Set Name",
    "field_level": 2
  }
}
```

---

### 15. Update String

**Endpoint**: `PUT /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}`

**Permissions**: Platform assigned members OR project owners/editors

**Request Body**:
```json
{
  "value": "Updated Campaign Name",
  "details": [
    {
      "dimension": 1,
      "dimension_value": 6,
      "dimension_value_freetext": null
    },
    {
      "dimension": 2,
      "dimension_value": null,
      "dimension_value_freetext": "2025"
    }
  ]
}
```

**Response** (200 OK): Same structure as Get String Expanded Details

**Note**: Platform approval status does NOT block updates (for now)

---

### 16. Delete String

**Endpoint**: `DELETE /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/delete`

**Permissions**: Platform assigned members OR project owners/editors

**Restrictions**: Cannot delete if string has children

**Response** (204 No Content): Empty body

**Error Response** (409 Conflict):
```json
{
  "error": "Conflict",
  "message": "String has children and cannot be deleted",
  "details": {
    "string_id": 1,
    "children_count": 3
  }
}
```

---

## Advanced Features (Phase 3)

### 17. Unlock String for Editing

**Endpoint**: `POST /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/unlock`

**Permissions**: Platform assigned members OR project owners/editors

**Requirements**: Platform must be in `approved` status

**Use Case**: Allow editing strings from approved platforms by unlocking them

**Request Body** (optional):
```json
{
  "reason": "Need to update campaign name"
}
```

**Response** (200 OK):
```json
{
  "string_id": 1,
  "unlocked_at": "2025-10-31T10:00:00Z",
  "unlocked_by": 1,
  "platform_status_changed": true,
  "new_platform_status": "draft",
  "message": "String unlocked successfully. Platform status changed to draft and requires re-approval."
}
```

**Side Effects**:
- Platform status changes from `approved` → `draft`
- Platform requires re-approval after changes
- Creates activity log with unlock reason

---

### 18. Bulk Update Strings

**Endpoint**: `PUT /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk-update`

**Permissions**: Platform assigned members OR project owners/editors

**Use Case**: Update multiple strings efficiently in a single request

**Request Body**:
```json
{
  "updates": [
    {
      "id": 1,
      "value": "Updated String Value",
      "details": [
        {
          "dimension": 1,
          "dimension_value": 5,
          "dimension_value_freetext": null
        }
      ]
    },
    {
      "id": 2,
      "value": "Another Updated Value",
      "details": [
        {
          "dimension": 1,
          "dimension_value": 6,
          "dimension_value_freetext": null
        }
      ]
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "updated_count": 2,
  "error_count": 0,
  "updated_strings": [
    {
      "id": 1,
      "value": "Updated String Value",
      // ... full string details
    },
    {
      "id": 2,
      "value": "Another Updated Value",
      // ... full string details
    }
  ],
  "errors": []
}
```

**Error Response** (partial failure):
```json
{
  "updated_count": 1,
  "error_count": 1,
  "updated_strings": [...],
  "errors": [
    {
      "string_id": 2,
      "error": "String not found"
    }
  ]
}
```

**Important Notes**:
- Uses atomic transaction (all succeed or all fail)
- Individual error tracking per string
- Creates single activity log for the operation

---

### 19. Export Strings

**Endpoint**: `GET /api/v1/workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/export`

**Query Parameters**:
- `format`: `csv` or `json` (default: `csv`)

**Permissions**: Any workspace member (read-only operation)

**Use Case**: Export project strings for analysis in Excel or other tools

#### CSV Export

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/1/platforms/1/strings/export?format=csv
```

**Response** (200 OK):
- **Content-Type**: `text/csv`
- **Content-Disposition**: `attachment; filename="project_1_platform_1_strings.csv"`

**CSV Structure**:
```csv
String ID,UUID,Project,Platform,Field,Field Level,Value,Parent UUID,Rule,Created By,Created,Last Updated
1,550e8400-e29b-41d4-a716-446655440000,Black Friday 2024,Google Ads,Campaign Name,1,Black Friday Sale 2024,,Google Ads Campaign Rule,Alice Johnson,2024-10-25T14:30:00Z,2024-10-25T14:30:00Z
2,550e8400-e29b-41d4-a716-446655440001,Black Friday 2024,Google Ads,Ad Set Name,2,Black Friday Sale 2024 - Ad Set 1,550e8400-e29b-41d4-a716-446655440000,Google Ads Campaign Rule,Alice Johnson,2024-10-25T14:30:00Z,2024-10-25T14:30:00Z
```

#### JSON Export

**Request**:
```typescript
GET /api/v1/workspaces/1/projects/1/platforms/1/strings/export?format=json
```

**Response** (200 OK):
- **Content-Type**: `application/json`
- **Content-Disposition**: `attachment; filename="project_1_platform_1_strings.json"`

```json
{
  "project": {
    "id": 1,
    "name": "Black Friday 2024",
    "slug": "black-friday-2024"
  },
  "platform": {
    "id": 1,
    "name": "Google Ads"
  },
  "exported_at": "2025-10-31T10:00:00Z",
  "count": 10,
  "strings": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "Black Friday 2024",
      "platform_id": 1,
      "platform_name": "Google Ads",
      "field_id": 62,
      "field_name": "Campaign Name",
      "value": "Black Friday Sale 2024",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent_uuid": null,
      "created_by": 1,
      "created_by_name": "Alice Johnson",
      "created": "2024-10-25T14:30:00Z",
      "last_updated": "2024-10-25T14:30:00Z",
      "field_level": 1,
      "details": [...]
    }
  ]
}
```

---

## TypeScript Types

```typescript
// ============================================================================
// ENUMS
// ============================================================================

export enum ProjectStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
}

export enum ApprovalStatus {
  DRAFT = 'draft',
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum ProjectMemberRole {
  OWNER = 'owner',
  EDITOR = 'editor',
  VIEWER = 'viewer',
}

export enum ProjectActivityType {
  PROJECT_CREATED = 'project_created',
  PLATFORM_ADDED = 'platform_added',
  PLATFORM_REMOVED = 'platform_removed',
  MEMBER_ASSIGNED = 'member_assigned',
  MEMBER_UNASSIGNED = 'member_unassigned',
  STRINGS_GENERATED = 'strings_generated',
  STATUS_CHANGED = 'status_changed',
  PROJECT_UPDATED = 'project_updated',
  SUBMITTED_FOR_APPROVAL = 'submitted_for_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

// ============================================================================
// MODELS
// ============================================================================

export interface User {
  id: number;
  name: string;
  email: string;
  avatar: string | null;
}

export interface ProjectMember {
  user: User;
  role: ProjectMemberRole;
}

export interface PlatformAssignment {
  id: number;
  platform_id: number;
  platform_name: string;
  platform_slug: string;
  assigned_members: number[];
  string_count: number;
  last_updated: string;
  approval_status: ApprovalStatus;
  approved_by?: number;
  approved_at?: string;
  rejected_by?: number;
  rejected_at?: string;
  rejection_reason?: string;
  approval_history?: ApprovalHistoryEntry[];
}

export interface ProjectStats {
  total_strings: number;
  platforms_count: number;
  team_members_count: number;
  last_activity: string | null;
}

export interface Project {
  id: number;
  name: string;
  slug: string;
  description: string;
  status: ProjectStatus;
  start_date: string | null;
  end_date: string | null;
  owner_id: number;
  owner_name: string;
  workspace: number;
  platform_assignments: PlatformAssignment[];
  team_members: ProjectMember[];
  stats: ProjectStats;
  created: string;
  last_updated: string;
  approval_status: ApprovalStatus;
}

export interface ProjectDetail extends Project {
  strings: ProjectString[];
  activities: ProjectActivity[];
  approval_history: ApprovalHistoryEntry[];
}

export interface ProjectActivity {
  id: number;
  project_id: number;
  type: ProjectActivityType;
  description: string;
  user_id: number | null;
  user_name: string | null;
  user_avatar: string | null;
  metadata: Record<string, any> | null;
  created: string;
}

export interface ApprovalHistoryEntry {
  id: number;
  action: 'submitted' | 'approved' | 'rejected';
  comment: string;
  timestamp: string;
  user_id: number | null;
  user_name: string | null;
}

export interface ProjectStringDetail {
  id: number;
  dimension: number;
  dimension_name: string;
  dimension_type: 'list' | 'text';
  dimension_value_id: number | null;
  dimension_value_freetext: string | null;
  dimension_value_display: string;
  dimension_value_label: string;
  is_inherited: boolean;
}

export interface ProjectString {
  id: number;
  project_id: number;
  project_name: string;
  platform_id: number;
  platform_name: string;
  field_id: number;
  field_name: string;
  field_level: number;
  rule_id: number;
  rule_name: string;
  value: string;
  string_uuid: string;
  parent_uuid: string | null;
  created_by: number | null;
  created_by_name: string | null;
  created: string;
  last_updated: string;
  details: ProjectStringDetail[];
}

export interface ProjectStringExpanded extends ProjectString {
  hierarchy_path: Array<{
    id: number;
    value: string;
    field_level: number;
  }>;
  can_have_children: boolean;
  suggested_child_field: {
    id: number;
    name: string;
    field_level: number;
  } | null;
}

// ============================================================================
// API REQUEST TYPES
// ============================================================================

export interface CreateProjectRequest {
  name: string;
  description?: string;
  status: ProjectStatus;
  start_date?: string;
  end_date?: string;
  workspace: number;
  platform_assignments?: Array<{
    platform_id: number;
    assigned_members?: number[];
  }>;
  team_members: Array<{
    user_id: number;
    role: ProjectMemberRole;
  }>;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  status?: ProjectStatus;
  start_date?: string;
  end_date?: string;
  platform_assignments?: Array<{
    platform_id: number;
    assigned_members?: number[];
  }>;
  team_members?: Array<{
    user_id: number;
    role: ProjectMemberRole;
  }>;
}

export interface BulkCreateStringsRequest {
  rule: number;
  starting_field: number;
  strings: Array<{
    field: number;
    string_uuid: string;
    parent_uuid?: string;
    value: string;
    details: Array<{
      dimension: number;
      dimension_value?: number;
      dimension_value_freetext?: string;
    }>;
  }>;
}

export interface UpdateStringRequest {
  value: string;
  details: Array<{
    dimension: number;
    dimension_value?: number;
    dimension_value_freetext?: string;
  }>;
}

export interface BulkUpdateStringsRequest {
  updates: Array<{
    id: number;
    value: string;
    details: Array<{
      dimension: number;
      dimension_value?: number;
      dimension_value_freetext?: string;
    }>;
  }>;
}

export interface SubmitForApprovalRequest {
  comment?: string;
}

export interface ApproveRequest {
  comment?: string;
}

export interface RejectRequest {
  reason: string;
}

export interface UnlockStringRequest {
  reason?: string;
}

// ============================================================================
// API RESPONSE TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  count: number;
  next: number | null;
  previous: number | null;
  results: T[];
}

export interface BulkCreateStringsResponse {
  created_count: number;
  strings: ProjectString[];
}

export interface BulkUpdateStringsResponse {
  updated_count: number;
  error_count: number;
  updated_strings: ProjectString[];
  errors: Array<{
    string_id?: number;
    error: string;
    data?: any;
  }>;
}

export interface ApprovalResponse {
  id: number;
  approval_status: ApprovalStatus;
  submitted_at?: string;
  submitted_by?: number;
  approved_at?: string;
  approved_by?: number;
  rejected_at?: string;
  rejected_by?: number;
  rejection_reason?: string;
}

export interface UnlockStringResponse {
  string_id: number;
  unlocked_at: string;
  unlocked_by: number;
  platform_status_changed: boolean;
  new_platform_status: string;
  message: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: any;
}
```

---

## Code Examples

### React/TypeScript Example

```typescript
import axios from 'axios';

// ============================================================================
// API CLIENT SETUP
// ============================================================================

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============================================================================
// API FUNCTIONS
// ============================================================================

// List projects
export const listProjects = async (
  workspaceId: number,
  params?: {
    status?: ProjectStatus;
    search?: string;
    page?: number;
    page_size?: number;
  }
): Promise<PaginatedResponse<Project>> => {
  const response = await api.get(`/workspaces/${workspaceId}/projects/`, {
    params,
  });
  return response.data;
};

// Get project detail
export const getProject = async (
  workspaceId: number,
  projectId: number
): Promise<ProjectDetail> => {
  const response = await api.get(
    `/workspaces/${workspaceId}/projects/${projectId}/`
  );
  return response.data;
};

// Create project
export const createProject = async (
  workspaceId: number,
  data: CreateProjectRequest
): Promise<Project> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/`,
    data
  );
  return response.data;
};

// Update project
export const updateProject = async (
  workspaceId: number,
  projectId: number,
  data: UpdateProjectRequest
): Promise<Project> => {
  const response = await api.put(
    `/workspaces/${workspaceId}/projects/${projectId}/`,
    data
  );
  return response.data;
};

// Delete project
export const deleteProject = async (
  workspaceId: number,
  projectId: number
): Promise<void> => {
  await api.delete(`/workspaces/${workspaceId}/projects/${projectId}/`);
};

// Submit project for approval
export const submitProjectForApproval = async (
  workspaceId: number,
  projectId: number,
  data?: SubmitForApprovalRequest
): Promise<ApprovalResponse> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/${projectId}/submit-for-approval/`,
    data || {}
  );
  return response.data;
};

// Approve project
export const approveProject = async (
  workspaceId: number,
  projectId: number,
  data?: ApproveRequest
): Promise<ApprovalResponse> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/${projectId}/approve/`,
    data || {}
  );
  return response.data;
};

// Reject project
export const rejectProject = async (
  workspaceId: number,
  projectId: number,
  data: RejectRequest
): Promise<ApprovalResponse> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/${projectId}/reject/`,
    data
  );
  return response.data;
};

// Bulk create strings
export const bulkCreateStrings = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  data: BulkCreateStringsRequest
): Promise<BulkCreateStringsResponse> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/bulk`,
    data
  );
  return response.data;
};

// List strings
export const listStrings = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  params?: {
    field?: number;
    parent_field?: number;
    parent_uuid?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }
): Promise<PaginatedResponse<ProjectString>> => {
  const response = await api.get(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings`,
    { params }
  );
  return response.data;
};

// Get string expanded
export const getStringExpanded = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  stringId: number
): Promise<ProjectStringExpanded> => {
  const response = await api.get(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}/expanded`
  );
  return response.data;
};

// Update string
export const updateString = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  stringId: number,
  data: UpdateStringRequest
): Promise<ProjectStringExpanded> => {
  const response = await api.put(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}`,
    data
  );
  return response.data;
};

// Delete string
export const deleteString = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  stringId: number
): Promise<void> => {
  await api.delete(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}/delete`
  );
};

// Unlock string
export const unlockString = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  stringId: number,
  data?: UnlockStringRequest
): Promise<UnlockStringResponse> => {
  const response = await api.post(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}/unlock`,
    data || {}
  );
  return response.data;
};

// Bulk update strings
export const bulkUpdateStrings = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  data: BulkUpdateStringsRequest
): Promise<BulkUpdateStringsResponse> => {
  const response = await api.put(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/bulk-update`,
    data
  );
  return response.data;
};

// Export strings
export const exportStrings = async (
  workspaceId: number,
  projectId: number,
  platformId: number,
  format: 'csv' | 'json' = 'csv'
): Promise<Blob> => {
  const response = await api.get(
    `/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/export`,
    {
      params: { format },
      responseType: 'blob',
    }
  );
  return response.data;
};

// ============================================================================
// REACT HOOKS
// ============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Hook to list projects
export const useProjects = (workspaceId: number, params?: any) => {
  return useQuery({
    queryKey: ['projects', workspaceId, params],
    queryFn: () => listProjects(workspaceId, params),
  });
};

// Hook to get project detail
export const useProject = (workspaceId: number, projectId: number) => {
  return useQuery({
    queryKey: ['project', workspaceId, projectId],
    queryFn: () => getProject(workspaceId, projectId),
  });
};

// Hook to create project
export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      data,
    }: {
      workspaceId: number;
      data: CreateProjectRequest;
    }) => createProject(workspaceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.workspaceId],
      });
    },
  });
};

// Hook to bulk create strings
export const useBulkCreateStrings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      projectId,
      platformId,
      data,
    }: {
      workspaceId: number;
      projectId: number;
      platformId: number;
      data: BulkCreateStringsRequest;
    }) => bulkCreateStrings(workspaceId, projectId, platformId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['strings', variables.workspaceId, variables.projectId, variables.platformId],
      });
      queryClient.invalidateQueries({
        queryKey: ['project', variables.workspaceId, variables.projectId],
      });
    },
  });
};

// ============================================================================
// USAGE IN COMPONENTS
// ============================================================================

const ProjectListComponent = ({ workspaceId }: { workspaceId: number }) => {
  const { data, isLoading, error } = useProjects(workspaceId, {
    status: 'active',
    page: 1,
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Projects ({data.count})</h1>
      {data.results.map((project) => (
        <div key={project.id}>
          <h2>{project.name}</h2>
          <p>{project.description}</p>
          <span>Status: {project.status}</span>
        </div>
      ))}
    </div>
  );
};

const CreateProjectComponent = ({ workspaceId }: { workspaceId: number }) => {
  const createProject = useCreateProject();

  const handleSubmit = async (formData: CreateProjectRequest) => {
    try {
      const project = await createProject.mutateAsync({
        workspaceId,
        data: formData,
      });
      console.log('Project created:', project);
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      const formData: CreateProjectRequest = {
        name: 'My New Project',
        status: ProjectStatus.PLANNING,
        workspace: workspaceId,
        team_members: [
          { user_id: 1, role: ProjectMemberRole.OWNER }
        ],
      };
      handleSubmit(formData);
    }}>
      <button type="submit" disabled={createProject.isPending}>
        Create Project
      </button>
    </form>
  );
};
```

---

## Best Practices

### 1. UUID Generation

Always generate UUIDs on the frontend before creating strings:

```typescript
import { v4 as uuidv4 } from 'uuid';

// Generate UUID for new string
const stringUuid = uuidv4();
```

### 2. Error Handling

Always handle errors properly:

```typescript
try {
  const project = await createProject(workspaceId, data);
  // Success
} catch (error) {
  if (axios.isAxiosError(error)) {
    const errorData = error.response?.data as ErrorResponse;
    console.error('Error:', errorData.message);
    // Show error to user
  }
}
```

### 3. Optimistic Updates

Use optimistic updates for better UX:

```typescript
const updateString = useMutation({
  mutationFn: updateStringAPI,
  onMutate: async (variables) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['string', variables.stringId] });

    // Snapshot previous value
    const previous = queryClient.getQueryData(['string', variables.stringId]);

    // Optimistically update
    queryClient.setQueryData(['string', variables.stringId], variables.data);

    return { previous };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(['string', variables.stringId], context?.previous);
  },
});
```

### 4. File Downloads

Handle file downloads properly:

```typescript
const handleExport = async (format: 'csv' | 'json') => {
  try {
    const blob = await exportStrings(workspaceId, projectId, platformId, format);

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `project_${projectId}_platform_${platformId}_strings.${format}`;
    link.click();

    // Cleanup
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export failed:', error);
  }
};
```

### 5. Pagination

Handle pagination properly:

```typescript
const [page, setPage] = useState(1);

const { data } = useQuery({
  queryKey: ['strings', workspaceId, projectId, platformId, page],
  queryFn: () => listStrings(workspaceId, projectId, platformId, { page }),
  keepPreviousData: true, // Keep previous data while fetching
});
```

---

## Support

For questions or issues:
- Backend API Spec: `BACKEND_PROJECT_API_SPECIFICATION.md`
- Backend Questions/Answers: `BACKEND_QUESTIONS_ANSWERS.md`
- GitHub Issues: Create an issue with the `api` label

---

**Happy Coding!** 🚀
