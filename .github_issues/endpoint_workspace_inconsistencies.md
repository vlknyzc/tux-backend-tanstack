---
title: "[AUDIT] [HIGH] Inconsistent workspace filtering patterns across API endpoints"
labels: ["api-design", "high", "refactoring", "consistency"]
assignees: []
---

## Description

The API has inconsistent patterns for workspace filtering and access control across different endpoints. Some endpoints use `workspace_id` in the URL path, others use query parameters (`?workspace=`), and some have mixed approaches. This creates confusion, security risks, and maintenance issues.

## Summary of Inconsistencies

### Pattern 1: Workspace ID in URL Path ✅ (Preferred Pattern)
**Location**: `master_data/urls_main_api.py`, `master_data/urls_projects.py`

**Endpoints using this pattern:**
- `/api/v1/workspaces/{workspace_id}/strings/` - StringViewSet
- `/api/v1/workspaces/{workspace_id}/string-details/` - StringDetailViewSet
- `/api/v1/workspaces/{workspace_id}/multi-operations/` - MultiOperationsViewSet
- `/api/v1/workspaces/{workspace_id}/projects/` - ProjectViewSet
- `/api/v1/workspaces/{workspace_id}/projects/{id}/platforms/{platform_id}/strings/` - Project string endpoints

**Characteristics:**
- Uses `WorkspaceValidationMixin` for validation
- Workspace ID extracted from `kwargs['workspace_id']`
- Set via `request.workspace_id` attribute
- Validated before request processing in `dispatch()` method
- **Security**: Strong - workspace context enforced at URL level

**Example:**
```python
# URL: /api/v1/workspaces/123/strings/
class StringViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    def dispatch(self, request, *args, **kwargs):
        workspace_id = kwargs.get('workspace_id')  # From URL path
        # Validation happens here
```

---

### Pattern 2: Query Parameter (`?workspace=`) ⚠️ (Inconsistent Pattern)
**Location**: `master_data/views/dimension_views.py`, `master_data/views/rule_views.py`

**Endpoints using this pattern:**
- `/api/v1/dimensions/?workspace=123` - DimensionViewSet
- `/api/v1/dimension-values/?workspace=123` - DimensionValueViewSet
- `/api/v1/dimension-constraints/?workspace=123` - DimensionConstraintViewSet
- `/api/v1/rules/?workspace=123` - RuleViewSet
- `/api/v1/rule-details/?workspace=123` - RuleDetailViewSet
- `/api/v1/rule-nested/?workspace=123` - RuleNestedViewSet
- `/api/v1/propagation-jobs/` - PropagationJobViewSet (uses `request.workspace`)
- `/api/v1/propagation-errors/` - PropagationErrorViewSet (uses `request.workspace`)
- `/api/v1/enhanced-string-details/` - EnhancedStringDetailViewSet (uses `request.workspace`)

**Characteristics:**
- Uses `WorkspaceMixin` to parse query parameter
- Workspace ID from `request.query_params.get('workspace')` or `request.GET.get('workspace')`
- Can also accept workspace in request body (mixed approach)
- Validation happens in `get_queryset()` method
- **Security**: Medium - workspace can be omitted, relies on default behavior

**Example:**
```python
# URL: /api/v1/dimensions/?workspace=123
class DimensionViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    def get_workspace_id(self):
        raw = getattr(self.request, 'workspace', None)
        if not raw:
            raw = self.get_workspace_param('workspace')  # From query param
        return int(raw) if raw else None
    
    def get_queryset(self):
        wid = self.get_workspace_id()
        if wid:
            self.check_workspace_access(wid)
            return models.Dimension.objects.all_workspaces().filter(workspace_id=wid)
        # Falls back to user's accessible workspaces
```

---

### Pattern 3: No Workspace Filtering ❌ (Global Resources)
**Location**: `master_data/views/workspace_views.py`, `master_data/views/field_views.py`

**Endpoints:**
- `/api/v1/workspaces/` - WorkspaceViewSet (no workspace filtering - it IS the workspace)
- `/api/v1/platforms/` - PlatformViewSet (global, not workspace-scoped)
- `/api/v1/fields/` - FieldViewSet (global, not workspace-scoped)

**Characteristics:**
- These are intentionally global or workspace-managing resources
- WorkspaceViewSet filters by user access, not workspace ID
- PlatformViewSet and FieldViewSet return all records globally
- **Security**: Appropriate for these resource types

---

### Pattern 4: Mixed Approaches (Query Param + Request Body) ⚠️⚠️ (Problematic)
**Location**: `master_data/views/dimension_views.py`

**Endpoints:**
- `/api/v1/dimensions/bulk_create/?workspace=123` OR with `{"workspace": 123}` in body
- `/api/v1/dimension-values/bulk_create/?workspace=123` OR with `{"workspace": 123}` in body

**Characteristics:**
- Accepts workspace in EITHER query parameter OR request body
- Fallback logic: checks query param first, then request body
- **Security**: Low - confusing, hard to validate consistently

