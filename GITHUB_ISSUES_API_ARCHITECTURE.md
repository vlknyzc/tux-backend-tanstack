# REST API Architecture Issues

This document contains GitHub issues for REST API architecture improvements.

---

## Issue #1: Inconsistent Workspace Handling in API Endpoints

**Severity:** High  
**Type:** Architecture / Consistency  
**Labels:** `api-design`, `breaking-change`, `workspace`

### Problem

The API currently uses two different patterns for workspace scoping:

1. **Path-based pattern** (used by main API endpoints):

   - `/api/v1/workspaces/{workspace_id}/submissions/`
   - `/api/v1/workspaces/{workspace_id}/strings/`
   - `/api/v1/workspaces/{workspace_id}/string-details/`
   - `/api/v1/workspaces/{workspace_id}/multi-operations/`

2. **Query parameter pattern** (used by other endpoints):

   - `/api/v1/dimensions/?workspace=123`
   - `/api/v1/dimension-values/?workspace=123`
   - `/api/v1/rules/?workspace=123`
   - `/api/v1/dimension-constraints/?workspace=123`
   - `/api/v1/propagation-jobs/?workspace=123`

3. **Request body pattern** (also supported in some endpoints):
   - Some endpoints allow workspace in request body as fallback

### Impact

- **Developer confusion**: Inconsistent patterns make API harder to learn and use
- **Security concerns**: Different validation paths may have different security checks
- **Client-side complexity**: Clients must handle multiple patterns
- **Documentation overhead**: More complex to document and maintain
- **Testing complexity**: Different test patterns needed for different endpoints

### Recommendation

**Standardize on path-based workspace scoping** for all workspace-scoped resources:

```
✅ GOOD: /api/v1/workspaces/{workspace_id}/dimensions/
✅ GOOD: /api/v1/workspaces/{workspace_id}/dimension-values/
✅ GOOD: /api/v1/workspaces/{workspace_id}/rules/
❌ BAD:  /api/v1/dimensions/?workspace=123
❌ BAD:  /api/v1/rules/?workspace=123
```

### Rationale

1. **Clearer resource hierarchy**: Path-based approach shows workspace as a parent resource
2. **Better security**: Workspace validation happens at URL routing level
3. **RESTful design**: Follows REST principles of resource nesting
4. **Consistency**: Matches existing main API endpoints pattern
5. **Better caching**: Workspace-aware URLs are easier to cache

### Implementation Plan

1. **Phase 1** (Non-breaking):

   - Add new path-based endpoints alongside existing query-param endpoints
   - Deprecate query-param endpoints with proper warnings
   - Update documentation

2. **Phase 2** (Breaking):
   - Remove query-param workspace support
   - Update all clients
   - Remove deprecated code

### Affected Endpoints

- `/api/v1/dimensions/` → `/api/v1/workspaces/{workspace_id}/dimensions/`
- `/api/v1/dimension-values/` → `/api/v1/workspaces/{workspace_id}/dimension-values/`
- `/api/v1/dimension-constraints/` → `/api/v1/workspaces/{workspace_id}/dimension-constraints/`
- `/api/v1/rules/` → `/api/v1/workspaces/{workspace_id}/rules/`
- `/api/v1/rule-details/` → `/api/v1/workspaces/{workspace_id}/rule-details/`
- `/api/v1/rule-nested/` → `/api/v1/workspaces/{workspace_id}/rule-nested/`
- `/api/v1/propagation-jobs/` → `/api/v1/workspaces/{workspace_id}/propagation-jobs/`
- `/api/v1/propagation-errors/` → `/api/v1/workspaces/{workspace_id}/propagation-errors/`
- `/api/v1/propagation-settings/` → `/api/v1/workspaces/{workspace_id}/propagation-settings/`

### Exceptions

- **Global resources** (not workspace-scoped):
  - `/api/v1/workspaces/` (workspace management)
  - `/api/v1/platforms/` (global, shared across workspaces)
  - `/api/v1/fields/` (global, shared across workspaces)
  - `/api/v1/users/` (user management)

---

## Issue #2: Naming Inconsistencies in Resource Names

**Severity:** Medium  
**Type:** Consistency / Naming  
**Labels:** `api-design`, `naming`, `consistency`

### Problem

There are inconsistencies in resource naming patterns:

1. **Singular vs Plural**:

   - `workspace-users` (singular "workspace")
   - `workspaces` (plural)

