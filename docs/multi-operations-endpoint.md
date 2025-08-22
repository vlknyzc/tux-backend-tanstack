# Multi-Operations Endpoint

## Overview

The Multi-Operations endpoint provides atomic transaction capabilities for executing multiple create, update, and delete operations across different models in a single API call. This solves the "all or nothing" requirement where complex workflows need guaranteed consistency.

## Endpoint URLs

- **Execute Operations**: `POST /api/v1/workspaces/{workspace_id}/multi-operations/execute/`
- **Validate Operations**: `POST /api/v1/workspaces/{workspace_id}/multi-operations/validate/`

## Key Features

### ✅ Atomic Transactions

- All operations succeed together, or all fail together
- Database rollback on any operation failure
- No partial updates or inconsistent states

### ✅ Comprehensive Operations

- **String Operations**: Create, update, delete strings and manage parent relationships
- **String Detail Operations**: Create, update, delete string details
- **Submission Operations**: Create, update, delete submissions

### ✅ Better URL Structure

Instead of the repetitive pattern:

```
❌ /api/v1/workspaces/{workspace_id}/batch-operations/batch-operations/
```

We use the cleaner pattern:

```
✅ /api/v1/workspaces/{workspace_id}/multi-operations/execute/
✅ /api/v1/workspaces/{workspace_id}/multi-operations/validate/
```

### ✅ Validation Before Execution

- Validate operations without executing them
- Check data integrity and permissions
- Preview operation results

## Supported Operation Types

### String Operations

- `create_string` - Create new string with details
- `update_string` - Update existing string properties
- `delete_string` - Delete string and related details
- `update_string_parent` - Update string parent relationship

### String Detail Operations

- `create_string_detail` - Create new string detail
- `update_string_detail` - Update existing string detail
- `delete_string_detail` - Delete string detail

### Submission Operations

- `create_submission` - Create new submission
- `update_submission` - Update existing submission
- `delete_submission` - Delete submission and related strings

## Request Format

### Individual Operations Format

```json
{
  "operations": [
    {
      "type": "operation_type",
      "data": {
        // Single operation data
      }
    }
  ]
}
```

### Grouped Array Format (Recommended)

```json
{
  "operations": [
    {
      "type": "operation_type",
      "data": [
        {
          // First operation data
        },
        {
          // Second operation data
        }
      ]
    }
  ]
}
```

**Benefits of Grouped Array Format:**

- ✅ **Cleaner JSON**: Less repetition of operation types
- ✅ **Better Organization**: Related operations grouped together
- ✅ **Improved Performance**: More efficient processing
- ✅ **Enhanced Readability**: Easier to understand complex workflows

## Response Format

### Success Response (200 OK)

```json
{
  "transaction_id": "uuid-string",
  "status": "completed",
  "total_operations": 2,
  "total_individual_operations": 3,
  "successful_operations": 2,
  "results": [
    {
      "operation_index": 0,
      "type": "update_string_detail",
      "status": "success",
      "count": 2,
      "results": [
        {
          "id": 154,
          "updated_fields": ["dimension_value"],
          "effective_value": "fr"
        },
        {
          "id": 157,
          "updated_fields": ["dimension_value_freetext"],
          "effective_value": "2"
        }
      ]
    },
    {
      "operation_index": 1,
      "type": "update_string_parent",
      "status": "success",
      "count": 1,
      "results": {
        "string_id": 88,
        "old_parent_id": null,
        "new_parent_id": 45
      }
    }
  ]
}
```

**Response Fields:**

- `total_operations`: Number of operation groups in the request
- `total_individual_operations`: Total number of individual operations executed
- `count`: Number of items processed in each operation group
- `results`: Single object (when count=1) or array (when count>1)

### Error Response (400 Bad Request)

```json
{
  "error": "Operation 1 (update_string_detail) failed: StringDetail 99999 does not exist",
  "transaction_id": "uuid-string",
  "status": "failed"
}
```

## Usage Examples

### Example 1: Original Use Case - Update Details and Parent

Solves the original problem of updating string details and changing parent relationships atomically.

**Using Grouped Array Format (Recommended):**