**Example:**
```python
def bulk_create(self, request, version=None):
    wid = self.get_workspace_id()  # From query param
    
    # If workspace not found in query params, check request body
    if not wid and hasattr(request, 'data') and 'workspace' in request.data:
        wid = int(request.data['workspace'])  # From request body
    
    if not wid:
        return Response({'error': 'No workspace context available...'})
```

---

### Pattern 5: Workspace from Request Attribute (Middleware) 🔄 (Unclear Pattern)
**Location**: `master_data/views/propagation_views.py`

**Endpoints:**
- `/api/v1/propagation-jobs/` - Uses `getattr(request, 'workspace', None)`
- `/api/v1/propagation-errors/` - Uses `getattr(request, 'workspace', None)`
- `/api/v1/enhanced-string-details/` - Has `_resolve_workspace_context()` method

**Characteristics:**
- Workspace set by middleware (`WorkspaceMiddleware`)
- Middleware sets `request.workspace` and `request.workspace_id`
- But middleware currently sets both to `None` by default!
- **Security**: Low - unclear where workspace comes from

**Example:**
```python
def get_queryset(self):
    workspace = getattr(self.request, 'workspace', None)  # From middleware?
    
    if not workspace:
        if hasattr(self.request, 'user') and self.request.user.is_superuser:
            return models.PropagationJob.objects.all_workspaces()
        return models.PropagationJob.objects.none()  # Returns empty!
```

---

## Detailed Inconsistency Analysis

### 1. URL Structure Inconsistency

| Endpoint Group | Pattern | Example URL |
|---------------|---------|-------------|
| Strings | Path | `/api/v1/workspaces/123/strings/` |
| String Details | Path | `/api/v1/workspaces/123/string-details/` |
| Projects | Path | `/api/v1/workspaces/123/projects/` |
| Dimensions | Query | `/api/v1/dimensions/?workspace=123` |
| Dimension Values | Query | `/api/v1/dimension-values/?workspace=123` |
| Rules | Query | `/api/v1/rules/?workspace=123` |
| Propagation Jobs | Attribute | `/api/v1/propagation-jobs/` (workspace from request.workspace) |

### 2. Validation Timing Inconsistency

| Pattern | When Validation Occurs | Method |
|---------|----------------------|--------|
| URL Path | Before request processing | `WorkspaceValidationMixin.dispatch()` |
| Query Parameter | During queryset filtering | `get_queryset()` or `get_object()` |
| Request Body | During serialization/action | `perform_create()` or custom action |

### 3. Fallback Behavior Inconsistency

| Endpoint | Fallback Behavior |
|----------|-------------------|
| **URL Path endpoints** | No fallback - workspace_id required |
| **Query Param endpoints** | Falls back to user's accessible workspaces (via manager) |
| **Propagation endpoints** | Returns empty queryset if no workspace |

### 4. Superuser Behavior Inconsistency

| Endpoint Type | Superuser Behavior |
|---------------|-------------------|
| URL Path | Superusers still need workspace_id in URL |
| Query Param | Superusers can omit workspace, see all workspaces |
| Propagation | Superusers can see all if no workspace provided |

### 5. Error Handling Inconsistency

| Pattern | Error Response |
|---------|----------------|
| URL Path | `PermissionDenied` exception (500 error) |
| Query Param | Empty queryset or `PermissionDenied` |
| Request Body | 400 Bad Request with error message |

### 6. Documentation Inconsistency

- Some endpoints documented in OpenAPI schema with workspace_id parameter
- Others not documented at all
- Mixed parameter types (PATH vs QUERY vs BODY)

---

## Security Concerns

### 1. Inconsistent Access Control

**Issue**: Different endpoints validate workspace access at different times:
- URL path endpoints: Validate in `dispatch()` - early and consistent
- Query param endpoints: Validate in `get_queryset()` - later, can be bypassed
- Propagation endpoints: May return empty queryset silently

**Risk**: Some endpoints may allow unauthorized access if validation logic differs.

### 2. Workspace ID Injection Risk

**Issue**: Query parameter approach allows workspace ID manipulation:
```python
# Attacker could try: /api/v1/dimensions/?workspace=999999
# vs enforced path: /api/v1/workspaces/123/dimensions/ (can't change 123 easily)
```

**Risk**: Easier to attempt workspace enumeration attacks with query params.

### 3. Missing Workspace Context

**Issue**: Some endpoints may return data without workspace filtering:
- Propagation endpoints return empty queryset if workspace not set
- Query param endpoints fall back to user's workspaces (may expose unintended data)

---

## Recommended Standard

### Standard Pattern: Workspace ID in URL Path ✅

**Rationale:**
1. **Security**: Enforces workspace context at URL level
2. **Consistency**: Matches RESTful resource hierarchy
3. **Clarity**: Makes workspace relationship explicit
4. **Validation**: Early validation prevents unauthorized access
5. **Documentation**: Easier to document in OpenAPI schema

