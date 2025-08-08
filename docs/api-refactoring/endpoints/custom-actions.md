# Custom Actions Analysis

**Priority:** 🟡 Medium  
**Breaking Changes:** ⚠️ Some  
**Implementation:** Phase 3 (Weeks 5-6)

## Current State

The TUX Backend has **25+ custom actions** via `@action` decorators. While some are appropriate domain-specific actions, others could be converted to proper REST resources or simplified.

## String Actions Analysis

### Current String Actions (7+ actions)

| Action | Current Endpoint | Method | Analysis |
|--------|------------------|--------|----------|
| `generate` | `POST /strings/generate/` | POST | ❌ Should be resource |
| `regenerate` | `POST /strings/{id}/regenerate/` | POST | ✅ Keep (domain action) |
| `check_conflicts` | `POST /strings/check_conflicts/` | POST | ❌ Should be resource |
| `bulk_generate` | `POST /strings/bulk_generate/` | POST | ❌ Should be resource |
| `hierarchy` | `GET /strings/{id}/hierarchy/` | GET | ⚠️ Could be query param |
| `conflicts` | `GET /strings/conflicts/` | GET | ❌ Should be resource |
| `expanded` | `GET /strings/{id}/expanded/` | GET | ⚠️ Could be query param |

### String Actions - Detailed Analysis

#### 1. Generate → Convert to Resource
**Current:**
```
POST /api/v1/strings/generate/
```

**Should Change:** ✅ Yes  
**Reason:** String generation is a resource creation operation

**New Structure:**
```
POST /api/v1/generations/                    # Create string generation request
GET  /api/v1/generations/{id}/               # Get generation result
GET  /api/v1/generations/                    # List generation history
```

**Implementation:**
- Create new `GenerationViewSet` 
- Move generation logic to dedicated resource
- Maintain generation history and status

#### 2. Bulk Generate → Bulk Resource Operation  
**Current:**
```
POST /api/v1/strings/bulk_generate/
```

**Should Change:** ✅ Yes
**Reason:** Should be bulk endpoint on generation resource

**New Structure:**
```
POST /api/v1/generations/bulk/               # Bulk generation requests
GET  /api/v1/generations/bulk/{batch_id}/    # Get bulk generation status
```

#### 3. Check Conflicts → Convert to Resource
**Current:**
```
POST /api/v1/strings/check_conflicts/
```

**Should Change:** ✅ Yes
**Reason:** Conflict checking is a resource operation

**New Structure:**  
```
POST /api/v1/conflict-checks/                # Create conflict check
GET  /api/v1/conflict-checks/{id}/           # Get check results  
GET  /api/v1/strings/conflicts/              # List all conflicts (as filter)
```

#### 4. Hierarchy & Expanded → Query Parameters
**Current:**
```
GET /api/v1/strings/{id}/hierarchy/
GET /api/v1/strings/{id}/expanded/
```

**Should Change:** ⚠️ Maybe
**Reason:** Could be achieved with query parameters

**New Structure:**
```
GET /api/v1/strings/{id}/?include=hierarchy   # Get string with hierarchy
GET /api/v1/strings/{id}/?expanded=true       # Get expanded string data
```

#### 5. Regenerate → Keep as Action
**Current:**
```
POST /api/v1/strings/{id}/regenerate/
```

**Should Change:** ❌ No
**Reason:** Domain-specific action that modifies existing resource

**Keep As-Is:** This is a proper domain action for modifying existing strings

## Rule Actions Analysis

### Current Rule Actions (8+ actions)

| Action | Current Endpoint | Method | Analysis |
|--------|------------------|--------|----------|
| `preview` | `POST /rules/{id}/preview/` | POST | ❌ Should be resource |
| `validate_configuration` | `GET /rules/{id}/validate_configuration/` | GET | ⚠️ Could be query param |
| `set_default` | `POST /rules/{id}/set_default/` | POST | ✅ Keep (domain action) |
| `defaults` | `GET /rules/defaults/` | GET | ⚠️ Could be filter |
| `required_dimensions` | `GET /rules/{id}/required_dimensions/` | GET | ⚠️ Could be query param |
| `active` | `GET /rules/active/` | GET | ⚠️ Could be filter |
| `validate_order` | `POST /rules/validate_order/` | POST | ❌ Should be resource |
| `clone` | `POST /rules/{id}/clone/` | POST | ✅ Keep (domain action) |

### Rule Actions - Detailed Analysis

#### 1. Preview → Convert to Resource
**Current:**
```
POST /api/v1/rules/{id}/preview/
```

**Should Change:** ✅ Yes
**Reason:** Rule preview is a resource generation operation

**New Structure:**
```
POST /api/v1/rule-previews/                  # Create rule preview
GET  /api/v1/rule-previews/{id}/             # Get preview result
```

#### 2. Filters → Query Parameters  
**Current:**
```
GET /api/v1/rules/defaults/
GET /api/v1/rules/active/
```

**Should Change:** ✅ Yes
**Reason:** These are just filtered views of rules

**New Structure:**
```
GET /api/v1/rules/?is_default=true           # Get default rules
GET /api/v1/rules/?status=active             # Get active rules
```

#### 3. Domain Actions → Keep
**Current:**
```
POST /api/v1/rules/{id}/set_default/         # Set rule as default
POST /api/v1/rules/{id}/clone/               # Clone rule with details
```

**Should Change:** ❌ No  
**Reason:** These are proper domain-specific actions