```json
POST /api/v1/workspaces/1/multi-operations/execute/
{
  "operations": [
    {
      "type": "update_string_detail",
      "data": [
        {"id": 154, "dimension_value": 3},
        {"id": 157, "dimension_value_freetext": "2"}
      ]
    },
    {
      "type": "update_string_parent",
      "data": {"string_id": 88, "parent_id": 45}
    }
  ]
}
```

**Using Individual Operations Format:**

```json
POST /api/v1/workspaces/1/multi-operations/execute/
{
  "operations": [
    {
      "type": "update_string_detail",
      "data": {"id": 154, "dimension_value": 3}
    },
    {
      "type": "update_string_detail",
      "data": {"id": 157, "dimension_value_freetext": "2"}
    },
    {
      "type": "update_string_parent",
      "data": {"string_id": 88, "parent_id": 45}
    }
  ]
}
```

### Example 2: Complex String Creation

```json
POST /api/v1/workspaces/1/multi-operations/execute/
{
  "operations": [
    {
      "type": "create_string",
      "data": {
        "field": 42,
        "submission": 123,
        "details": [
          {"dimension": 8, "dimension_value": 25},
          {"dimension": 12, "dimension_value_freetext": "custom"}
        ]
      }
    }
  ]
}
```

### Example 3: Validation Before Execution

```json
POST /api/v1/workspaces/1/multi-operations/validate/
{
  "operations": [
    {
      "type": "update_string_detail",
      "data": [
        {"id": 154, "dimension_value": 3},
        {"id": 157, "dimension_value_freetext": "2"}
      ]
    },
    {
      "type": "update_string_parent",
      "data": {"string_id": 88, "parent_id": 45}
    }
  ]
}
```

**Valid Response (200 OK):**

```json
{
  "status": "valid",
  "total_operations": 2,
  "message": "All operations are valid and ready for execution"
}
```

**Invalid Response (200 OK):**

```json
{
  "status": "invalid",
  "error": "Unknown operation type: invalid_operation_type",
  "total_operations": 0
}
```

## Error Handling

### Transaction Rollback

If any operation fails, the entire transaction is rolled back:

- No partial updates
- Database remains in consistent state
- Detailed error messages provided

### Validation Errors

- Missing required fields
- Invalid operation types
- Permission denied
- Resource not found

## Performance Benefits

### Single API Call

- Reduced network overhead
- Lower latency compared to multiple sequential requests
- Better user experience

### Database Efficiency

- Single transaction reduces connection overhead
- Optimized query execution
- Reduced lock contention

## Security Features

### Workspace Isolation

- All operations validated against workspace access
- Users can only operate on resources they have access to
- Workspace-scoped validation for all entities

### Permission Checking

- Authentication required for all operations
- User permissions validated per operation
- Audit trail maintained

## Implementation Details

### Files Created

- `master_data/serializers/batch_operations.py` - Multi-operation serializer
- `master_data/views/multi_operations_views.py` - ViewSet implementation
- `master_data/urls_main_api.py` - URL routing (updated)
- `examples/multi_operations_example.py` - Usage examples
- `docs/multi-operations-endpoint.md` - This documentation

### Database Transactions

- Uses Django's `@transaction.atomic` decorator
- Automatic rollback on any exception
- ACID compliance guaranteed

### Error Recovery

- Detailed error messages with operation context
- Transaction IDs for tracking
- Graceful failure handling

## Validate Endpoint Details

### How Validation Works

The validate endpoint (`POST /api/v1/workspaces/{workspace_id}/multi-operations/validate/`) performs comprehensive validation of operations **without executing them**. This is useful for:

- **Pre-flight Checks**: Validate operations before execution
- **Testing**: Test operation configurations safely
- **Debugging**: Identify issues in complex workflows
- **UI Validation**: Real-time validation in user interfaces

### What Gets Validated

#### Structure Validation

- ✅ Operations list is not empty
- ✅ Each operation has required `type` and `data` fields
- ✅ JSON structure is valid

#### Operation Type Validation

- ✅ Operation type is supported (see supported types above)
- ✅ Operation type spelling and case

#### Data Format Validation