### Proposed URL Structure

```
# Workspace-scoped resources (workspace_id in path)
/api/v1/workspaces/{workspace_id}/strings/
/api/v1/workspaces/{workspace_id}/string-details/
/api/v1/workspaces/{workspace_id}/projects/
/api/v1/workspaces/{workspace_id}/dimensions/          # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/dimension-values/    # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/dimension-constraints/ # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/rules/               # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/rule-details/        # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/propagation-jobs/    # ⚠️ MIGRATE
/api/v1/workspaces/{workspace_id}/propagation-errors/  # ⚠️ MIGRATE

# Global resources (no workspace_id)
/api/v1/workspaces/                                    # ✅ Stays as-is
/api/v1/platforms/                                     # ✅ Stays as-is
/api/v1/fields/                                        # ✅ Stays as-is
```

### Implementation Standard

**All workspace-scoped endpoints should:**

1. **Use `WorkspaceValidationMixin`**:
   ```python
   class DimensionViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
       # Workspace ID comes from kwargs['workspace_id']
       # Validated in dispatch() method
   ```

2. **URL Pattern**:
   ```python
   router.register(
       r'workspaces/(?P<workspace_id>\d+)/dimensions',
       DimensionViewSet,
       basename='dimension'
   )
   ```

3. **Access workspace_id consistently**:
   ```python
   def get_queryset(self):
       workspace_id = self.kwargs.get('workspace_id')  # From URL
       # Already validated by WorkspaceValidationMixin
       return models.Dimension.objects.filter(workspace_id=workspace_id)
   ```

4. **Error handling**:
   - Use `PermissionDenied` for access violations
   - Return 404 for non-existent workspaces
   - Return 403 for unauthorized access

---

## Migration Plan

### Phase 1: Document Current State ✅
- [x] Audit all endpoints (this document)
- [ ] Create migration guide
- [ ] Update API documentation

### Phase 2: Standardize New Endpoints
- [ ] Ensure all new endpoints use URL path pattern
- [ ] Update code review checklist
- [ ] Add linting rules if possible

### Phase 3: Migrate Existing Endpoints (Breaking Changes)

**Priority Order:**
1. **High Priority** (Security-sensitive):
   - [ ] Rules endpoints (`/api/v1/rules/`)
   - [ ] Rule details (`/api/v1/rule-details/`)
   - [ ] Propagation endpoints

2. **Medium Priority**:
   - [ ] Dimensions (`/api/v1/dimensions/`)
   - [ ] Dimension values (`/api/v1/dimension-values/`)
   - [ ] Dimension constraints (`/api/v1/dimension-constraints/`)

**Migration Strategy:**
- Option A: Add new endpoints, deprecate old ones (recommended)
- Option B: Support both patterns temporarily (not recommended - adds complexity)
- Option C: Breaking change with version bump (v2)

### Phase 4: Cleanup
- [ ] Remove `WorkspaceMixin` (query param pattern)
- [ ] Remove query parameter support
- [ ] Update all tests
- [ ] Update API documentation

---

## Examples of Required Changes

### Before (Query Parameter Pattern):
```python
# URL: /api/v1/dimensions/?workspace=123
class DimensionViewSet(WorkspaceMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        wid = self.get_workspace_id()  # From query param
        if wid:
            self.check_workspace_access(wid)
            return models.Dimension.objects.all_workspaces().filter(workspace_id=wid)
        # Fallback logic...
```

### After (URL Path Pattern):
```python
# URL: /api/v1/workspaces/123/dimensions/
class DimensionViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        workspace_id = self.kwargs.get('workspace_id')  # From URL path
        # Already validated by WorkspaceValidationMixin.dispatch()
        return models.Dimension.objects.filter(workspace_id=workspace_id)
```

---

## Testing Requirements

All migrated endpoints should have tests for:

1. **Workspace Access Control**:
   - User without workspace access gets 403
   - User with workspace access gets 200
   - Superuser can access any workspace

2. **URL Path Validation**:
   - Invalid workspace_id returns 404
   - Missing workspace_id returns 404 (if required)

3. **Backward Compatibility** (if supporting both):
   - Old query param pattern still works
   - New URL path pattern works
   - Deprecation warnings for old pattern

---

## Related Issues

- Rate limiting not configured (#rate-limiting-issue)
- Missing request body size limits (#request-size-limits-issue)
- Debug endpoint security issue (#debug-endpoint-issue)

---

## Severity

**HIGH** - Inconsistent patterns create:
- Security vulnerabilities
- Developer confusion
- Maintenance burden
- Poor API design
- Difficult documentation

## Next Steps

1. **Review this audit** with team
2. **Decide on migration strategy** (deprecation vs breaking change)
3. **Create migration tickets** for each endpoint group
4. **Update API design guidelines** to prevent future inconsistencies
5. **Add code review checklist** item for workspace filtering patterns

