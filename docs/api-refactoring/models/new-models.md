# New Model Proposals

**Priority:** 🟢 Low  
**Breaking Changes:** ❌ No (additive only)  
**Implementation:** Future phases - Beyond initial 8-week refactoring

## Overview

Based on the API audit analysis, several new models could improve the system's architecture and support better separation of concerns. These are **optional enhancements** that go beyond the core refactoring scope.

## Proposed New Models

### 1. Generation Model
**Purpose:** Replace custom actions with proper resource tracking

**Current Problem:**
- String generation is handled via custom actions (`POST /strings/generate/`)
- No history or tracking of generation requests
- Difficult to debug failed generations
- No batch generation management

**Proposed Model:**
```python
class GenerationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'

class Generation(TimeStampModel, WorkspaceMixin):
    """
    Tracks string generation requests and their status.
    
    Replaces custom action endpoints with proper resource management.
    """
    
    # Request details
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="generations",
        help_text="Rule used for generation"
    )
    submission = models.ForeignKey(
        "master_data.Submission", 
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Submission that triggered generation"
    )
    
    # Generation parameters
    dimension_values = models.JSONField(
        help_text="Dimension values used for generation"
    )
    field_filter = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific fields to generate (empty = all fields)"
    )
    
    # Status and results
    status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        help_text="Current generation status"
    )
    result_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of strings generated"
    )
    error_message = models.TextField(
        null=True, blank=True,
        help_text="Error message if generation failed"
    )
    
    # Audit
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_generations'
    )
    
    class Meta:
        verbose_name = "Generation"
        verbose_name_plural = "Generations" 
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['rule', 'status']),
        ]
```

**API Benefits:**
```python
# Instead of: POST /strings/generate/
# Use: POST /generations/
{
    "rule": 1,
    "dimension_values": {"environment": "prod", "project": "web-app"},
    "field_filter": [1, 2]  # Optional: specific fields only
}

# Track generation progress: GET /generations/123/
{
    "id": 123,
    "status": "in_progress",
    "result_count": 5,
    "created_at": "2025-01-01T10:00:00Z"
}

# List generation history: GET /generations/
```

### 2. ConflictCheck Model
**Purpose:** Replace conflict checking actions with proper resource

**Current Problem:**
- Conflict checking via custom action (`POST /strings/check_conflicts/`)
- No tracking of conflict check history
- Results not persisted for analysis

**Proposed Model:**
```python
class ConflictSeverity(models.TextChoices):
    INFO = 'info', 'Info'
    WARNING = 'warning', 'Warning'  
    ERROR = 'error', 'Error'
    CRITICAL = 'critical', 'Critical'

class ConflictCheck(TimeStampModel, WorkspaceMixin):
    """
    Tracks naming conflict checks and their results.
    """
    
    # Check parameters
    proposed_strings = models.JSONField(
        help_text="Proposed string values to check for conflicts"
    )
    scope = models.CharField(
        max_length=50,
        choices=[
            ('workspace', 'Workspace'),
            ('platform', 'Platform'),
            ('rule', 'Rule'),
        ],
        default='workspace',
        help_text="Scope of conflict checking"
    )
    
    # Results
    conflicts_found = models.PositiveIntegerField(
        default=0,
        help_text="Number of conflicts detected"
    )
    max_severity = models.CharField(
        max_length=20,
        choices=ConflictSeverity.choices,
        null=True, blank=True,
        help_text="Highest severity level found"
    )
    
    # Audit
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        verbose_name = "Conflict Check"
        verbose_name_plural = "Conflict Checks"
        ordering = ['-created_at']

class ConflictResult(TimeStampModel):
    """
    Individual conflict results within a check.
    """
    check = models.ForeignKey(
        ConflictCheck,
        on_delete=models.CASCADE,
        related_name='results'
    )
    proposed_value = models.CharField(max_length=255)
    conflicting_string = models.ForeignKey(
        "master_data.String",
        on_delete=models.CASCADE,
        null=True
    )
    severity = models.CharField(
        max_length=20,
        choices=ConflictSeverity.choices
    )
    message = models.TextField()
    
    class Meta:
        ordering = ['check', '-severity']
```

### 3. RulePreview Model
**Purpose:** Replace rule preview actions with tracked resources

**Current Problem:**
- Rule preview via custom action (`POST /rules/{id}/preview/`)
- No persistence of preview results
- Hard to compare different rule configurations

**Proposed Model:**
```python
class RulePreview(TimeStampModel, WorkspaceMixin):
    """
    Tracks rule preview generations for testing and validation.
    """
    
    # Preview configuration
    rule = models.ForeignKey(
        "master_data.Rule",
        on_delete=models.CASCADE,
        related_name="previews"
    )
    test_data = models.JSONField(
        help_text="Sample dimension values used for preview"
    )
    
    # Results  
    generated_examples = models.JSONField(
        help_text="Examples of strings that would be generated"
    )
    validation_results = models.JSONField(
        default=dict,
        help_text="Validation messages and warnings"
    )
    
    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        verbose_name = "Rule Preview"
        verbose_name_plural = "Rule Previews"
        ordering = ['-created_at']
```

### 4. UserPreferences Model
**Purpose:** Store user-specific settings and preferences

**Current Gap:**
- No user preference storage
- UI settings not persisted
- Workspace-specific user settings mixed with general preferences