2. **Compound naming**:

   - `dimension-values` ✅
   - `string-details` ✅
   - `rule-details` ✅
   - `multi-operations` ✅
   - `propagation-jobs` ✅
   - `propagation-errors` ✅
   - `propagation-settings` ✅
   - `workspace-users` (should be `workspace-users` or `workspace-user-assignments`?)

3. **Hyphenation consistency**:
   - Most compound resources use hyphens correctly ✅
   - Need to verify all follow same pattern

### Impact

- **Developer confusion**: Inconsistent naming makes API harder to remember
- **Automated tooling**: Code generators struggle with inconsistencies
- **Documentation**: Harder to organize and navigate

### Recommendation

**Standardize on plural, hyphenated resource names:**

```
✅ GOOD: /api/v1/workspaces/{workspace_id}/dimension-values/
✅ GOOD: /api/v1/workspaces/{workspace_id}/string-details/
✅ GOOD: /api/v1/workspaces/{workspace_id}/rule-details/
✅ GOOD: /api/v1/workspaces/{workspace_id}/propagation-jobs/

❓ REVIEW: /api/v1/workspace-users/
   → Consider: /api/v1/workspace-user-assignments/
   → Or: /api/v1/workspaces/{workspace_id}/users/
```

### Rules

1. **Always use plural** for collection endpoints
2. **Use hyphens** for compound words
3. **Be descriptive** - prefer clarity over brevity
4. **Follow REST conventions** - resources are nouns, actions are verbs

### Action Items

- [ ] Review all resource names for consistency
- [ ] Decide on `workspace-users` naming (assignment vs membership)
- [ ] Update all endpoints to follow consistent pattern
- [ ] Update documentation

---

## Issue #3: Inconsistent Bulk Operation Patterns

**Severity:** Medium  
**Type:** Consistency / API Design  
**Labels:** `api-design`, `bulk-operations`, `consistency`

### Problem

Bulk operations are implemented inconsistently:

1. **Custom action endpoints**:

   - `/api/v1/workspaces/{workspace_id}/strings/bulk/` (POST)
   - `/api/v1/workspaces/{workspace_id}/string-details/bulk/` (POST, PATCH, DELETE)
   - `/api/v1/workspaces/{workspace_id}/submissions/{id}/strings/bulk/` (POST, DELETE)

2. **Action method endpoints**:

   - `/api/v1/dimensions/bulk_create/` (POST)
   - `/api/v1/dimension-values/bulk_create/` (POST)

3. **Separate multi-operations endpoint**:
   - `/api/v1/workspaces/{workspace_id}/multi-operations/execute/`
   - `/api/v1/workspaces/{workspace_id}/multi-operations/validate/`

### Impact

- **Developer confusion**: Multiple patterns for similar operations
- **Inconsistent behavior**: Different error handling and validation
- **Client complexity**: Must handle multiple patterns

### Recommendation

**Standardize on `/bulk/` action pattern:**

```
✅ GOOD: POST   /api/v1/workspaces/{workspace_id}/dimensions/bulk/
✅ GOOD: POST   /api/v1/workspaces/{workspace_id}/strings/bulk/
✅ GOOD: PATCH  /api/v1/workspaces/{workspace_id}/string-details/bulk/
✅ GOOD: DELETE /api/v1/workspaces/{workspace_id}/string-details/bulk/

❌ BAD:  POST   /api/v1/dimensions/bulk_create/
```

### Standard Pattern

All bulk operations should follow:

```python
@action(detail=False, methods=['post', 'patch', 'delete'], url_path='bulk')
def bulk(self, request, workspace_id=None):
    """Handle bulk create/update/delete operations"""
    if request.method == 'POST':
        # Bulk create
    elif request.method == 'PATCH':
        # Bulk update
    elif request.method == 'DELETE':
        # Bulk delete
```

### Action Items

