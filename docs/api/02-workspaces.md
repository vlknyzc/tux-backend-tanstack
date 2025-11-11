# Workspaces API

Workspaces provide multi-tenant isolation in Tuxonomy. Each workspace has its own data, users, and configurations.

**Base Path**: `/api/v1/workspaces/`

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workspaces/` | List all workspaces user has access to |
| POST | `/workspaces/` | Create new workspace |
| GET | `/workspaces/{id}/` | Get workspace details |
| PATCH | `/workspaces/{id}/` | Update workspace |
| DELETE | `/workspaces/{id}/` | Delete workspace |

---

## Data Models

### Workspace Object

```json
{
  "id": 1,
  "name": "ACME Corporation",
  "slug": "acme-corporation",
  "status": "active",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-11-10T14:30:00Z",
  "created_by": {
    "id": 1,
    "email": "admin@acme.com",
    "name": "John Admin"
  },
  "stats": {
    "total_projects": 25,
    "total_users": 12,
    "total_platforms": 3,
    "total_strings": 1250
  }
}
```

### Workspace Status

- `active` - Workspace is active and operational
- `inactive` - Workspace is temporarily disabled
- `archived` - Workspace is archived (read-only)

---

## List Workspaces

**GET** `/api/v1/workspaces/`

Get all workspaces the authenticated user has access to.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `active`, `inactive`, `archived` |
| `search` | string | Search by name |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Results per page (default: 20) |

### Example Request

```bash
GET /api/v1/workspaces/?status=active
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "ACME Corporation",
      "slug": "acme-corporation",
      "status": "active",
      "created": "2024-01-15T10:00:00Z",
      "last_updated": "2024-11-10T14:30:00Z",
      "created_by": {...},
      "stats": {...}
    },
    {
      "id": 2,
      "name": "Beta Company",
      "slug": "beta-company",
      "status": "active",
      "created": "2024-03-20T09:00:00Z",
      "last_updated": "2024-11-09T11:00:00Z",
      "created_by": {...},
      "stats": {...}
    }
  ]
}
```

---

## Create Workspace

**POST** `/api/v1/workspaces/`

Create a new workspace. **Requires admin privileges**.

### Request Body

```json
{
  "name": "New Company Inc",
  "status": "active"
}
```

### Validation Rules

- `name`: Required, max 200 characters, unique globally
- `slug`: Auto-generated from name
- `status`: Optional, default: `active`

### Example Response (201 Created)

```json
{
  "id": 3,
  "name": "New Company Inc",
  "slug": "new-company-inc",
  "status": "active",
  "created": "2024-11-11T10:00:00Z",
  "last_updated": "2024-11-11T10:00:00Z",
  "created_by": {
    "id": 5,
    "email": "admin@newcompany.com",
    "name": "Jane Admin"
  },
  "stats": {
    "total_projects": 0,
    "total_users": 1,
    "total_platforms": 0,
    "total_strings": 0
  }
}
```

---

## Get Workspace Details

**GET** `/api/v1/workspaces/{id}/`

Get detailed information about a specific workspace.

### Example Response (200 OK)

```json
{
  "id": 1,
  "name": "ACME Corporation",
  "slug": "acme-corporation",
  "status": "active",
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-11-10T14:30:00Z",
  "created_by": {
    "id": 1,
    "email": "admin@acme.com",
    "name": "John Admin"
  },
  "stats": {
    "total_projects": 25,
    "total_users": 12,
    "total_platforms": 3,
    "total_strings": 1250,
    "active_projects": 18,
    "archived_projects": 7
  },
  "users": [
    {
      "id": 1,
      "email": "admin@acme.com",
      "name": "John Admin",
      "role": "admin"
    },
    {
      "id": 5,
      "email": "user@acme.com",
      "name": "Jane User",
      "role": "member"
    }
  ]
}
```

---

## Update Workspace

**PATCH** `/api/v1/workspaces/{id}/`

Update workspace details. **Requires admin privileges**.

### Request Body (Partial Update)

```json
{
  "name": "ACME Corp (Updated)",
  "status": "inactive"
}
```

### Example Response (200 OK)

Returns updated workspace object (same structure as GET).

---

## Delete Workspace

**DELETE** `/api/v1/workspaces/{id}/`

Delete a workspace. **This deletes ALL associated data** (projects, strings, etc.). **Requires admin privileges**.

### Example Response (204 No Content)

No response body.

### Error Response (403 Forbidden)

```json
{
  "error": "Cannot delete workspace with active projects"
}
```

---

## Frontend Integration Examples

### Fetch Workspaces

```javascript
async function fetchWorkspaces() {
  const response = await fetch(`${API_BASE}/workspaces/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}

// Usage
const { results: workspaces } = await fetchWorkspaces();
```

### Workspace Selector

```javascript
// For workspace switcher dropdown
async function getWorkspaceOptions() {
  const { results } = await fetchWorkspaces();
  return results.map(ws => ({
    value: ws.id,
    label: ws.name,
    slug: ws.slug
  }));
}

// Usage in UI
const workspaceOptions = await getWorkspaceOptions();
```

### Create Workspace

```javascript
async function createWorkspace(name) {
  const response = await fetch(`${API_BASE}/workspaces/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ name, status: 'active' })
  });

  if (!response.ok) {
    throw new Error('Failed to create workspace');
  }

  return await response.json();
}
```

---

## Common Use Cases

### 1. Workspace Switcher

```javascript
// Store current workspace in state
const [currentWorkspace, setCurrentWorkspace] = useState(null);

