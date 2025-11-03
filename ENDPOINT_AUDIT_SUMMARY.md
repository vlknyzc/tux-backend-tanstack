# API Endpoint Workspace Filtering Audit Summary

## Quick Reference: Endpoint Patterns

### ✅ Pattern 1: Workspace ID in URL Path (RECOMMENDED)

| Endpoint              | URL Pattern                                                                        | ViewSet                     | Status      |
| --------------------- | ---------------------------------------------------------------------------------- | --------------------------- | ----------- |
| Strings               | `/api/v1/workspaces/{workspace_id}/strings/`                                       | `StringViewSet`             | ✅ Standard |
| String Details        | `/api/v1/workspaces/{workspace_id}/string-details/`                                | `StringDetailViewSet`       | ✅ Standard |
| Nested String Details | `/api/v1/workspaces/{workspace_id}/strings/{id}/details/`                          | `StringDetailNestedViewSet` | ✅ Standard |
| Multi-Operations      | `/api/v1/workspaces/{workspace_id}/multi-operations/`                              | `MultiOperationsViewSet`    | ✅ Standard |
| Projects              | `/api/v1/workspaces/{workspace_id}/projects/`                                      | `ProjectViewSet`            | ✅ Standard |
| Project Strings       | `/api/v1/workspaces/{workspace_id}/projects/{id}/platforms/{platform_id}/strings/` | Various                     | ✅ Standard |

**Characteristics:**

- Uses `WorkspaceValidationMixin`
- Workspace ID from `kwargs['workspace_id']`
- Validated in `dispatch()` method
- **Security: Strong** ✅

---

### ⚠️ Pattern 2: Query Parameter (`?workspace=`)

| Endpoint              | URL Pattern                                    | ViewSet                      | Status             |
| --------------------- | ---------------------------------------------- | ---------------------------- | ------------------ |
| Dimensions            | `/api/v1/dimensions/?workspace=123`            | `DimensionViewSet`           | ⚠️ Needs Migration |
| Dimension Values      | `/api/v1/dimension-values/?workspace=123`      | `DimensionValueViewSet`      | ⚠️ Needs Migration |
| Dimension Constraints | `/api/v1/dimension-constraints/?workspace=123` | `DimensionConstraintViewSet` | ⚠️ Needs Migration |
| Rules                 | `/api/v1/rules/?workspace=123`                 | `RuleViewSet`                | ⚠️ Needs Migration |
| Rule Details          | `/api/v1/rule-details/?workspace=123`          | `RuleDetailViewSet`          | ⚠️ Needs Migration |
| Rule Nested           | `/api/v1/rule-nested/?workspace=123`           | `RuleNestedViewSet`          | ⚠️ Needs Migration |

**Characteristics:**

- Uses `WorkspaceMixin`
- Workspace ID from `request.query_params.get('workspace')`
- Validated in `get_queryset()` method
- Falls back to user's accessible workspaces
- **Security: Medium** ⚠️

---

### ⚠️⚠️ Pattern 3: Request Attribute (Unclear Source)

| Endpoint                | URL Pattern                        | ViewSet                       | Status         |
| ----------------------- | ---------------------------------- | ----------------------------- | -------------- |
| Propagation Jobs        | `/api/v1/propagation-jobs/`        | `PropagationJobViewSet`       | ⚠️⚠️ Needs Fix |
| Propagation Errors      | `/api/v1/propagation-errors/`      | `PropagationErrorViewSet`     | ⚠️⚠️ Needs Fix |
| Enhanced String Details | `/api/v1/enhanced-string-details/` | `EnhancedStringDetailViewSet` | ⚠️⚠️ Needs Fix |
| Propagation Settings    | `/api/v1/propagation-settings/`    | `PropagationSettingsViewSet`  | ⚠️⚠️ Needs Fix |

**Characteristics:**

- Uses `getattr(request, 'workspace', None)`
- Middleware sets workspace (but currently sets to `None`!)
- Returns empty queryset if no workspace
- **Security: Low** ⚠️⚠️

