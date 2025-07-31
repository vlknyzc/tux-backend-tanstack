# String Auto-Regeneration Feature

## Overview

The String Auto-Regeneration feature automatically updates string values when their underlying `StringDetail` records are modified. This ensures that string values remain consistent with their dimension values without requiring manual regeneration API calls.

## How It Works

When a `StringDetail` record is updated (not created), the system automatically:

1. **Detects the change** via Django's `post_save` signal
2. **Regenerates the parent string** using the existing `String.regenerate_value()` method
3. **Propagates changes** to child strings in the hierarchy (if enabled)
4. **Logs all operations** for audit purposes

### String Generation Process

The regeneration follows the same logic as manual regeneration:

1. Collects all `StringDetail` values for the string
2. Applies `RuleDetail` configurations (prefix, suffix, delimiter, order)
3. Concatenates values according to the rule pattern
4. Updates the string value and increments version number

## Configuration

The feature is controlled by global settings in `MASTER_DATA_CONFIG`:

```python
MASTER_DATA_CONFIG = {
    # Enable/disable automatic string regeneration
    'AUTO_REGENERATE_STRINGS': True,

    # Fail silently (False) vs raise exceptions (True)
    'STRICT_AUTO_REGENERATION': False,

    # Propagate changes to child strings
    'ENABLE_INHERITANCE_PROPAGATION': True,

    # Maximum depth for inheritance propagation
    'MAX_INHERITANCE_DEPTH': 5,
}
```

### Environment Variables (Production)

For production deployments, these can be controlled via environment variables:

- `AUTO_REGENERATE_STRINGS=true/false`
- `STRICT_AUTO_REGENERATION=true/false`
- `ENABLE_INHERITANCE_PROPAGATION=true/false`
- `MAX_INHERITANCE_DEPTH=5`

## Behavior Details

### When Regeneration Occurs

✅ **Triggers regeneration:**

- Updating `StringDetail.dimension_value`
- Updating `StringDetail.dimension_value_freetext`
- Any field update on existing `StringDetail` records

❌ **Does NOT trigger regeneration:**

- Creating new `StringDetail` records
- Deleting `StringDetail` records
- Updates when `AUTO_REGENERATE_STRINGS=False`

### Inheritance Propagation

When `ENABLE_INHERITANCE_PROPAGATION=True`, changes cascade to child strings:

```
Parent String (updated)
  ├── Child String 1 (auto-regenerated)
  │   └── Grandchild String (auto-regenerated)
  └── Child String 2 (auto-regenerated)
```

The system respects `MAX_INHERITANCE_DEPTH` to prevent infinite loops.

### Error Handling

**Non-Strict Mode** (`STRICT_AUTO_REGENERATION=False`):

- Errors are logged but don't interrupt the request
- The original `StringDetail` update succeeds
- Failed regenerations are captured in logs

**Strict Mode** (`STRICT_AUTO_REGENERATION=True`):

- Any regeneration error raises an exception
- The entire transaction is rolled back
- The `StringDetail` update fails

## Safety Features

### Circular Dependency Prevention

The system prevents infinite recursion through:

- **Recursion guards**: `_regenerating` flag on instances
- **Depth limiting**: `MAX_INHERITANCE_DEPTH` setting
- **Signal filtering**: Only processes updates, not creations

### Transaction Safety

All regeneration operations are wrapped in `transaction.atomic()` blocks to ensure data consistency.

## Logging

The feature logs to `master_data.string_regeneration` logger:

```python
# Example log entries
INFO: Auto-regenerating string 123 due to StringDetail 456 update
INFO: String 123 auto-regenerated: 'Nike-Summer2024' -> 'Nike-Winter2024' (triggered by StringDetail 456)
INFO: Propagating regeneration to 2 child strings of 123
ERROR: Auto-regeneration failed for StringDetail 456: Missing dimension value
```

## API Impact

### No Breaking Changes

The feature operates transparently:

- Existing API endpoints work unchanged
- No new required parameters
- Backward compatible with manual regeneration

### Response Behavior

When updating `StringDetail` via API:

```http
PUT /api/v1/string-details/123/
{
    "dimension_value": 456
}
```

**Response includes updated string value:**

```json
{
  "id": 123,
  "string": {
    "id": 789,
    "value": "Nike-Winter2024", // Auto-regenerated
    "version": 2 // Incremented
  }
  // ... other fields
}
```

## Performance Considerations

### Database Impact

- **Minimal overhead**: Uses existing regeneration logic
- **Optimized queries**: Leverages existing `select_related` patterns
- **Batch friendly**: Processes updates individually but efficiently

### Scaling Recommendations

For high-volume environments:

- Consider disabling inheritance propagation
- Use monitoring to track regeneration frequency
- Implement rate limiting if needed

## Testing

Comprehensive test coverage includes:

- ✅ Basic regeneration on `StringDetail` update
- ✅ No regeneration on creation
- ✅ Configuration enable/disable
- ✅ Inheritance propagation
- ✅ Circular dependency prevention
- ✅ Error handling (strict/non-strict modes)
- ✅ Transaction rollback scenarios

Run tests with:

```bash
python manage.py test master_data.tests.test_string_detail_auto_regeneration
```

## Migration Notes

### Enabling the Feature

1. **Deploy the code** with `AUTO_REGENERATE_STRINGS=True`
2. **Monitor logs** for regeneration activity
3. **Verify behavior** in staging environment first

### Disabling the Feature

Set `AUTO_REGENERATE_STRINGS=False` in configuration - no code changes needed.

### Rollback Plan

The feature can be safely disabled without data loss:

- Existing strings remain unchanged
- Manual regeneration APIs continue to work
- No database schema changes required

## Troubleshooting

### Common Issues

**Regeneration not occurring:**

- Check `AUTO_REGENERATE_STRINGS` setting
- Verify you're updating (not creating) `StringDetail`
- Check logs for recursion guard messages

**Performance issues:**

- Disable inheritance propagation temporarily
- Check `MAX_INHERITANCE_DEPTH` setting
- Monitor regeneration frequency in logs

**Transaction errors:**

- Review `STRICT_AUTO_REGENERATION` setting
- Check for conflicting string values
- Verify rule configuration completeness

### Debug Logging

Enable debug logging for detailed information:

```python
LOGGING = {
    'loggers': {
        'master_data.string_regeneration': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```