// Load workspaces on mount
useEffect(() => {
  async function loadWorkspaces() {
    const { results } = await fetchWorkspaces();

    // Set first workspace as default
    if (results.length > 0) {
      setCurrentWorkspace(results[0]);
    }
  }
  loadWorkspaces();
}, []);

// Switch workspace
function switchWorkspace(workspaceId) {
  const workspace = workspaces.find(ws => ws.id === workspaceId);
  setCurrentWorkspace(workspace);
  // Reload data for new workspace
  router.push(`/workspaces/${workspaceId}/projects`);
}
```

### 2. Workspace Stats Dashboard

```javascript
async function getWorkspaceStats(workspaceId) {
  const workspace = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  ).then(r => r.json());

  return {
    totalProjects: workspace.stats.total_projects,
    totalStrings: workspace.stats.total_strings,
    totalUsers: workspace.stats.total_users,
    activeProjects: workspace.stats.active_projects
  };
}
```

---

## Multi-Tenant Best Practices

### 1. Always Include Workspace ID

All workspace-scoped API calls should include the workspace ID:

```javascript
// Good
const projects = await fetch(
  `${API_BASE}/workspaces/${workspaceId}/projects/`
);

// Bad - missing workspace scope
const projects = await fetch(`${API_BASE}/projects/`);
```

### 2. Store Current Workspace

```javascript
// In React context or state management
const WorkspaceContext = createContext();

function WorkspaceProvider({ children }) {
  const [workspace, setWorkspace] = useState(null);

  return (
    <WorkspaceContext.Provider value={{ workspace, setWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
}
```

### 3. Workspace Switching

```javascript
// Clear cached data when switching workspaces
function switchWorkspace(newWorkspaceId) {
  // Clear local state
  clearProjectsCache();
  clearStringsCache();

  // Update workspace
  setCurrentWorkspace(newWorkspaceId);

  // Reload data
  loadWorkspaceData(newWorkspaceId);
}
```

---

## Security & Permissions

### Workspace Roles

- **Admin**: Full access to workspace (create, update, delete)
- **Member**: Read/write access to projects and strings
- **Viewer**: Read-only access

### Permission Checks

The API automatically filters workspaces based on user permissions. Users only see workspaces they have access to.

---

## Notes

- Workspace slugs are auto-generated and unique
- All workspace data is isolated (users can't access data from other workspaces)
- Deleting a workspace is irreversible
- Workspace stats are computed on-demand
