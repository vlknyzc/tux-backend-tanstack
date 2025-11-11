# Projects API

Projects are containers for organizing strings within a workspace. Each project has team members, platforms, and approval workflows.

**Base Path**: `/api/v1/workspaces/{workspace_id}/projects/`

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/projects/` | List all projects in workspace |
| POST | `/projects/` | Create new project |
| GET | `/projects/{id}/` | Get project details |
| PATCH | `/projects/{id}/` | Update project |
| DELETE | `/projects/{id}/` | Delete project |
| POST | `/projects/{id}/submit/` | Submit for approval |
| POST | `/projects/{id}/approve/` | Approve project |
| POST | `/projects/{id}/reject/` | Reject project |

---

## Data Models

### Project Object

```json
{
  "id": 10,
  "name": "Q4 2024 Campaign",
  "slug": "q4-2024-campaign",
  "description": "Marketing campaign for Q4 2024",
  "status": "active",
  "approval_status": "draft",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "owner_id": 5,
  "owner_name": "John Doe",
  "workspace": 1,
  "platforms": [
    {
      "id": 1,
      "name": "Meta Ads",
      "slug": "meta-ads",
      "platform_type": "meta"
    }
  ],
  "team_members": [
    {
      "id": 101,
      "user": {
        "id": 5,
        "name": "John Doe",
        "email": "john@example.com",
        "avatar": null
      },
      "role": "owner",
      "created": "2024-11-01T10:00:00Z"
    }
  ],
  "stats": {
    "total_strings": 45,
    "platforms_count": 2,
    "team_members_count": 3,
    "last_activity": "2024-11-10T15:30:00Z"
  },
  "created": "2024-11-01T10:00:00Z",
  "last_updated": "2024-11-10T15:30:00Z"
}
```

### Project Status

- `active` - Project is active
- `archived` - Project is archived
- `on_hold` - Project is on hold

### Approval Status

- `draft` - Initial state, editing allowed
- `submitted` - Submitted for approval, locked
- `approved` - Approved, locked
- `rejected` - Rejected, editing allowed

### Team Roles

- `owner` - Full control over project
- `editor` - Can edit strings and settings
- `viewer` - Read-only access

---

## List Projects

**GET** `/api/v1/workspaces/{workspace_id}/projects/`

Get all projects in a workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `active`, `archived`, `on_hold` |
| `approval_status` | string | Filter by approval: `draft`, `submitted`, `approved`, `rejected` |
| `owner_id` | integer | Filter by owner user ID |
| `platform_id` | integer | Filter projects using this platform |
| `search` | string | Search by name or description |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Results per page (default: 20, max: 100) |

### Example Request

```bash
GET /api/v1/workspaces/1/projects/?status=active&page=1&page_size=20
Authorization: Bearer <token>
```

### Example Response

```json
{
  "count": 45,
  "next": "http://api.tuxonomy.com/api/v1/workspaces/1/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 10,
      "name": "Q4 2024 Campaign",
      "slug": "q4-2024-campaign",
      "description": "Marketing campaign for Q4 2024",
      "status": "active",
      "approval_status": "draft",
      "start_date": "2024-10-01",
      "end_date": "2024-12-31",
      "owner_id": 5,
      "owner_name": "John Doe",
      "workspace": 1,
      "platforms": [...],
      "team_members": [...],
      "stats": {...},
      "created": "2024-11-01T10:00:00Z",
      "last_updated": "2024-11-10T15:30:00Z"
    }
  ]
}
```

---

## Create Project

**POST** `/api/v1/workspaces/{workspace_id}/projects/`

Create a new project.

### Request Body

```json
{
  "name": "Q4 2024 Campaign",
  "description": "Marketing campaign for Q4 2024",
  "status": "active",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "platforms": [1, 2],
  "team_members": [
    {
      "user_id": 5,
      "role": "owner"
    },
    {
      "user_id": 8,
      "role": "editor"
    }
  ]
}
```

### Validation Rules

- `name`: Required, max 200 characters, unique per workspace
- `description`: Optional, max 1000 characters
- `status`: Optional, default: `active`
- `start_date`: Optional, ISO date format
- `end_date`: Optional, must be >= start_date
- `platforms`: Optional, array of platform IDs
- `team_members`: Optional, must include at least one `owner` role

### Example Response (201 Created)

```json
{
  "id": 15,
  "name": "Q4 2024 Campaign",
  "slug": "q4-2024-campaign",
  "description": "Marketing campaign for Q4 2024",
  "status": "active",
  "approval_status": "draft",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "owner_id": 5,
  "owner_name": "John Doe",
  "workspace": 1,
  "platforms": [...],
  "team_members": [...],
  "stats": {
    "total_strings": 0,
    "platforms_count": 2,
    "team_members_count": 2,
    "last_activity": null
  },
  "created": "2024-11-11T10:00:00Z",
  "last_updated": "2024-11-11T10:00:00Z"
}
```

### Error Response (400 Bad Request)

```json
{
  "name": ["Project with this name already exists in workspace"],
  "end_date": ["End date must be after start date"],
  "team_members": ["At least one team member must have role 'owner'"]
}
```

---

## Get Project Details

**GET** `/api/v1/workspaces/{workspace_id}/projects/{id}/`

Get detailed information about a specific project.

### Example Response (200 OK)

```json
{
  "id": 10,
  "name": "Q4 2024 Campaign",
  "slug": "q4-2024-campaign",
  "description": "Marketing campaign for Q4 2024",
  "status": "active",
  "approval_status": "draft",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "owner_id": 5,
  "owner_name": "John Doe",
  "workspace": 1,
  "platforms": [...],
  "team_members": [...],
  "stats": {...},
  "strings": [
    {
      "id": 501,
      "value": "ACME-2024-US-Q4-Awareness",
      "string_uuid": "abc123...",
      "platform": {...},
      "entity": {...},
      "created": "2024-11-05T12:00:00Z"
    }
  ],
  "activities": [
    {
      "id": 301,
      "type": "project_created",
      "description": "created the project",
      "user_id": 5,
      "user_name": "John Doe",
      "user_avatar": null,
      "metadata": {},
      "created": "2024-11-01T10:00:00Z"
    }
  ],
  "approval_history": [],
  "created": "2024-11-01T10:00:00Z",
  "last_updated": "2024-11-10T15:30:00Z"
}
```

---

## Update Project

**PATCH** `/api/v1/workspaces/{workspace_id}/projects/{id}/`

Update project fields. Can only update if approval_status is not `approved`.

### Request Body (Partial Update)

```json
{
  "description": "Updated description for Q4 campaign",
  "status": "on_hold",
  "end_date": "2025-01-15"
}
```

### Example Response (200 OK)

Returns updated project object (same structure as GET).

### Error Response (400 Bad Request)

```json
{
  "error": "Cannot update approved project without unlock"
}
```

---

## Delete Project

**DELETE** `/api/v1/workspaces/{workspace_id}/projects/{id}/`

Delete a project. **This also deletes all associated strings**.

### Example Response (204 No Content)

No response body.

### Error Response (403 Forbidden)

```json
{
  "error": "Cannot delete approved project"
}
```

---

## Submit for Approval

**POST** `/api/v1/workspaces/{workspace_id}/projects/{id}/submit/`

Submit project for approval. Changes status from `draft` to `submitted`.

### Request Body

```json
{
  "comment": "Ready for review - all strings validated"
}
```

### Example Response (200 OK)

```json
{
  "id": 10,
  "approval_status": "submitted",
  "approval_history": [
    {
      "id": 201,
      "action": "submitted",
      "comment": "Ready for review - all strings validated",
      "timestamp": "2024-11-11T14:00:00Z",
      "user_id": 5,
      "user_name": "John Doe"
    }
  ]
}
```

---

## Approve Project

**POST** `/api/v1/workspaces/{workspace_id}/projects/{id}/approve/`

Approve a submitted project. Changes status to `approved` and locks the project.

### Request Body

```json
{
  "comment": "Approved for deployment"
}
```

### Example Response (200 OK)

```json
{
  "id": 10,
  "approval_status": "approved",
  "approval_history": [
    {
      "id": 202,
      "action": "approved",
      "comment": "Approved for deployment",
      "timestamp": "2024-11-11T15:00:00Z",
      "user_id": 3,
      "user_name": "Jane Manager"
    }
  ]
}
```

---

## Reject Project

**POST** `/api/v1/workspaces/{workspace_id}/projects/{id}/reject/`

Reject a submitted project. Changes status back to `draft` for editing.

### Request Body

```json
{
  "reason": "String naming convention issues found"
}
```

### Example Response (200 OK)

```json
{
  "id": 10,
  "approval_status": "rejected",
  "approval_history": [
    {
      "id": 203,
      "action": "rejected",
      "comment": "String naming convention issues found",
      "timestamp": "2024-11-11T15:30:00Z",
      "user_id": 3,
      "user_name": "Jane Manager"
    }
  ]
}
```

---

## Frontend Integration Examples

### List Projects

```javascript
async function fetchProjects(workspaceId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
}