---

### ✅ Pattern 4: Global Resources (No Workspace Filtering)

| Endpoint   | URL Pattern           | ViewSet            | Status     |
| ---------- | --------------------- | ------------------ | ---------- |
| Workspaces | `/api/v1/workspaces/` | `WorkspaceViewSet` | ✅ Correct |
| Platforms  | `/api/v1/platforms/`  | `PlatformViewSet`  | ✅ Correct |
| Fields     | `/api/v1/fields/`     | `FieldViewSet`     | ✅ Correct |

**Characteristics:**

- Intentionally global resources
- WorkspaceViewSet filters by user access (not workspace ID)
- Platforms and Fields are global entities
- **Security: Appropriate** ✅

---

### ⚠️⚠️ Pattern 5: Mixed (Query Param + Request Body)

| Endpoint                     | URL Pattern                                                                   | ViewSet                               | Status         |
| ---------------------------- | ----------------------------------------------------------------------------- | ------------------------------------- | -------------- |
| Dimensions Bulk Create       | `/api/v1/dimensions/bulk_create/?workspace=123` OR `{"workspace": 123}`       | `DimensionViewSet.bulk_create()`      | ⚠️⚠️ Needs Fix |
| Dimension Values Bulk Create | `/api/v1/dimension-values/bulk_create/?workspace=123` OR `{"workspace": 123}` | `DimensionValueViewSet.bulk_create()` | ⚠️⚠️ Needs Fix |

**Characteristics:**

- Accepts workspace in query param OR request body
- Confusing fallback logic
- **Security: Low** ⚠️⚠️

---

## Inconsistency Matrix

| Aspect                | URL Path Pattern    | Query Param Pattern    | Request Attribute Pattern |
| --------------------- | ------------------- | ---------------------- | ------------------------- |
| **Security**          | ✅ Strong           | ⚠️ Medium              | ⚠️⚠️ Low                  |
| **Clarity**           | ✅ High             | ⚠️ Medium              | ⚠️ Low                    |
| **Validation Timing** | ✅ Early (dispatch) | ⚠️ Late (get_queryset) | ⚠️⚠️ Unclear              |
| **Error Handling**    | ✅ Consistent       | ⚠️ Mixed               | ⚠️⚠️ Silent failures      |
| **Documentation**     | ✅ Easy             | ⚠️ Medium              | ⚠️ Hard                   |
| **RESTful**           | ✅ Yes              | ⚠️ Less so             | ⚠️ No                     |

---

## Migration Priority

### 🔴 High Priority (Security-Sensitive)

1. Rules endpoints (`/api/v1/rules/`)
2. Rule details (`/api/v1/rule-details/`)
3. Propagation endpoints (security risk with unclear workspace source)

### 🟡 Medium Priority

4. Dimensions (`/api/v1/dimensions/`)
5. Dimension values (`/api/v1/dimension-values/`)
6. Dimension constraints (`/api/v1/dimension-constraints/`)

### 🟢 Low Priority (Less Critical)

7. Bulk create endpoints (fix mixed pattern)

---

## Recommended Standard

**All workspace-scoped resources should use:**

```
/api/v1/workspaces/{workspace_id}/resource-name/
```

**Implementation:**

- Use `WorkspaceValidationMixin`
- Extract workspace_id from `kwargs['workspace_id']`
- Validate in `dispatch()` method
- Return 403 for unauthorized access
- Return 404 for non-existent workspace

---

## Statistics

- **Total Endpoints Audited**: ~50+
- **Using URL Path Pattern**: 15 endpoints ✅
- **Using Query Param Pattern**: 12 endpoints ⚠️
- **Using Request Attribute**: 4 endpoints ⚠️⚠️
- **Mixed Patterns**: 2 endpoints ⚠️⚠️
- **Global Resources**: 3 endpoints ✅

**Consistency Score**: ~47% (15/32 workspace-scoped endpoints follow standard)

---

For detailed analysis, see: `.github_issues/endpoint_workspace_inconsistencies.md`
