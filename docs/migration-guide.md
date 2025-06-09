# Migration Guide

## Overview

This guide helps you migrate from the legacy subdomain-based workspace access to the new flexible workspace access model. The new approach provides greater flexibility while maintaining backwards compatibility.

## Migration from Subdomain-Based Access

### Key Changes

#### Before (Legacy Subdomain-Based)

- **Access Pattern**: `https://client1.yourdomain.com/api/v1/`
- **Workspace Detection**: Automatic via subdomain
- **Frontend Complexity**: Simple but inflexible
- **Multi-Workspace**: Required multiple domains/deployments

#### After (Flexible Workspace Access)

- **Access Pattern**: `https://yourdomain.com/api/v1/` (primary)
- **Workspace Detection**: User authentication + API calls
- **Frontend Complexity**: More control and flexibility
- **Multi-Workspace**: Single deployment, user-based access

### Migration Steps

#### 1. Update API Base URLs

**Old Configuration:**

```javascript
// client1.yourdomain.com frontend
const API_BASE = "https://client1.yourdomain.com/api/v1/";

// client2.yourdomain.com frontend
const API_BASE = "https://client2.yourdomain.com/api/v1/";
```

**New Configuration:**

```javascript
// Single frontend for all workspaces
const API_BASE = "https://yourdomain.com/api/v1/";
```

#### 2. Implement Workspace Selection

**Add workspace discovery to your application:**

```javascript
// 1. Get user's accessible workspaces after authentication
async function loadWorkspaces() {
  const response = await fetch(`${API_BASE}/workspaces/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  return response.json();
}

// 2. User can switch between workspaces
function selectWorkspace(workspaceId) {
  // Store in app state, localStorage, etc.
  setCurrentWorkspace(workspaceId);
  // Reload workspace-specific data
  loadWorkspaceData();
}

