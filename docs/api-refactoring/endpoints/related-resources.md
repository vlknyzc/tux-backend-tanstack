# Related Resources Naming Analysis

**Priority:** 🔴 High  
**Breaking Changes:** ⚠️ Yes  
**Implementation:** Phase 2 (Weeks 3-4)

## Current State Problems

The API has **inconsistent naming patterns** for related resources, causing confusion about resource relationships and REST conventions.

## Resource Naming Issues

### 1. Dimension Resources

| Current Endpoint | Issue | Status |
|------------------|-------|--------|
| `/api/v1/dimensions/` | ✅ Good - main resource | Keep |
| `/api/v1/dimension-values/` | ❌ Inconsistent naming | **Fix** |

**Problem**: Should be nested under dimensions, not separate resource
- Unclear relationship between dimensions and their values
- Violates REST nested resource convention

### 2. Rule Resources

| Current Endpoint | Issue | Status |
|------------------|-------|--------|
| `/api/v1/rules/` | ✅ Good - main resource | Keep |
| `/api/v1/rule-details/` | ❌ Inconsistent naming | **Fix** |
| `/api/v1/rule-nested/` | ❌ Unclear purpose vs `/rules/` | **Merge** |

**Problems**: 
- `rule-details` should be nested under `rules`
- `rule-nested` functionality should be merged into main `rules` resource

### 3. String Resources

| Current Endpoint | Issue | Status |
|------------------|-------|--------|
| `/api/v1/strings/` | ✅ Good - main resource | Keep |
| `/api/v1/string-details/` | ❌ Inconsistent naming | **Fix** |
| `/api/v1/enhanced-string-details/` | ❌ Redundant with string-details | **Merge** |

**Problems**:
- Two separate endpoints for string details create confusion  
- `enhanced-string-details` vs `string-details` - unclear difference
- Should be nested under strings resource

### 4. Submission Resources

| Current Endpoint | Issue | Status |
|------------------|-------|--------|
| `/api/v1/submissions/` | ✅ Good - main resource | Keep |
| `/api/v1/nested-submissions/` | ❌ Unclear difference | **Merge** |

**Problem**: Unclear what makes a submission "nested" vs regular

## Recommendations

### ✅ Target State: Consistent Nested Resources

| Current Endpoint | → | New Endpoint | Change Type |
|------------------|---|--------------|-------------|
| `/api/v1/dimension-values/` | → | `/api/v1/dimensions/{id}/values/` | **Move to nested** |
| `/api/v1/rule-details/` | → | `/api/v1/rules/{id}/details/` | **Move to nested** |
| `/api/v1/string-details/` | → | `/api/v1/strings/{id}/details/` | **Move to nested** |
| `/api/v1/enhanced-string-details/` | → | `/api/v1/strings/{id}/details/` | **Merge functionality** |
| `/api/v1/rule-nested/` | → | `/api/v1/rules/` | **Merge functionality** |
| `/api/v1/nested-submissions/` | → | `/api/v1/submissions/` | **Merge functionality** |

## Detailed Analysis

### 1. Dimension Values → Nested Resource

**Current:**
```
GET    /api/v1/dimension-values/          # List all dimension values
POST   /api/v1/dimension-values/          # Create dimension value
GET    /api/v1/dimension-values/{id}/     # Get specific value
PUT    /api/v1/dimension-values/{id}/     # Update specific value
DELETE /api/v1/dimension-values/{id}/     # Delete specific value
```

**Should Change:** ✅ Yes
**Reason:** Values belong to dimensions - should be nested resource

**New Structure:**
```
GET    /api/v1/dimensions/{dimension_id}/values/          # List dimension's values
POST   /api/v1/dimensions/{dimension_id}/values/          # Create value for dimension
GET    /api/v1/dimensions/{dimension_id}/values/{id}/     # Get specific value
PUT    /api/v1/dimensions/{dimension_id}/values/{id}/     # Update specific value  
DELETE /api/v1/dimensions/{dimension_id}/values/{id}/     # Delete specific value

# Bulk operations
POST   /api/v1/dimensions/{dimension_id}/values/bulk/     # Bulk create values
```

**Implementation:**
- Update `DimensionValueViewSet` to be nested under dimensions
- Add dimension_id filtering automatically
- Maintain bulk operations under nested structure

### 2. Rule Details → Nested Resource

**Current:**
```
GET    /api/v1/rule-details/          # List all rule details
POST   /api/v1/rule-details/          # Create rule detail
GET    /api/v1/rule-details/{id}/     # Get specific rule detail
PUT    /api/v1/rule-details/{id}/     # Update rule detail
DELETE /api/v1/rule-details/{id}/     # Delete rule detail
```