- ✅ `data` field is object or array (not string/number/null)
- ✅ If `data` is array, it's not empty
- ✅ If `data` is array, all items are objects
- ✅ Data structure matches expected format

### Validation Response Format

#### Success Response (200 OK)

```json
{
  "status": "valid",
  "total_operations": 3,
  "message": "All operations are valid and ready for execution"
}
```

#### Validation Error Response (200 OK)

```json
{
  "status": "invalid",
  "error": "Operation 0 missing 'type' field",
  "total_operations": 0
}
```

**Note**: The validate endpoint always returns `200 OK`. Check the `status` field to determine if validation passed or failed.

### Common Validation Errors

#### Missing Fields

```json
{
  "status": "invalid",
  "error": "Operation 0 missing 'type' field",
  "total_operations": 0
}
```

#### Unknown Operation Type

```json
{
  "status": "invalid",
  "error": "Unknown operation type: invalid_operation_type",
  "total_operations": 0
}
```

#### Invalid Data Format

```json
{
  "status": "invalid",
  "error": "Operation 0 'data' must be an object or array",
  "total_operations": 0
}
```

#### Empty Array

```json
{
  "status": "invalid",
  "error": "Operation 0 'data' array cannot be empty",
  "total_operations": 0
}
```

#### Invalid Array Items

```json
{
  "status": "invalid",
  "error": "Operation 0 data item 1 must be an object",
  "total_operations": 0
}
```

### Validation Workflow Example

```javascript
// 1. Validate operations first
const validateResponse = await fetch(
  "/api/v1/workspaces/1/multi-operations/validate/",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operations }),
  }
);

const validation = await validateResponse.json();

if (validation.status === "valid") {
  // 2. Execute operations if validation passes
  const executeResponse = await fetch(
    "/api/v1/workspaces/1/multi-operations/execute/",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operations }),
    }
  );

  const result = await executeResponse.json();
  console.log("Operations completed:", result);
} else {
  // 3. Handle validation errors
  console.error("Validation failed:", validation.error);
  // Show user-friendly error message
  // Fix operations and retry validation
}
```

### Performance Characteristics

- **Fast**: No database operations performed
- **Lightweight**: Only validates JSON structure and types
- **Safe**: No side effects or data changes
- **Idempotent**: Can be called multiple times safely

### Limitations

The validate endpoint performs **structural validation only**. It does **NOT** validate:

- ❌ Database record existence (e.g., if ID 154 exists)
- ❌ User permissions for specific operations
- ❌ Business logic constraints
- ❌ Foreign key relationships
- ❌ Data integrity rules

For complete validation including database checks, you would need to use a "dry run" mode of the execute endpoint (not currently implemented).

## Best Practices

### Validation Strategy

- **Always validate** complex operations before execution
- **Cache validation results** to avoid repeated validation
- **Provide user feedback** based on validation errors
- **Use validation in CI/CD** pipelines for testing

### Operation Ordering

- Order operations by dependency (create before update)
- Consider foreign key relationships
- Plan for cascading effects

### Validation Strategy

- Always validate operations before execution
- Use the `/validate/` endpoint for complex workflows
- Handle validation errors gracefully

### Error Handling

- Implement retry logic for transient failures
- Log transaction IDs for debugging
- Provide user-friendly error messages

## Migration Guide

### From Individual Endpoints

```python
# Old approach - multiple API calls
update_string_detail(154, {"dimension_value": 3})
update_string_detail(157, {"dimension_value_freetext": "2"})
update_string_parent(88, 45)

# New approach - single atomic call
multi_operations([
    {"type": "update_string_detail", "data": {"id": 154, "dimension_value": 3}},
    {"type": "update_string_detail", "data": {"id": 157, "dimension_value_freetext": "2"}},
    {"type": "update_string_parent", "data": {"string_id": 88, "parent_id": 45}}
])
```

### Benefits of Migration

- Guaranteed consistency
- Better performance
- Simplified error handling
- Reduced complexity

## Conclusion

The Multi-Operations endpoint provides a robust, atomic solution for complex operations that require consistency across multiple entities. It solves the original problem of needing to update string details and parent relationships together while providing a clean, extensible API design.