## Propagation Actions Analysis

### Current Propagation Actions (4+ actions)

| Action | Current Endpoint | Method | Analysis |
|--------|------------------|--------|----------|
| `errors` | `GET /propagation-jobs/{id}/errors/` | GET | ⚠️ Should be nested resource |
| `summary` | `GET /propagation-jobs/summary/` | GET | ⚠️ Could be query param |
| `mark_resolved` | `POST /propagation-errors/{id}/mark_resolved/` | POST | ✅ Keep (state change) |
| `retry` | `POST /propagation-errors/{id}/retry/` | POST | ✅ Keep (state change) |

### Propagation Actions - Detailed Analysis

#### 1. Errors → Nested Resource
**Current:**
```
GET /api/v1/propagation-jobs/{id}/errors/
```

**Should Change:** ✅ Yes
**Reason:** Errors belong to jobs - should be nested

**New Structure:**
```
GET /api/v1/propagation-jobs/{job_id}/errors/       # List job's errors
GET /api/v1/propagation-jobs/{job_id}/errors/{id}/  # Get specific error
```

#### 2. Summary → Query Parameter
**Current:**
```
GET /api/v1/propagation-jobs/summary/
```

**Should Change:** ✅ Yes  
**Reason:** Summary is just aggregated view

**New Structure:**
```
GET /api/v1/propagation-jobs/?summary=true          # Get summary statistics
```

## Recommendations

### ✅ Actions to Convert to Resources

| Current Action | New Resource | Reason |
|----------------|--------------|---------|
| `POST /strings/generate/` | `POST /generations/` | Resource creation |
| `POST /strings/bulk_generate/` | `POST /generations/bulk/` | Bulk operations |
| `POST /strings/check_conflicts/` | `POST /conflict-checks/` | Resource creation |
| `POST /rules/{id}/preview/` | `POST /rule-previews/` | Resource creation |
| `POST /rules/validate_order/` | `POST /validations/` | Resource creation |

### ✅ Actions to Convert to Query Parameters

| Current Action | New Query Param | Reason |
|----------------|-----------------|---------|
| `GET /rules/defaults/` | `GET /rules/?is_default=true` | Simple filter |
| `GET /rules/active/` | `GET /rules/?status=active` | Simple filter |  
| `GET /strings/conflicts/` | `GET /strings/?has_conflicts=true` | Simple filter |
| `GET /strings/{id}/hierarchy/` | `GET /strings/{id}/?include=hierarchy` | Data inclusion |
| `GET /strings/{id}/expanded/` | `GET /strings/{id}/?expanded=true` | Data inclusion |

### ✅ Actions to Keep (Domain-Specific)

| Action | Reason to Keep |
|--------|---------------|
| `POST /strings/{id}/regenerate/` | Modifies existing resource state |
| `POST /rules/{id}/set_default/` | Domain-specific state change |
| `POST /rules/{id}/clone/` | Complex domain operation |
| `POST /propagation-errors/{id}/mark_resolved/` | State transition |
| `POST /propagation-errors/{id}/retry/` | State transition |

## Implementation Plan

### Week 5: Create New Resources

1. **Generation Resource**
```python
class GenerationViewSet(ModelViewSet):
    """Handle string generation as proper resource"""
    
    def create(self, request):
        # Move logic from strings/generate action
        pass
```

2. **Conflict Check Resource**  
```python
class ConflictCheckViewSet(ModelViewSet):
    """Handle conflict checking as proper resource"""
```

3. **Rule Preview Resource**
```python  
class RulePreviewViewSet(ModelViewSet):
    """Handle rule previews as proper resource"""
```

### Week 6: Convert to Query Parameters

1. **Update ViewSets with Filtering**
```python
class RuleViewSet(ModelViewSet):
    filterset_fields = ['status', 'is_default', 'platform']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Handle special query params
        if self.request.query_params.get('summary'):
            return self.get_summary_queryset()
            
        return queryset
```

2. **Update Serializers for Inclusion**
```python
class StringSerializer(ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if self.context['request'].query_params.get('include') == 'hierarchy':
            data['hierarchy'] = self.get_hierarchy_data(instance)
            
        return data
```

## Breaking Change Analysis

### Low Impact (Query Param Changes)
- Old action endpoints can redirect to new query param versions
- Easy to maintain backward compatibility

### Medium Impact (New Resources)
- Generation, conflict-check, and preview endpoints change significantly
- Requires client updates for these specific operations

### No Impact (Keep Actions)
- Domain-specific actions remain unchanged
- No breaking changes for core domain operations

## Success Metrics

| Metric | Before | Target | Improvement |
|--------|--------|--------|-------------|
| Custom actions | 25+ | 15 | -40% |
| Resource endpoints | 8 | 12 | +50% |
| REST compliance | 60% | 90% | +30% |
| Action clarity | Low | High | Qualitative |

## Testing Strategy

### New Resource Tests
- [ ] Generation resource CRUD operations
- [ ] Conflict check resource functionality  
- [ ] Rule preview resource operations
- [ ] Bulk operation handling

### Query Parameter Tests
- [ ] Filtering works correctly
- [ ] Data inclusion parameters work
- [ ] Backward compatibility with actions

### Domain Action Tests  
- [ ] Existing domain actions unchanged
- [ ] State transitions work correctly
- [ ] Complex operations preserved

---

**Next:** Review [phase-1-auth.md](../migration/phase-1-auth.md) for implementation planning.