**Should Change:** ✅ Yes  
**Reason:** Rule details belong to rules - should be nested

**New Structure:**
```
GET    /api/v1/rules/{rule_id}/details/          # List rule's details
POST   /api/v1/rules/{rule_id}/details/          # Create detail for rule
GET    /api/v1/rules/{rule_id}/details/{id}/     # Get specific detail
PUT    /api/v1/rules/{rule_id}/details/{id}/     # Update specific detail
DELETE /api/v1/rules/{rule_id}/details/{id}/     # Delete specific detail
```

### 3. String Details → Merged Nested Resource

**Current:**
```
# Two separate endpoints for similar functionality
/api/v1/string-details/               # Basic string details
/api/v1/enhanced-string-details/      # Enhanced string details with extra features
```

**Should Change:** ✅ Yes
**Reason:** Redundant endpoints for same resource type

**New Structure:**
```
GET    /api/v1/strings/{string_id}/details/          # Get string details (merged functionality)
POST   /api/v1/strings/{string_id}/details/          # Create string detail
PUT    /api/v1/strings/{string_id}/details/{id}/     # Update string detail
DELETE /api/v1/strings/{string_id}/details/{id}/     # Delete string detail

# Enhanced operations as query params or actions
GET    /api/v1/strings/{string_id}/details/?enhanced=true    # Enhanced view
POST   /api/v1/strings/{string_id}/details/batch-update/    # Batch operations
```

### 4. Rule Nested → Merge Functionality

**Current:**
```
/api/v1/rules/                        # Main rules endpoint
/api/v1/rule-nested/                  # Unclear additional functionality
```

**Should Change:** ✅ Yes
**Reason:** Functionality should be merged into main rules resource

**New Structure:**
- Merge all `rule-nested` functionality into `/api/v1/rules/`
- Use query parameters for different views: `/api/v1/rules/?include=nested`
- Use actions for special operations: `/api/v1/rules/{id}/clone/`

## Implementation Plan

### Week 3: Create New Nested Endpoints

1. **Update ViewSets for Nested Resources**
```python
# master_data/views/dimension_views.py
class DimensionValueViewSet(NestedViewSetMixin, ModelViewSet):
    """Now properly nested under dimensions"""
    parent_lookup_kwargs = {'dimension_pk': 'dimension__pk'}
```

2. **Update URL Patterns**
```python
# master_data/urls.py
router.register(
    r'dimensions/(?P<dimension_pk>[^/.]+)/values', 
    DimensionValueViewSet, 
    basename='dimension-values'
)
```

3. **Add Nested Resource Support**
- Use `drf-nested-routers` library
- Update serializers for nested context
- Maintain filtering by parent resource

### Week 4: Merge Redundant Endpoints  

1. **Merge Enhanced String Details**
```python
class StringDetailViewSet(ModelViewSet):
    """Merged functionality from both string-details and enhanced-string-details"""
    
    def get_queryset(self):
        if self.request.query_params.get('enhanced'):
            return self.enhanced_queryset()
        return self.standard_queryset()
```

2. **Merge Rule Nested into Rules**
- Move all `rule-nested` functionality to `RuleViewSet`
- Add query parameters for nested views
- Convert unique actions to proper actions on main resource

## Breaking Change Analysis

### High Impact Changes
- `/api/v1/dimension-values/` → `/api/v1/dimensions/{id}/values/`
- `/api/v1/rule-details/` → `/api/v1/rules/{id}/details/`  
- `/api/v1/string-details/` → `/api/v1/strings/{id}/details/`

### Medium Impact Changes
- Merge `/api/v1/enhanced-string-details/` into `/api/v1/strings/{id}/details/`
- Remove `/api/v1/rule-nested/` and `/api/v1/nested-submissions/`

### Migration Support
```python
# Add backward compatibility decorators
@deprecated_endpoint(
    use_instead="/api/v1/dimensions/{dimension_id}/values/",
    removal_date="2025-12-01"
)
def old_dimension_values_view():
    # Redirect to new nested endpoint
```

## Testing Strategy

### API Structure Tests
- [ ] Nested resources properly filter by parent
- [ ] Parent resource existence validation  
- [ ] Nested bulk operations work correctly
- [ ] Error handling for invalid parent IDs

### Migration Tests  
- [ ] Old endpoints redirect to new ones
- [ ] Data integrity maintained during transition
- [ ] Client applications still function with deprecation warnings

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| Resource naming consistency | 40% | 100% |
| Developer confusion | High | None |
| REST convention compliance | 60% | 95% |
| API endpoint count | 65+ | 50- |

---

**Next:** Review [custom-actions.md](custom-actions.md) for action rationalization.