**Proposed Model:**
```python
class UserPreferences(TimeStampModel):
    """
    Stores user-specific preferences and settings.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    
    # UI Preferences
    ui_theme = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='light'
    )
    default_workspace = models.ForeignKey(
        "master_data.Workspace",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="User's preferred default workspace"
    )
    
    # API Preferences
    default_page_size = models.PositiveSmallIntegerField(
        default=25,
        help_text="Preferred pagination size"
    )
    preferred_date_format = models.CharField(
        max_length=20,
        default='iso',
        choices=[
            ('iso', 'ISO 8601'),
            ('us', 'US Format'),
            ('eu', 'European Format'),
        ]
    )
    
    # Feature Flags (user-specific)
    enabled_features = models.JSONField(
        default=list,
        help_text="List of enabled experimental features"
    )
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    propagation_notifications = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"
```

### 5. APIUsageLog Model (Optional)
**Purpose:** Track API usage for analytics and billing

**Use Case:**
- API usage monitoring
- Rate limiting data
- Performance analysis
- Billing calculations (if needed)

**Proposed Model:**
```python
class APIUsageLog(models.Model):
    """
    Tracks API usage for monitoring and analytics.
    
    Note: High-volume table - consider partitioning or rotation.
    """
    
    # Request details
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    workspace = models.ForeignKey(
        "master_data.Workspace",
        on_delete=models.SET_NULL,
        null=True
    )
    
    # API call information
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    response_status = models.PositiveSmallIntegerField()
    response_time_ms = models.PositiveIntegerField()
    
    # Usage metrics
    request_size_bytes = models.PositiveIntegerField(default=0)
    response_size_bytes = models.PositiveIntegerField(default=0)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)  # For efficient date-based queries
    
    class Meta:
        verbose_name = "API Usage Log"
        verbose_name_plural = "API Usage Logs"
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['workspace', 'date']), 
            models.Index(fields=['endpoint', 'date']),
            models.Index(fields=['date']),  # For cleanup/aggregation
        ]
        # Consider partitioning by date for large datasets
```

## Implementation Priority

### Phase 1 (Immediate - Week 8)
**High Value, Low Complexity:**
- ✅ **UserPreferences** - Improves UX immediately
- ⚠️ **Generation** - Only if custom action conversion is prioritized

### Phase 2 (Post-Refactoring - Month 2-3)  
**Medium Value, Medium Complexity:**
- ⚠️ **ConflictCheck** - Better conflict management
- ⚠️ **RulePreview** - Enhanced rule testing

### Phase 3 (Future Enhancement - Month 6+)
**Low Priority, High Maintenance:**
- ⚠️ **APIUsageLog** - Only if monitoring/billing needed

## Migration Strategy

### New Models (Non-Breaking)
All proposed models are **additive** and don't break existing functionality:

```python
# New migrations only add tables, don't modify existing ones
class Migration(migrations.Migration):
    operations = [
        migrations.CreateModel(
            name='UserPreferences',
            fields=[...],
        ),
        migrations.CreateModel(
            name='Generation', 
            fields=[...],
        ),
        # etc.
    ]
```

### Gradual Endpoint Migration
```python
# Phase 1: Add new endpoints alongside old ones
POST /api/v1/generations/              # NEW
POST /api/v1/strings/generate/         # Keep temporarily

# Phase 2: Deprecate old endpoints  
POST /api/v1/strings/generate/         # Add deprecation warnings

# Phase 3: Remove old endpoints
# Remove old custom actions after client migration
```

## API Benefits

### Before (Custom Actions)
```python
# Scattered functionality across different action endpoints
POST /strings/generate/
POST /strings/check_conflicts/
POST /rules/123/preview/
```

### After (Proper Resources)
```python
# Consistent REST resources
POST /generations/           # Create generation request
GET  /generations/123/       # Check generation status
GET  /generations/           # List generation history

POST /conflict-checks/       # Create conflict check
GET  /conflict-checks/123/   # Get check results

POST /rule-previews/         # Create rule preview
GET  /rule-previews/123/     # Get preview results
```

## Database Considerations

### Storage Impact
- **UserPreferences**: Low impact (1 row per user)
- **Generation**: Medium impact (depends on usage frequency)
- **ConflictCheck**: Medium impact (periodic checks)
- **RulePreview**: Low impact (infrequent usage)
- **APIUsageLog**: High impact (requires data retention policy)

### Performance Considerations
- Add appropriate indexes for common queries
- Consider partitioning for high-volume tables (APIUsageLog)
- Implement cleanup policies for transient data

## Success Metrics

### Functionality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Custom action reduction | 25+ → 15 | Endpoint count |
| Resource consistency | 90% | REST compliance score |
| User experience | +20% | User preference adoption |
| API discoverability | +30% | Developer feedback |

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time | No degradation | API monitoring |
| Storage efficiency | <5% increase | Database size |
| Code maintainability | +15% | Lines of code, complexity |

## Implementation Guidelines

### Development Order
1. **Start with UserPreferences** - High value, low risk
2. **Add Generation model** - If custom action conversion prioritized  
3. **Evaluate usage patterns** - Before adding other models
4. **Monitor performance impact** - After each model addition

### Code Quality
- Follow existing model patterns and conventions
- Include comprehensive tests for new models
- Add proper documentation and help text
- Consider migration rollback scenarios

## Conclusion

The proposed new models **enhance the system architecture** by:

1. **Replacing custom actions** with proper REST resources
2. **Adding user preference management** for better UX
3. **Improving audit trails** and operation tracking
4. **Maintaining backward compatibility** during transition

**Recommendation:** Implement **UserPreferences first** (high value, low risk), then evaluate other models based on actual usage patterns and client feedback after the main refactoring is complete.

These models are **optional enhancements** that go beyond the core 8-week refactoring scope but provide a roadmap for future improvements.

---

**Implementation Priority:** Phase 5+ (post-refactoring enhancements)