// Usage
const projects = await fetchProjects(1, { status: 'active', page_size: 50 });
```

### Create Project

```javascript
async function createProject(workspaceId, projectData) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(projectData)
    }
  );

  if (!response.ok) {
    const errors = await response.json();
    throw new Error(JSON.stringify(errors));
  }

  return await response.json();
}

// Usage
const newProject = await createProject(1, {
  name: 'Q4 2024 Campaign',
  description: 'Marketing campaign',
  platforms: [1, 2],
  team_members: [{ user_id: 5, role: 'owner' }]
});
```

### Submit for Approval

```javascript
async function submitProject(workspaceId, projectId, comment) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/submit/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ comment })
    }
  );

  return await response.json();
}

// Usage
await submitProject(1, 10, 'Ready for review');
```

---

## Common Use Cases

### 1. Project Dashboard

```javascript
// Fetch projects with stats for dashboard
const activeProjects = await fetchProjects(workspaceId, {
  status: 'active',
  page_size: 100
});

const projectCards = activeProjects.results.map(project => ({
  id: project.id,
  name: project.name,
  stringCount: project.stats.total_strings,
  platforms: project.platforms.map(p => p.name),
  lastActivity: project.stats.last_activity,
  approvalStatus: project.approval_status
}));
```

### 2. Project Creation Workflow

```javascript
// Step 1: Create project
const project = await createProject(workspaceId, {
  name: formData.name,
  description: formData.description,
  platforms: selectedPlatformIds,
  team_members: [
    { user_id: currentUser.id, role: 'owner' },
    ...invitedMembers.map(m => ({ user_id: m.id, role: m.role }))
  ]
});

// Step 2: Navigate to project
router.push(`/projects/${project.id}`);
```

### 3. Approval Workflow

```javascript
// Admin reviewing submitted projects
const pendingProjects = await fetchProjects(workspaceId, {
  approval_status: 'submitted'
});

// Approve or reject
if (approved) {
  await approveProject(workspaceId, projectId, 'Looks good!');
} else {
  await rejectProject(workspaceId, projectId, 'Needs revisions');
}
```
