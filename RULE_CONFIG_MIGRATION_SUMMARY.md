# Rule Configuration Endpoints Migration Summary

## ✅ Completed Migration

All rule configuration endpoints have been migrated to include `workspace_id` in the URL path.

## Migrated Endpoints

### 1. Rule Configuration ✅

- **Old**: `/api/v1/rules/{rule_id}/configuration/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/{rule_id}/configuration/`
- **View**: `RuleConfigurationView`
- **Method**: GET

### 2. Lightweight Rule View ✅

- **Old**: `/api/v1/rules/{rule_id}/lightweight/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/{rule_id}/lightweight/`
- **View**: `LightweightRuleView`
- **Method**: GET

### 3. Field-Specific Rule View ✅

- **Old**: `/api/v1/rules/{rule_id}/fields/{field_id}/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/{rule_id}/fields/{field_id}/`
- **View**: `FieldSpecificRuleView`
- **Method**: GET

### 4. Rule Validation View ✅

- **Old**: `/api/v1/rules/{rule_id}/validation/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/{rule_id}/validation/`
- **View**: `RuleValidationView`
- **Method**: GET

### 5. Generation Preview ✅

- **Old**: `/api/v1/rules/generation-preview/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/generation-preview/`
- **View**: `GenerationPreviewView`
- **Method**: POST

### 6. Cache Invalidation ✅

- **Old**: `/api/v1/rules/cache/invalidate/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/cache/invalidate/`
- **View**: `CacheManagementView`
- **Method**: POST

### 7. Performance Metrics ✅

- **Old**: `/api/v1/rules/{rule_id}/metrics/`
- **New**: `/api/v1/workspaces/{workspace_id}/rules/{rule_id}/metrics/`
- **View**: `CacheManagementView`
- **Method**: GET

## Implementation Details

### Created WorkspaceScopedRuleViewMixin

A new mixin was created to handle workspace validation for APIView classes:

```python
class WorkspaceScopedRuleViewMixin:
    """Mixin for workspace-scoped rule views that validates workspace access."""

    def validate_workspace_and_rule(self, request, rule_id, workspace_id=None):
        """
        Validate workspace access and ensure rule belongs to workspace.
        Returns (rule, workspace_id) tuple.
        """
        # Validates workspace access
        # Ensures rule belongs to workspace
        # Returns rule and workspace_id
```

### Changes Made

1. **URL Patterns** (`master_data/urls.py`):

   - All rule configuration endpoints now include `workspace_id` in path
   - Pattern: `workspaces/<int:workspace_id>/rules/...`

2. **Views** (`master_data/views/rule_configuration_views.py`):

   - All views now inherit from `WorkspaceScopedRuleViewMixin`
   - Updated method signatures to accept `workspace_id` parameter
   - Updated validation logic to use `validate_workspace_and_rule()` helper
   - Removed old `_validate_rule_access()` method from `RuleConfigurationView`

3. **Error Handling**:
   - Proper handling of `Http404` exceptions
   - Consistent error responses across all endpoints

## Security Improvements

1. **Early Validation**: Workspace access is validated before rule lookup
2. **Rule Ownership Check**: Ensures rule belongs to the specified workspace
3. **Consistent Access Control**: All endpoints use the same validation logic

## Breaking Changes

⚠️ **This is a breaking change!** All client applications need to update:

**Before:**

```javascript
GET /api/v1/rules/123/configuration/
GET /api/v1/rules/123/lightweight/
POST /api/v1/rules/generation-preview/
```

**After:**

```javascript
GET /api/v1/workspaces/456/rules/123/configuration/
GET /api/v1/workspaces/456/rules/123/lightweight/
POST /api/v1/workspaces/456/rules/generation-preview/
```

## Example Usage

### Get Rule Configuration

```bash
GET /api/v1/workspaces/123/rules/456/configuration/
```

### Get Lightweight Rule Data

```bash
GET /api/v1/workspaces/123/rules/456/lightweight/
```

### Generate Preview

```bash
POST /api/v1/workspaces/123/rules/generation-preview/
{
  "rule": 456,
  "field": 789,
  "sample_values": {...}
}
```

### Invalidate Cache

```bash
POST /api/v1/workspaces/123/rules/cache/invalidate/
{
  "rule_ids": [456, 789]
}
```

## Files Modified

- `master_data/urls.py` - Updated URL patterns
- `master_data/views/rule_configuration_views.py` - Updated all views

## Testing Checklist

- [ ] Test workspace access validation (403 for unauthorized)
- [ ] Test workspace not found (404)
- [ ] Test rule not found (404)
- [ ] Test rule belongs to different workspace (403)
- [ ] Test superuser access to any workspace
- [ ] Test regular user access to their workspace
- [ ] Verify all endpoints return correct workspace_id in responses
- [ ] Check OpenAPI schema generation includes workspace_id parameter

## Related Migration

This completes the workspace URL pattern migration. See `WORKSPACE_MIGRATION_SUMMARY.md` for the full migration details.