// 3. API calls work with any accessible workspace
async function loadDimensions() {
  const response = await fetch(`${API_BASE}/dimensions/`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  // Response automatically filtered by user's workspace access
  return response.json();
}
```

#### 3. Update Authentication Flow

**Legacy Flow:**

1. User logs in to specific subdomain
2. Authentication tied to single workspace
3. No workspace switching capability

**New Flow:**

1. User logs in once for all accessible workspaces
2. Frontend manages workspace context switching
3. API automatically filters data based on user permissions

```javascript
// Authentication and workspace management
class WorkspaceManager {
  constructor(apiBase) {
    this.apiBase = apiBase;
    this.currentWorkspace = null;
    this.availableWorkspaces = [];
  }

  async authenticate(credentials) {
    // Login user
    const response = await fetch(`${this.apiBase}/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });

    const { token } = await response.json();
    this.token = token;

    // Load available workspaces
    await this.loadWorkspaces();

    // Set default workspace if available
    if (this.availableWorkspaces.length > 0) {
      this.setCurrentWorkspace(this.availableWorkspaces[0].id);
    }

    return token;
  }

  async loadWorkspaces() {
    const response = await fetch(`${this.apiBase}/workspaces/`, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    this.availableWorkspaces = await response.json().results;
  }

  setCurrentWorkspace(workspaceId) {
    this.currentWorkspace = workspaceId;
    // Trigger app refresh or state update
    this.onWorkspaceChange?.(workspaceId);
  }

  async apiCall(endpoint, options = {}) {
    return fetch(`${this.apiBase}${endpoint}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
  }
}
```

#### 4. Optional: Maintain Subdomain Support

For gradual migration, you can maintain both access patterns:

```javascript
// Detect access pattern and configure accordingly
function getApiConfig() {
  const hostname = window.location.hostname;

  // Check if using subdomain pattern
  if (hostname.includes(".") && !hostname.startsWith("www")) {
    const subdomain = hostname.split(".")[0];
    return {
      apiBase: `https://${hostname}/api/v1/`,
      workspaceMode: "subdomain",
      workspaceId: getWorkspaceIdFromSubdomain(subdomain),
    };
  }

  // Use new flexible access pattern
  return {
    apiBase: "https://yourdomain.com/api/v1/",
    workspaceMode: "flexible",
    workspaceId: null, // Determined by user authentication
  };
}
```

### Frontend Implementation Examples

#### React Implementation

```jsx
// WorkspaceProvider.jsx
import React, { createContext, useContext, useState, useEffect } from "react";

const WorkspaceContext = createContext();

export function WorkspaceProvider({ children }) {
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [availableWorkspaces, setAvailableWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  async function loadWorkspaces() {
    try {
      const response = await fetch("/api/v1/workspaces/", {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await response.json();
      setAvailableWorkspaces(data.results);

      // Set first workspace as default
      if (data.results.length > 0 && !currentWorkspace) {
        setCurrentWorkspace(data.results[0]);
      }
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setLoading(false);
    }
  }

  const value = {
    currentWorkspace,
    availableWorkspaces,
    setCurrentWorkspace,
    loading,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export const useWorkspace = () => useContext(WorkspaceContext);

// WorkspaceSwitcher.jsx
import React from "react";
import { useWorkspace } from "./WorkspaceProvider";

export function WorkspaceSwitcher() {
  const { currentWorkspace, availableWorkspaces, setCurrentWorkspace } =
    useWorkspace();

  return (
    <select
      value={currentWorkspace?.id || ""}
      onChange={(e) => {
        const workspace = availableWorkspaces.find(
          (w) => w.id === parseInt(e.target.value)
        );
        setCurrentWorkspace(workspace);
      }}
    >
      {availableWorkspaces.map((workspace) => (
        <option key={workspace.id} value={workspace.id}>
          {workspace.name}
        </option>
      ))}
    </select>
  );
}
```

#### Vue.js Implementation

```javascript
// workspace.js (Pinia store)
import { defineStore } from "pinia";
import { api } from "@/services/api";

export const useWorkspaceStore = defineStore("workspace", {
  state: () => ({
    currentWorkspace: null,
    availableWorkspaces: [],
    loading: false,
  }),

  actions: {
    async loadWorkspaces() {
      this.loading = true;
      try {
        const response = await api.get("/workspaces/");
        this.availableWorkspaces = response.data.results;

        if (this.availableWorkspaces.length > 0 && !this.currentWorkspace) {
          this.setCurrentWorkspace(this.availableWorkspaces[0]);
        }
      } catch (error) {
        console.error("Failed to load workspaces:", error);
      } finally {
        this.loading = false;
      }
    },

    setCurrentWorkspace(workspace) {
      this.currentWorkspace = workspace;
      // Trigger data refresh
      this.refreshWorkspaceData();
    },

    async refreshWorkspaceData() {
      // Reload workspace-specific data
      // This will be automatically filtered by the API
      await this.loadDimensions();
      await this.loadRules();
    },
  },
});
```

### Database Migration

The database schema supports both access patterns without changes. No database migration is required for the API functionality.

#### User and Workspace Setup

Ensure users have proper workspace assignments:

```bash
# Django management command to verify workspace assignments
python manage.py shell

# Check user workspace assignments
from users.models import UserAccount
from master_data.models import WorkspaceUser

for user in UserAccount.objects.all():
    assignments = WorkspaceUser.objects.filter(user=user)
    print(f"User {user.email}: {assignments.count()} workspace(s)")
    for assignment in assignments:
        print(f"  - {assignment.workspace.name} ({assignment.role})")
```

### Testing Migration

#### Phase 1: Parallel Testing

Run both access patterns simultaneously:

```bash
# Test legacy subdomain access
curl -H "Authorization: Bearer $TOKEN" \
     https://client1.yourdomain.com/api/v1/workspaces/

# Test new flexible access
curl -H "Authorization: Bearer $TOKEN" \
     https://yourdomain.com/api/v1/workspaces/
```

#### Phase 2: Validation

Verify data consistency between access patterns:

```javascript
// Test script to compare responses
async function validateMigration() {
  const token = "your-auth-token";

  // Legacy response
  const legacyResponse = await fetch(
    "https://client1.yourdomain.com/api/v1/dimensions/",
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  const legacyData = await legacyResponse.json();

  // New flexible response (should be filtered to same workspace)
  const newResponse = await fetch("https://yourdomain.com/api/v1/dimensions/", {
    headers: { Authorization: `Bearer ${token}` },
  });
  const newData = await newResponse.json();

  // Compare data (should be equivalent for single-workspace users)
  console.log("Legacy data count:", legacyData.count);
  console.log("New data count:", newData.count);
  console.log(
    "Data consistency:",
    JSON.stringify(legacyData) === JSON.stringify(newData)
  );
}
```

#### Phase 3: Production Cutover

1. **Update DNS/Load Balancer**: Point main domain to new configuration
2. **Redirect Subdomains**: Optional redirect to main domain with workspace selection
3. **Monitor**: Watch for errors and user experience issues
4. **Rollback Plan**: Keep subdomain configuration available for quick rollback

### Rollback Plan

If issues arise during migration:

#### Immediate Rollback

```bash
# Restore subdomain routing configuration
# Update load balancer to previous configuration
# DNS changes take time, so plan accordingly
```

#### Gradual Rollback

```javascript
// Feature flag to switch between access patterns
const USE_LEGACY_SUBDOMAIN =
  process.env.REACT_APP_USE_LEGACY_SUBDOMAIN === "true";

function getApiBase() {
  if (USE_LEGACY_SUBDOMAIN) {
    return `https://${getSubdomain()}.yourdomain.com/api/v1/`;
  }
  return "https://yourdomain.com/api/v1/";
}
```

### Benefits After Migration

#### For Users

- **Single Login**: Access all workspaces with one authentication
- **Workspace Switching**: Easy switching between accessible workspaces
- **Consistent Interface**: Same UI/UX across all workspaces

#### For Developers

- **Simplified Deployment**: Single application deployment
- **Code Reuse**: Shared components and logic across workspaces
- **Easier Maintenance**: Single codebase to maintain

#### For Administrators

- **Centralized Management**: Single admin panel for all workspaces
- **User Management**: Assign users to multiple workspaces easily
- **Reduced Infrastructure**: Fewer deployments and domains to manage

### Support and Troubleshooting

#### Common Issues

1. **Empty Workspace List**: User may not have workspace assignments

   ```bash
   # Check user assignments in Django admin
   python manage.py shell
   from users.models import UserAccount
   user = UserAccount.objects.get(email='user@example.com')
   print(user.workspace_assignments.all())
   ```

2. **Authentication Errors**: Token may be workspace-specific

   ```javascript
   // Ensure using correct API base URL
   const response = await fetch("https://yourdomain.com/api/v1/auth/verify/", {
     headers: { Authorization: `Bearer ${token}` },
   });
   ```

3. **CORS Issues**: Update CORS configuration for new domain
   ```python
   # settings.py
   CORS_ALLOWED_ORIGINS = [
       "https://yourdomain.com",
       "https://app.yourdomain.com",
   ]
   ```

#### Getting Help

- **Migration Issues**: Check the troubleshooting sections in development setup
- **User Assignment**: Use Django admin panel for workspace assignments
- **API Issues**: See API documentation for endpoint details

---

_Last Updated: 2025-06-08_
_Migration: Subdomain to Flexible Access_
