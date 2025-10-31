# Backend API Specification: Projects & Project Strings

**Version:** 1.0  
**Last Updated:** 2024-12-XX  
**Status:** Specification for Backend Development

---

## Table of Contents

1. [Overview](#overview)
2. [Data Models](#data-models)
3. [API Endpoints](#api-endpoints)
4. [Business Logic & Constraints](#business-logic--constraints)
5. [Approval Workflow](#approval-workflow)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Testing Requirements](#testing-requirements)

---

## Overview

### Context

This document specifies the backend APIs needed to support the **Projects** feature in the frontend application. Projects are workspace-scoped containers that organize strings by platform, replacing the previous "submission" concept for platform-specific string management.

### Key Design Principles

1. **No Submission Layer**: Strings are directly linked to projects/platforms - no intermediate "submission" entity
2. **Platform-Specific Strings**: Every string belongs to exactly one platform within a project
3. **Parent-Child Relationships**: Strings can have parent-child relationships, but only within the same platform
4. **Approval Workflow**: Approval can be requested at the platform level (not just project level)
5. **Team Collaboration**: Projects support team members with role-based permissions

### Frontend Status

The frontend implementation is **complete** but currently uses mock data. All API calls are stubbed with TODOs. This document provides the complete specification for backend implementation.

---

## Data Models

### 1. Project Model

```python
class Project:
    id: int                          # Primary key
    name: str                        # Required, max 100 chars
    slug: str                        # Auto-generated from name, unique per workspace
    description: Optional[str]       # Optional, max 500 chars
    status: str                      # Enum: "planning", "active", "completed", "archived"
    start_date: Optional[datetime]  # Optional
    end_date: Optional[datetime]     # Optional
    owner_id: int                    # Foreign key to User
    workspace_id: int                # Foreign key to Workspace
    approval_status: str             # Enum: "draft", "pending_approval", "approved", "rejected"
    approved_by: Optional[int]       # Foreign key to User
    approved_at: Optional[datetime]
    rejected_by: Optional[int]        # Foreign key to User
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    created: datetime                # Auto-generated
    last_updated: datetime           # Auto-generated

    # Relationships
    platform_assignments: List[PlatformAssignment]
    team_members: List[ProjectMember]
    strings: List[ProjectString]
    activities: List[ProjectActivity]
```

**Database Constraints:**

- `slug` must be unique per workspace
- `end_date` must be >= `start_date` if both are provided
- `owner_id` must reference a valid User in the workspace
- `workspace_id` must reference a valid Workspace

---

### 2. PlatformAssignment Model

```python
class PlatformAssignment:
    id: int                          # Primary key
    project_id: int                  # Foreign key to Project
    platform_id: int                 # Foreign key to Platform
    approval_status: str              # Enum: "draft", "pending_approval", "approved", "rejected"
    approved_by: Optional[int]        # Foreign key to User
    approved_at: Optional[datetime]
    rejected_by: Optional[int]        # Foreign key to User
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    assigned_members: List[int]       # List of User IDs (many-to-many via junction table)
    created: datetime
    last_updated: datetime

    # Relationships
    project: Project
    platform: Platform
    strings: List[ProjectString]     # All strings for this platform in this project
    approval_history: List[ApprovalHistory]
```

**Database Constraints:**

- `project_id` + `platform_id` must be unique (one platform assignment per project/platform)
- `assigned_members` must reference valid Users in the workspace

---

### 3. ProjectMember Model

```python
class ProjectMember:
    id: int                          # Primary key
    project_id: int                  # Foreign key to Project
    user_id: int                     # Foreign key to User
    role: str                        # Enum: "owner", "editor", "viewer"
    created: datetime

    # Relationships
    project: Project
    user: User
```

**Database Constraints:**

- `project_id` + `user_id` must be unique (one role per user per project)
- At least one member must have role "owner"
- `user_id` must reference a valid User in the workspace

---

### 4. ProjectString Model

```python
class ProjectString:
    id: int                          # Primary key
    project_id: int                  # Foreign key to Project
    platform_id: int                 # Foreign key to Platform (via PlatformAssignment)
    field_id: int                    # Foreign key to Field
    rule_id: int                     # Foreign key to Rule
    value: str                       # Generated string value
    string_uuid: str                 # UUID4, unique identifier for this string
    parent_uuid: Optional[str]       # UUID4 of parent string (null for level 1)
    created_by: Optional[int]         # Foreign key to User
    created: datetime
    last_updated: datetime

    # Relationships
    project: Project
    platform: Platform
    field: Field
    rule: Rule
    details: List[StringDetail]       # Dimension values for this string
    parent: Optional[ProjectString]  # Self-referential (via parent_uuid)
    children: List[ProjectString]    # Inverse relationship
```

**Database Constraints:**

- `string_uuid` must be unique globally
- `parent_uuid` must reference a valid ProjectString in the **same platform**
- `platform_id` must match the project's platform assignment
- `field_id` must belong to the rule's platform
- `parent_uuid` cannot reference itself (no circular references)

---

### 5. StringDetail Model

```python
class StringDetail:
    id: int                          # Primary key
    string_id: int                   # Foreign key to ProjectString
    dimension_id: int                 # Foreign key to Dimension
    dimension_value_id: Optional[int] # Foreign key to DimensionValue (for list dimensions)
    dimension_value_freetext: Optional[str]  # For text dimensions
    is_inherited: bool               # Whether this value was inherited from parent
    created: datetime

    # Relationships
    string: ProjectString
    dimension: Dimension
    dimension_value: Optional[DimensionValue]
```

**Database Constraints:**

- `string_id` + `dimension_id` must be unique (one detail per dimension per string)
- For list dimensions: `dimension_value_id` must be set, `dimension_value_freetext` must be null
- For text dimensions: `dimension_value_freetext` must be set, `dimension_value_id` must be null
- `dimension_value_id` must belong to the specified `dimension_id`

---

### 6. ApprovalHistory Model

```python
class ApprovalHistory:
    id: int                          # Primary key
    project_id: Optional[int]        # Foreign key to Project (for project-level approval)
    platform_assignment_id: Optional[int]  # Foreign key to PlatformAssignment (for platform-level approval)
    user_id: int                     # Foreign key to User (who performed the action)
    action: str                      # Enum: "submitted", "approved", "rejected"
    comment: Optional[str]            # Optional comment/reason
    timestamp: datetime              # Auto-generated

    # Relationships
    project: Optional[Project]
    platform_assignment: Optional[PlatformAssignment]
    user: User
```

**Database Constraints:**

- Either `project_id` OR `platform_assignment_id` must be set (not both, not neither)

---

### 7. ProjectActivity Model

```python
class ProjectActivity:
    id: int                          # Primary key
    project_id: int                  # Foreign key to Project
    type: str                        # Enum: see ProjectActivityType below
    description: str                 # Human-readable description
    user_id: Optional[int]           # Foreign key to User (who performed the action)
    metadata: Optional[dict]         # JSON field for additional context
    created: datetime                # Auto-generated

    # Relationships
    project: Project
    user: Optional[User]
```

**ProjectActivityType Enum:**

- `project_created`
- `platform_added`
- `platform_removed`
- `member_assigned`
- `member_unassigned`
- `strings_generated`
- `status_changed`
- `project_updated`
- `submitted_for_approval`
- `approved`
- `rejected`

---

## API Endpoints

### Base URL Pattern

All endpoints follow the pattern:

```
/workspaces/{workspaceId}/projects/{projectId}/...
```

All endpoints require:

- Authentication (JWT token)
- Workspace membership validation
- Project access permission check

---

### Project Management Endpoints

#### 1. List Projects

**Endpoint:** `GET /workspaces/{workspaceId}/projects/`

**Query Parameters:**

- `status` (optional): Filter by status (`planning`, `active`, `completed`, `archived`)
- `search` (optional): Search by name or description
- `page` (optional): Page number for pagination
- `page_size` (optional): Items per page (default: 20)

**Response:** `200 OK`

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

**Permissions:**

- User must be a member of the workspace
- User must be a member of the project (or workspace admin)

---

#### 2. Get Project Detail

**Endpoint:** `GET /workspaces/{workspaceId}/projects/{projectId}/`

**Response:** `200 OK`

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
  "platform_assignments": [
    {
      "platform_id": 1,
      "platform_name": "Google Ads",
      "platform_slug": "google-ads",
      "assigned_members": [1],
      "string_count": 4,
      "last_updated": "2024-10-25T14:30:00Z",
      "approval_status": "draft",
      "approval_history": []
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

**Permissions:**

- User must be a member of the project (or workspace admin)

---

#### 3. Create Project

**Endpoint:** `POST /workspaces/{workspaceId}/projects/`

**Request Body:**

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

**Response:** `201 Created`

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
  "created": "2024-12-XXT10:00:00Z",
  "last_updated": "2024-12-XXT10:00:00Z",
  "approval_status": "draft"
}
```

**Validation Rules:**

- `name` is required, 3-100 characters
- `description` is optional, max 500 characters
- `status` must be one of: `planning`, `active`, `completed`, `archived`
- `end_date` must be >= `start_date` if both provided
- `platform_assignments` must reference valid platforms in the workspace
- `team_members` must include at least one member with role `owner`
- `team_members` must reference valid users in the workspace
- `assigned_members` in platform assignments must reference valid users in the workspace

**Permissions:**

- User must be a member of the workspace
- User must have permission to create projects (workspace admin or owner)

**Side Effects:**

- Creates `ProjectActivity` record with type `project_created`
- Creates `ProjectMember` records for all team members
- Creates `PlatformAssignment` records for all platform assignments
- Creates `ProjectActivity` records for each platform added (`platform_added`)
- Creates `ProjectActivity` records for each team member assigned (`member_assigned`)

---

#### 4. Update Project

**Endpoint:** `PUT /workspaces/{workspaceId}/projects/{projectId}/`

**Request Body:** (all fields optional)

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

**Response:** `200 OK` (same structure as Get Project Detail)

**Validation Rules:**

- Same as Create Project
- Cannot change `workspace` or `owner_id` (separate endpoints if needed)
- Cannot update if `approval_status` is `approved` (may require unlock)

**Permissions:**

- User must have `owner` or `editor` role in the project

**Side Effects:**

- Creates `ProjectActivity` record with type `project_updated`
- Creates `ProjectActivity` records for added/removed platforms
- Creates `ProjectActivity` records for added/removed team members
- Creates `ProjectActivity` record if status changed (`status_changed`)

---

#### 5. Delete Project

**Endpoint:** `DELETE /workspaces/{workspaceId}/projects/{projectId}/`

**Response:** `204 No Content`

**Permissions:**

- User must have `owner` role in the project (or workspace admin)

**Side Effects:**

- Deletes all related `ProjectString` records (cascade)
- Deletes all related `ProjectMember` records (cascade)
- Deletes all related `PlatformAssignment` records (cascade)
- Deletes all related `ProjectActivity` records (cascade)
- Deletes all related `ApprovalHistory` records (cascade)

---

### Project Approval Endpoints

#### 6. Submit Project for Approval

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/submit-for-approval/`

**Request Body:** (optional)

```json
{
  "comment": "Ready for review"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "approval_status": "pending_approval",
  "submitted_at": "2024-12-XXT10:00:00Z",
  "submitted_by": 1
}
```

**Business Logic:**

- Sets `approval_status` to `pending_approval`
- Creates `ApprovalHistory` record with action `submitted`
- Creates `ProjectActivity` record with type `submitted_for_approval`

**Permissions:**

- User must have `owner` or `editor` role in the project
- Project must be in `draft` or `rejected` status

---

#### 7. Approve Project

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/approve/`

**Request Body:** (optional)

```json
{
  "comment": "Looks good!"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "approval_status": "approved",
  "approved_at": "2024-12-XXT10:00:00Z",
  "approved_by": 2
}
```

**Business Logic:**

- Sets `approval_status` to `approved`
- Sets `approved_by` and `approved_at`
- Creates `ApprovalHistory` record with action `approved`
- Creates `ProjectActivity` record with type `approved`

**Permissions:**

- User must have approval permissions (workspace admin or designated approver)
- Project must be in `pending_approval` status

---

#### 8. Reject Project

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/reject/`

**Request Body:**

```json
{
  "reason": "Needs more details"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "approval_status": "rejected",
  "rejected_at": "2024-12-XXT10:00:00Z",
  "rejected_by": 2,
  "rejection_reason": "Needs more details"
}
```

**Business Logic:**

- Sets `approval_status` to `rejected`
- Sets `rejected_by`, `rejected_at`, and `rejection_reason`
- Creates `ApprovalHistory` record with action `rejected`
- Creates `ProjectActivity` record with type `rejected`

**Permissions:**

- User must have approval permissions (workspace admin or designated approver)
- Project must be in `pending_approval` status

---

### Platform Assignment Approval Endpoints

#### 9. Submit Platform for Approval

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/submit-for-approval/`

**Request Body:** (optional)

```json
{
  "comment": "Ready for review"
}
```

**Response:** `200 OK`

```json
{
  "platform_assignment_id": 1,
  "approval_status": "pending_approval",
  "submitted_at": "2024-12-XXT10:00:00Z",
  "submitted_by": 1
}
```

**Business Logic:**

- Sets platform assignment's `approval_status` to `pending_approval`
- Creates `ApprovalHistory` record with action `submitted` (linked to platform_assignment_id)

**Permissions:**

- User must be assigned to the platform or have `owner`/`editor` role in project
- Platform must be in `draft` or `rejected` status

---

#### 10. Approve Platform

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/approve/`

**Request Body:** (optional)

```json
{
  "comment": "Approved"
}
```

**Response:** `200 OK`

```json
{
  "platform_assignment_id": 1,
  "approval_status": "approved",
  "approved_at": "2024-12-XXT10:00:00Z",
  "approved_by": 2
}
```

**Permissions:**

- User must have approval permissions (workspace admin or designated approver)
- Platform must be in `pending_approval` status

---

#### 11. Reject Platform

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/reject/`

**Request Body:**

```json
{
  "reason": "Strings need review"
}
```

**Response:** `200 OK`

```json
{
  "platform_assignment_id": 1,
  "approval_status": "rejected",
  "rejected_at": "2024-12-XXT10:00:00Z",
  "rejected_by": 2,
  "rejection_reason": "Strings need review"
}
```

**Permissions:**

- User must have approval permissions (workspace admin or designated approver)
- Platform must be in `pending_approval` status

---

### Project String Endpoints

#### 12. Bulk Create Strings

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk`

**Request Body:**

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

**Response:** `201 Created`

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
      "created": "2024-12-XXT10:00:00Z",
      "last_updated": "2024-12-XXT10:00:00Z"
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
      "created": "2024-12-XXT10:00:00Z",
      "last_updated": "2024-12-XXT10:00:00Z"
    }
  ]
}
```

**Validation Rules:**

- `rule` must reference a valid Rule
- `starting_field` must belong to the rule's platform
- `platform_id` must match a PlatformAssignment for this project
- All `field` values must belong to the specified rule
- `parent_uuid` must reference a string in the **same platform** (or be null for level 1)
- `parent_uuid` cannot reference itself (no circular references)
- For list dimensions: `dimension_value` must be set, `dimension_value_freetext` must be null
- For text dimensions: `dimension_value_freetext` must be set, `dimension_value` must be null
- `dimension_value` must belong to the specified `dimension`
- `string_uuid` must be unique globally
- Platform's `approval_status` does NOT block creation (users can add more strings incrementally)

**Business Logic:**

- Creates all strings atomically (all or nothing)
- Creates `StringDetail` records for each string's details
- Sets `is_inherited` flag on details based on parent string (if applicable)
- Updates platform assignment's `string_count` and `last_updated`
- Creates `ProjectActivity` record with type `strings_generated`

**Permissions:**

- User must be assigned to the platform OR have `owner`/`editor` role in project
- Platform approval status does NOT block creation

**Error Responses:**

- `400 Bad Request`: Validation errors
- `404 Not Found`: Project, platform, or rule not found
- `403 Forbidden`: User doesn't have permission

---

#### 13. List Strings for Platform

**Endpoint:** `GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings`

**Query Parameters:**

- `field` (optional): Filter by field ID
- `parent_field` (optional): Filter by parent field ID (returns parent strings for a given field level)
- `parent_uuid` (optional): Filter by parent UUID (returns children of a specific parent)
- `search` (optional): Search by string value
- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 50)

**Response:** `200 OK`

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

**Special Case: `parent_field` parameter**
When `parent_field` is provided, return only strings that:

- Belong to the specified `parent_field` (field level)
- Are in the same platform
- Can be used as parents for the current field level

**Permissions:**

- User must be a member of the project (or workspace admin)

---

#### 14. Get String Expanded Details

**Endpoint:** `GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/expanded`

**Response:** `200 OK`

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
      "dimension_value_utm": "sale",
      "effective_value": "Sale",
      "value": "Sale",
      "label": "Sale Campaign",
      "is_inherited": false,
      "created_by": 1,
      "created_by_name": "Alice Johnson",
      "created": "2024-10-25T14:30:00Z",
      "last_updated": "2024-10-25T14:30:00Z"
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

**Use Case:** This endpoint is used for parent string inheritance. When a user selects a parent string in the grid builder, the frontend fetches expanded details to populate inherited dimension values.

**Permissions:**

- User must be a member of the project (or workspace admin)

---

#### 15. Update String

**Endpoint:** `PUT /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}`

**Request Body:**

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

**Response:** `200 OK` (same structure as Get String Expanded Details)

**Validation Rules:**

- Same as Bulk Create Strings (for details)
- Platform's `approval_status` does NOT block updates (for now - may require unlock in future)

**Business Logic:**

- Updates string value and details
- Updates `last_updated` timestamp
- If details changed, updates `is_inherited` flags
- Updates platform assignment's `last_updated`

**Permissions:**

- User must be assigned to the platform OR have `owner`/`editor` role in project
- Platform approval status does NOT block updates (for now)

**Future Enhancement:**

- If platform is `approved`, may require "unlock" step before allowing updates
- After unlock, platform status changes to `draft` and requires re-approval

---

#### 16. Delete String

**Endpoint:** `DELETE /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}`

**Response:** `204 No Content`

**Business Logic:**

- Checks if string has children (if `parent_uuid` matches this string's `string_uuid`)
- If has children, returns error (must delete children first, or implement cascade delete)
- Updates platform assignment's `string_count` and `last_updated`

**Permissions:**

- User must be assigned to the platform OR have `owner`/`editor` role in project
- Platform approval status does NOT block deletion (for now)

**Error Responses:**

- `400 Bad Request`: String has children (cannot delete parent without deleting children)
- `404 Not Found`: String not found
- `403 Forbidden`: User doesn't have permission

**Future Enhancement:**

- If platform is `approved`, may require "unlock" step before allowing deletion

---

#### 17. Unlock String (Future)

**Endpoint:** `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/unlock`

**Request Body:** (optional)

```json
{
  "reason": "Need to update campaign name"
}
```

**Response:** `200 OK`

```json
{
  "string_id": 1,
  "unlocked_at": "2024-12-XXT10:00:00Z",
  "unlocked_by": 1,
  "platform_status_changed": true,
  "new_platform_status": "draft"
}
```

**Business Logic:**

- Allows editing/deleting approved strings
- If platform is `approved`, changes platform status to `draft`
- Creates audit trail record
- Requires re-approval after changes

**Permissions:**

- User must be assigned to the platform OR have `owner`/`editor` role in project
- Platform must be in `approved` status

**Note:** This is a future enhancement and can be implemented later.

---

## Business Logic & Constraints

### 1. Platform-Specific Strings

**Constraint:** Every string must belong to exactly one platform within a project.

**Validation:**

- When creating/updating strings, `platform_id` must match a `PlatformAssignment` for the project
- Parent-child relationships can only exist within the same platform
- When filtering by `parent_uuid`, ensure the parent string is in the same platform

### 2. Parent-Child Relationships

**Constraint:** Parent strings must be in the same platform as child strings.

**Validation:**

- `parent_uuid` must reference a `ProjectString` where:
  - `project_id` matches
  - `platform_id` matches
  - `field_level` is less than the current string's field level
- Prevent circular references (string cannot be its own parent, or grandparent)
- When deleting a parent string, handle children:
  - Option A: Prevent deletion if children exist (return error)
  - Option B: Cascade delete children (with confirmation)
  - Option C: Set children's `parent_uuid` to null (orphan them)

**Recommended:** Option A (prevent deletion) for data integrity.

### 3. String UUID Uniqueness

**Constraint:** `string_uuid` must be globally unique (not just per project/platform).

**Validation:**

- Check uniqueness before creating
- Use UUID4 format
- Frontend generates UUIDs before sending to backend

### 4. Dimension Value Validation

**Constraint:** Dimension values must match their dimension type.

**Validation:**

- For list dimensions: `dimension_value_id` must be set, `dimension_value_freetext` must be null
- For text dimensions: `dimension_value_freetext` must be set, `dimension_value_id` must be null
- `dimension_value_id` must belong to the specified `dimension_id`

### 5. Field Validation

**Constraint:** Strings must use fields that belong to the rule's platform.

**Validation:**

- All `field` values in a bulk create must belong to the rule's platform
- `starting_field` must belong to the rule's platform

### 6. Team Member Roles

**Constraint:** At least one team member must have role `owner`.

**Validation:**

- On create/update, ensure at least one `team_member` has role `owner`
- Prevent removing the last owner (must transfer ownership first)

### 7. Approval Status

**Constraint:** Approval status follows a specific workflow.

**Workflow:**

- `draft` → `pending_approval` (via submit)
- `pending_approval` → `approved` (via approve)
- `pending_approval` → `rejected` (via reject)
- `rejected` → `draft` (can resubmit)
- `approved` → `draft` (via unlock, if implemented)

**Current Behavior:**

- Platform approval status does **NOT** block string creation/updates/deletes
- This allows incremental string addition even after approval

### 8. Activity Tracking

**Constraint:** All significant actions must create activity records.

**Required Activities:**

- Project created
- Platform added/removed
- Team member assigned/unassigned
- Strings generated (bulk)
- Status changed
- Project updated
- Submitted for approval
- Approved
- Rejected

---

## Approval Workflow

### Project-Level Approval

1. **Draft** → User creates/updates project
2. **Submit** → User submits project for approval (`pending_approval`)
3. **Approve/Reject** → Approver reviews and approves/rejects
4. **If Rejected** → Returns to `draft`, user can fix and resubmit

### Platform-Level Approval

1. **Draft** → User creates/updates strings for platform
2. **Submit** → User submits platform for approval (`pending_approval`)
3. **Approve/Reject** → Approver reviews and approves/rejects
4. **If Rejected** → Returns to `draft`, user can fix and resubmit

### Approval Permissions

- Approvers: Workspace admins or designated approvers (TBD)
- Submitters: Project owners or editors

### Current Behavior

- **Approval does NOT block operations**: Users can still create/update/delete strings even if platform is approved
- This allows incremental string addition
- Future enhancement: May require unlock for approved platforms

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Validation Error",
  "message": "Field 'name' is required",
  "details": {
    "field": "name",
    "code": "required"
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful GET/PUT/PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation errors, invalid data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User doesn't have permission
- `404 Not Found`: Resource not found
- `409 Conflict`: Conflict (e.g., duplicate slug, circular reference)
- `500 Internal Server Error`: Server error

### Common Error Scenarios

#### 1. Validation Errors (`400 Bad Request`)

```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": [
    {
      "field": "name",
      "code": "required",
      "message": "Name is required"
    },
    {
      "field": "end_date",
      "code": "invalid",
      "message": "End date must be after start date"
    }
  ]
}
```

#### 2. Permission Errors (`403 Forbidden`)

```json
{
  "error": "Permission Denied",
  "message": "You do not have permission to perform this action",
  "required_role": "owner"
}
```

#### 3. Not Found Errors (`404 Not Found`)

```json
{
  "error": "Not Found",
  "message": "Project with id 123 not found"
}
```

#### 4. Conflict Errors (`409 Conflict`)

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

## Performance Considerations

### 1. Pagination

- All list endpoints should support pagination
- Default page size: 20-50 items
- Use cursor-based pagination if possible (better for large datasets)

### 2. Eager Loading

- Project detail endpoint should eager load related data:
  - Platform assignments
  - Team members
  - Strings (with details)
  - Activities
- Use select_related/prefetch_related to avoid N+1 queries

### 3. Bulk Operations

- `bulk create strings` endpoint should use bulk insert
- Consider transaction wrapping for atomicity

### 4. Caching

- Consider caching project detail (with short TTL)
- Cache platform assignments (they change infrequently)
- Invalidate cache on updates

### 5. Database Indexes

**Recommended indexes:**

- `Project`: `workspace_id`, `slug`, `owner_id`, `status`
- `ProjectMember`: `project_id`, `user_id`
- `PlatformAssignment`: `project_id`, `platform_id`, `approval_status`
- `ProjectString`: `project_id`, `platform_id`, `field_id`, `string_uuid`, `parent_uuid`, `rule_id`
- `StringDetail`: `string_id`, `dimension_id`
- `ProjectActivity`: `project_id`, `created` (for timeline queries)

---

## Testing Requirements

### Unit Tests

1. **Model Validation**
   - Test all field validations
   - Test relationship constraints
   - Test enum values

2. **Business Logic**
   - Test parent-child relationship validation
   - Test approval workflow state transitions
   - Test team member role constraints

### Integration Tests

1. **API Endpoints**
   - Test all CRUD operations
   - Test query parameters
   - Test pagination
   - Test filtering

2. **Permission Checks**
   - Test role-based access control
   - Test workspace isolation
   - Test project membership requirements

3. **Bulk Operations**
   - Test atomicity (all or nothing)
   - Test large batch sizes
   - Test error handling in partial failures

### Edge Cases

1. **Parent-Child Relationships**
   - Circular reference prevention
   - Cross-platform parent prevention
   - Orphan handling

2. **Approval Workflow**
   - Invalid state transitions
   - Concurrent approval requests
   - Approval history tracking

3. **String Operations**
   - Duplicate UUID handling
   - Invalid dimension value handling
   - Missing parent string handling

---

## Additional Notes

### Migration from Submissions

- Projects are a new concept, no migration needed initially
- Future: May need to migrate existing submissions to projects (out of scope for now)

### API Versioning

- Consider API versioning if needed: `/api/v1/workspaces/...`
- Current frontend expects endpoints without version prefix

### Rate Limiting

- Consider rate limiting for bulk operations
- Consider rate limiting for approval endpoints

### Audit Trail

- All approval actions should be logged in `ApprovalHistory`
- All significant actions should be logged in `ProjectActivity`

---

## Frontend Integration Notes

### Current Mock Data

The frontend currently uses mock data structures that match the above specifications. When implementing backend APIs, ensure response formats match exactly to avoid frontend changes.

### Key Frontend Expectations

1. **Response Format**: Snake_case for all fields (will be converted to camelCase in frontend)
2. **Pagination**: Standard paginated response format with `count`, `next`, `previous`, `results`
3. **Error Format**: Consistent error response format as specified above
4. **UUIDs**: Frontend generates UUIDs before sending to backend (validate uniqueness)
5. **Timestamps**: ISO 8601 format (e.g., `2024-10-25T14:30:00Z`)

### Frontend Files Waiting for Backend

- `src/hooks/project-grid-builder/useProjectStringSubmission.ts` (lines 220, 237, 291)
- `src/hooks/project-grid-builder/useProjectStringsByField.ts` (lines 13, 21)
- `src/hooks/project-grid-builder/useProjectParentStringSync.ts` (lines 56, 61, 109)
- `src/components/projects/ProjectPlatformStringsTable.tsx` (delete functionality)

---

## Questions or Clarifications Needed

1. **Unlock Functionality**: Should we implement unlock for approved platforms now, or defer to Phase 2?
2. **Cascade Delete**: When deleting a parent string, should we cascade delete children or prevent deletion?
3. **Approval Permissions**: Who can approve? Workspace admins only, or configurable per workspace?
4. **String History**: Do we need version history for strings, or can we skip for now?
5. **Bulk Updates**: Do we need a bulk update endpoint, or is single-string update sufficient?
6. **Export**: Do we need export endpoints for project strings, or is frontend export sufficient?

---

## Implementation Priority

### Phase 1 (Critical - Blocking Frontend)

1. ✅ Project CRUD endpoints (already exists per frontend)
2. ⚠️ **Bulk Create Strings** endpoint
3. ⚠️ **List Strings** endpoint (with filters)
4. ⚠️ **Get String Expanded** endpoint (for parent inheritance)
5. ⚠️ **Update String** endpoint
6. ⚠️ **Delete String** endpoint

### Phase 2 (Important - Core Features)

7. Platform assignment approval endpoints
8. Project approval endpoints
9. Activity tracking
10. Approval history

### Phase 3 (Nice to Have - Future Enhancements)

11. Unlock functionality
12. String history/versioning
13. Bulk update endpoints
14. Export endpoints

---

## Contact

For questions or clarifications, please reach out to the frontend team or refer to the frontend codebase for implementation details.

**Frontend Repository:** `/Users/volkanyazici/Dev/tux-frontend-tanstack`

**Key Files:**

- `src/types/project.ts` - TypeScript type definitions
- `src/components/projects/` - Project UI components
- `src/hooks/project-grid-builder/` - Grid builder hooks (waiting for APIs)