- [ ] Migrate `bulk_create` actions to `/bulk/` pattern
- [ ] Ensure consistent request/response formats
- [ ] Update documentation
- [ ] Keep `multi-operations` as separate endpoint (it's for atomic multi-resource operations)

---

## Issue #4: Inconsistent HTTP Method Usage

**Severity:** Low  
**Type:** REST Conventions  
**Labels:** `api-design`, `rest`, `http-methods`

### Problem

Some endpoints don't follow standard REST HTTP method conventions:

1. **Strings endpoint**:

   - No PUT/PATCH (only DELETE) - strings are generated from details
   - ✅ This is intentional and well-documented

2. **Rule configuration endpoints**:

   - `/api/v1/rules/{rule_id}/validation/` uses POST (could be GET)
   - `/api/v1/rules/generation-preview/` uses POST (could be GET)
   - `/api/v1/rules/cache/invalidate/` uses POST (could be DELETE)

3. **Multi-operations**:
   - `/api/v1/workspaces/{workspace_id}/multi-operations/execute/` - POST ✅
   - `/api/v1/workspaces/{workspace_id}/multi-operations/validate/` - POST ✅
   - (These are actions, not resources, so POST is correct)

### Impact

- Minor inconsistency in some endpoints
- Mostly intentional design decisions

### Recommendation

**Review and document exceptions to standard REST patterns:**

1. **Action-based endpoints** (use POST):

   - `/api/v1/rules/{rule_id}/validation/` - POST ✅ (action with side effects)
   - `/api/v1/rules/generation-preview/` - POST ✅ (may have side effects)
   - `/api/v1/rules/cache/invalidate/` - POST ✅ (action, not resource deletion)

2. **Resource-based endpoints** (use standard methods):
   - Collections: GET, POST
   - Detail: GET, PUT, PATCH, DELETE

### Action Items

- [ ] Review all POST endpoints that don't create resources
- [ ] Document intentional deviations from REST conventions
- [ ] Consider if `cache/invalidate` should be DELETE (it's deleting cache, not a resource)

---

## Issue #5: Inconsistent Filter Parameter Naming

**Severity:** Low  
**Type:** Consistency / Query Parameters  
**Labels:** `api-design`, `query-parameters`, `filters`

### Problem

Filter parameters are inconsistent:

1. **Workspace filtering**:

   - Some endpoints use `?workspace=123`
   - Others use workspace in URL path

2. **ID filtering**:

   - Some filters use `?dimension=123` (references dimension ID)
   - Others use `?dimension_id=123`
   - Some use `?field__id=123`

3. **Related resource filtering**:
   - `?platform=123` vs `?platform_id=123`
   - `?field=123` vs `?field_id=123`

### Impact

- **Developer confusion**: Hard to remember which parameter name to use
- **Client errors**: Incorrect parameter names lead to failed requests

### Recommendation

**Standardize filter parameter naming:**

1. **For foreign key relationships**:

   - Use the relationship name: `?dimension=123` not `?dimension_id=123`
   - Use `?workspace=123` only for global resources (when workspace is in query param)

2. **For nested relationships**:

   - Use double underscore: `?field__platform=123`
   - Not: `?field_platform_id=123`

3. **For boolean/enum filters**:
   - Use descriptive names: `?status=active`, `?is_default=true`

### Current State Analysis

```python
# Dimensions
?workspace=123       # ✅ Good (but should be in path)
?type=...            # ✅ Good
?status=...          # ✅ Good

# Rules
?workspace=123       # ✅ Good (but should be in path)
?platform=123        # ✅ Good
?field=123           # ✅ Good
?status=...          # ✅ Good

# Strings
?submission=123      # ✅ Good
?field=123           # ✅ Good
?platform=123        # ✅ Good (via rule__platform__id)
```

### Action Items

- [ ] Audit all filter parameters
- [ ] Standardize naming convention
- [ ] Update documentation
- [ ] Add OpenAPI schema for all filters

---

## Issue #6: Missing Workspace Validation Consistency

**Severity:** High  
**Type:** Security / Validation  
**Labels:** `security`, `workspace`, `validation`

### Problem

Workspace validation is implemented differently across endpoints:

1. **Path-based endpoints** (using `WorkspaceValidationMixin`):

   - Validation happens at dispatch level
   - Workspace ID extracted from URL
   - Access check performed early

2. **Query-param endpoints** (using `WorkspaceMixin`):

   - Validation happens in `get_queryset()` or `perform_create()`
   - Workspace ID extracted from query params or request body
   - Access check may happen late or inconsistently

3. **Some endpoints** may not validate workspace access properly

### Impact

- **Security risk**: Inconsistent validation may allow unauthorized access
- **Code duplication**: Similar validation logic in multiple places
- **Maintenance burden**: Changes to validation logic must be applied in multiple places

### Recommendation

**Standardize workspace validation:**

1. **Use `WorkspaceValidationMixin`** for all workspace-scoped endpoints
2. **Extract workspace from URL path** (not query params or body)
3. **Validate early** in `dispatch()` method
4. **Filter queryset automatically** in `get_queryset()`

### Implementation

```python
# Standard pattern for all workspace-scoped viewsets
class MyResourceViewSet(WorkspaceValidationMixin, viewsets.ModelViewSet):
    """
    Workspace-scoped resource.
    URL: /api/v1/workspaces/{workspace_id}/my-resources/
    """
    # WorkspaceValidationMixin handles:
    # - Workspace extraction from URL
    # - Access validation
    # - Queryset filtering
    # - Workspace injection on create
```

### Action Items

- [ ] Audit all viewsets for workspace validation
- [ ] Migrate query-param endpoints to path-based with WorkspaceValidationMixin
- [ ] Add tests for workspace access validation
- [ ] Document workspace validation pattern

---

## Issue #7: Inconsistent Error Response Formats

**Severity:** Low  
**Type:** Consistency / Error Handling  
**Labels:** `api-design`, `error-handling`, `consistency`

### Problem

Error responses may be inconsistent across endpoints:

1. **Validation errors**:

   - DRF standard format: `{"field": ["error message"]}`
   - Custom formats in some endpoints

2. **Permission errors**:

   - Some return `PermissionDenied` with DRF format
   - Others return custom error objects

3. **Bulk operation errors**:
   - Some return `{"error": "message"}`
   - Others return `{"errors": [...]}`

### Impact

- **Client complexity**: Must handle multiple error formats
- **Developer confusion**: Unpredictable error responses

### Recommendation

**Standardize error response format:**

1. **Validation errors** (400):

   ```json
   {
     "field_name": ["Error message 1", "Error message 2"]
   }
   ```

2. **Permission errors** (403):

   ```json
   {
     "detail": "Access denied to workspace 123"
   }
   ```

3. **Bulk operation errors**:
   ```json
   {
     "success_count": 5,
     "error_count": 2,
     "results": [...],
     "errors": [
       {"index": 1, "field": "name", "error": "Validation failed"},
       {"index": 3, "error": "Already exists"}
     ]
   }
   ```

### Action Items

- [ ] Audit all error responses
- [ ] Standardize error format
- [ ] Update error handling middleware if needed
- [ ] Document error response formats

---

## Issue #8: Nested Resource URL Pattern Inconsistency

**Severity:** Low  
**Type:** Consistency / URL Structure  
**Labels:** `api-design`, `url-structure`, `nested-resources`

### Problem

Nested resources use different patterns:

1. **Nested routes** (via nested router):

   - `/api/v1/workspaces/{workspace_id}/submissions/{submission_id}/strings/`
   - `/api/v1/workspaces/{workspace_id}/strings/{string_id}/details/`

2. **Filter-based approach** (alternative):
   - `/api/v1/workspaces/{workspace_id}/strings/?submission={submission_id}`
   - `/api/v1/workspaces/{workspace_id}/string-details/?string={string_id}`

### Impact

- **Developer confusion**: Two ways to access same data
- **API surface area**: More endpoints to maintain

### Recommendation

**Prefer nested routes for parent-child relationships:**

✅ **Use nested routes when:**

- Child resource doesn't exist without parent
- Child is primarily accessed via parent
- Example: Submission → Strings, String → Details

✅ **Use filters when:**

- Resource can exist independently
- Multiple ways to access are common
- Example: Strings filtered by submission (but strings can exist independently)

### Current State

```
✅ GOOD: /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/
   → Strings belong to submission

✅ GOOD: /api/v1/workspaces/{workspace_id}/strings/{id}/details/
   → Details belong to string

✅ ALSO GOOD: /api/v1/workspaces/{workspace_id}/string-details/?string={id}
   → Alternative access pattern (for filtering/searching)
```

### Action Items

- [ ] Document when to use nested routes vs filters
- [ ] Ensure both patterns work consistently
- [ ] Update documentation with examples

---

## Summary

### High Priority Issues

1. **Issue #1**: Inconsistent workspace handling (path vs query param)
2. **Issue #6**: Missing workspace validation consistency

### Medium Priority Issues

3. **Issue #2**: Naming inconsistencies
4. **Issue #3**: Inconsistent bulk operation patterns

### Low Priority Issues

5. **Issue #4**: HTTP method usage (mostly intentional)
6. **Issue #5**: Filter parameter naming
7. **Issue #7**: Error response formats
8. **Issue #8**: Nested resource patterns

### Recommended Implementation Order

1. **Phase 1** (Security & Consistency):

   - Fix workspace validation consistency (Issue #6)
   - Standardize workspace handling (Issue #1)

2. **Phase 2** (API Polish):

   - Fix naming inconsistencies (Issue #2)
   - Standardize bulk operations (Issue #3)

3. **Phase 3** (Documentation):
   - Document HTTP method exceptions (Issue #4)
   - Standardize filter parameters (Issue #5)
   - Standardize error formats (Issue #7)
   - Document nested resource patterns (Issue #8)
