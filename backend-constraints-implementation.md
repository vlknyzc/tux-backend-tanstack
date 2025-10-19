# Backend Implementation Guide: Dimension Constraints

## Overview

This document outlines the backend implementation requirements for the dimension constraints feature. The frontend is fully implemented and ready for integration.

## Database Schema

### New Table: `dimension_constraints`

```sql
CREATE TABLE dimension_constraints (
    id SERIAL PRIMARY KEY,
    dimension_id INTEGER NOT NULL REFERENCES dimensions(id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL,
    value VARCHAR(255),  -- Optional: for constraints that need configuration (e.g., max_length, regex)
    error_message TEXT,  -- Optional: custom error message
    order INTEGER NOT NULL DEFAULT 0,  -- Order of constraint application
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_dimension_constraint_order UNIQUE(dimension_id, order)
);

CREATE INDEX idx_dimension_constraints_dimension ON dimension_constraints(dimension_id);
CREATE INDEX idx_dimension_constraints_active ON dimension_constraints(dimension_id, is_active);
```

## Constraint Types

The system supports 15 constraint types:

| Type | Requires Value | Description | Example Value |
|------|---------------|-------------|---------------|
| `no_spaces` | No | No whitespace allowed | - |
| `lowercase` | No | Only lowercase letters | - |
| `uppercase` | No | Only uppercase letters | - |
| `no_special_chars` | No | Alphanumeric + underscore only | - |
| `alphanumeric` | No | Letters and numbers only | - |
| `numeric` | No | Numbers only | - |
| `max_length` | Yes | Maximum character length | `"50"` |
| `min_length` | Yes | Minimum character length | `"3"` |
| `regex` | Yes | Custom regex pattern | `"^[a-z0-9-]+$"` |
| `starts_with` | Yes | Must start with string | `"utm_"` |
| `ends_with` | Yes | Must end with string | `"_campaign"` |
| `allowed_chars` | Yes | Whitelist of characters | `"abcdefghijklmnopqrstuvwxyz0123456789-_"` |
| `no_uppercase` | No | No uppercase letters | - |
| `no_numbers` | No | No numeric characters | - |
| `url_safe` | No | URL-safe chars (a-z, 0-9, -, _, .) | - |

## API Endpoints

### 1. Get Constraints for a Dimension

```http
GET /api/dimensions/{dimension_id}/constraints
```

**Response:**
```json
[
  {
    "id": 1,
    "dimension": 123,
    "constraint_type": "lowercase",
    "value": null,
    "error_message": "Value must be lowercase",
    "order": 1,
    "is_active": true,
    "created_by": 1,
    "created_by_name": "John Doe",
    "created": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "dimension": 123,
    "constraint_type": "max_length",
    "value": "50",
    "error_message": null,
    "order": 2,
    "is_active": true,
    "created_by": 1,
    "created_by_name": "John Doe",
    "created": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-15T10:30:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Dimension doesn't exist

---

### 2. Create Constraint

```http
POST /api/dimension-constraints
```

**Request Body:**
```json
{
  "dimension": 123,
  "constraint_type": "max_length",
  "value": "50",  // Optional
  "error_message": "Custom error message",  // Optional
  "order": 1,  // Optional, auto-calculated if not provided
  "is_active": true  // Optional, defaults to true
}
```

**Response:**
```json
{
  "id": 1,
  "dimension": 123,
  "constraint_type": "max_length",
  "value": "50",
  "error_message": "Custom error message",
  "order": 1,
  "is_active": true,
  "created_by": 1,
  "created_by_name": "John Doe",
  "created": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `201 Created` - Success
- `400 Bad Request` - Invalid constraint type or missing required fields
- `404 Not Found` - Dimension doesn't exist
- `409 Conflict` - Order already exists for this dimension

**Notes:**
- If `order` is not provided, set it to `MAX(order) + 1` for that dimension
- Validate that `constraint_type` is one of the allowed types
- For constraint types that require a value (see table above), validate that `value` is provided

---

### 3. Update Constraint

```http
PUT /api/dimension-constraints/{constraint_id}
```

**Request Body:**
```json
{
  "constraint_type": "min_length",  // Optional
  "value": "10",  // Optional
  "error_message": "Updated message",  // Optional
  "order": 2,  // Optional
  "is_active": false  // Optional
}
```

**Response:** Same as Create

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid data
- `404 Not Found` - Constraint doesn't exist
- `409 Conflict` - Order conflict

---

### 4. Delete Constraint

```http
DELETE /api/dimension-constraints/{constraint_id}
```

**Response:**
```json
{
  "message": "Constraint deleted successfully"
}
```

**Status Codes:**
- `204 No Content` - Success
- `404 Not Found` - Constraint doesn't exist

**Notes:**
- After deletion, reorder remaining constraints to fill gaps (optional, but recommended)

---

### 5. Bulk Create Constraints

```http
POST /api/dimensions/{dimension_id}/constraints/bulk
```

**Request Body:**
```json
{
  "constraints": [
    {
      "constraint_type": "lowercase",
      "error_message": "Must be lowercase"
    },
    {
      "constraint_type": "no_spaces",
      "error_message": "No spaces allowed"
    },
    {
      "constraint_type": "max_length",
      "value": "50"
    }
  ]
}
```

**Response:**
```json
[
  {
    "id": 1,
    "dimension": 123,
    "constraint_type": "lowercase",
    "order": 1,
    ...
  },
  {
    "id": 2,
    "dimension": 123,
    "constraint_type": "no_spaces",
    "order": 2,
    ...
  },
  {
    "id": 3,
    "dimension": 123,
    "constraint_type": "max_length",
    "value": "50",
    "order": 3,
    ...
  }
]
```

**Status Codes:**
- `201 Created` - All constraints created
- `400 Bad Request` - Invalid data
- `404 Not Found` - Dimension doesn't exist

**Notes:**
- Used for applying presets
- Orders should be auto-assigned sequentially
- Transaction: All or nothing (rollback on any error)

---

### 6. Reorder Constraints

```http
PUT /api/dimensions/{dimension_id}/constraints/reorder
```

**Request Body:**
```json
{
  "constraint_ids": [3, 1, 2]  // New order
}
```

**Response:**
```json
[
  {
    "id": 3,
    "order": 1,
    ...
  },
  {
    "id": 1,
    "order": 2,
    ...
  },
  {
    "id": 2,
    "order": 3,
    ...
  }
]
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid constraint IDs or missing constraints
- `404 Not Found` - Dimension doesn't exist

**Notes:**
- Validate all constraint_ids belong to the specified dimension
- Update orders based on array position

---

### 7. Validate Value Against Constraints

```http
POST /api/dimensions/{dimension_id}/validate
```

**Request Body:**
```json
{
  "value": "test-value-123"
}
```

**Response:**
```json
{
  "is_valid": false,
  "errors": [
    {
      "constraint_type": "no_special_chars",
      "error_message": "Only letters, numbers, and underscores allowed"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Validation completed (even if invalid)
- `404 Not Found` - Dimension doesn't exist

**Notes:**
- This is for server-side validation (frontend already validates client-side)
- Apply constraints in order
- Return all violations, not just the first one

---

## Validation Logic

### Implementation Guidelines

For each constraint type, implement the following validation:

```python
# Example validation logic (Python pseudocode)

def validate_constraint(value: str, constraint: Constraint) -> ValidationResult:
    constraint_type = constraint.constraint_type
    config_value = constraint.value

    if constraint_type == "no_spaces":
        is_valid = " " not in value and "\t" not in value and "\n" not in value

    elif constraint_type == "lowercase":
        is_valid = value.islower() and any(c.isalpha() for c in value)

    elif constraint_type == "uppercase":
        is_valid = value.isupper() and any(c.isalpha() for c in value)

    elif constraint_type == "no_special_chars":
        is_valid = all(c.isalnum() or c == "_" for c in value)

    elif constraint_type == "alphanumeric":
        is_valid = value.isalnum()

    elif constraint_type == "numeric":
        is_valid = value.isdigit()

    elif constraint_type == "max_length":
        is_valid = len(value) <= int(config_value)

    elif constraint_type == "min_length":
        is_valid = len(value) >= int(config_value)

    elif constraint_type == "regex":
        import re
        is_valid = bool(re.match(config_value, value))

    elif constraint_type == "starts_with":
        is_valid = value.startswith(config_value)

    elif constraint_type == "ends_with":
        is_valid = value.endswith(config_value)

    elif constraint_type == "allowed_chars":
        allowed = set(config_value)
        is_valid = all(c in allowed for c in value)

    elif constraint_type == "no_uppercase":
        is_valid = not any(c.isupper() for c in value)

    elif constraint_type == "no_numbers":
        is_valid = not any(c.isdigit() for c in value)

    elif constraint_type == "url_safe":
        import re
        is_valid = bool(re.match(r'^[a-zA-Z0-9\-_.]+$', value))

    return ValidationResult(
        is_valid=is_valid,
        error_message=constraint.error_message or get_default_error(constraint_type)
    )

def validate_all_constraints(value: str, constraints: List[Constraint]) -> dict:
    errors = []
    active_constraints = [c for c in constraints if c.is_active]
    active_constraints.sort(key=lambda c: c.order)

    for constraint in active_constraints:
        result = validate_constraint(value, constraint)
        if not result.is_valid:
            errors.append({
                "constraint_type": constraint.constraint_type,
                "error_message": result.error_message
            })

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
```

---

## Integration with Dimension Values

### During Dimension Value Creation/Update

When a dimension value is created or updated, validate against constraints:

```python
# Example: Dimension Value Creation
POST /api/dimension-values

def create_dimension_value(data):
    # Get constraints for the dimension
    constraints = get_constraints_for_dimension(data.dimension)

    # Validate the value
    validation_result = validate_all_constraints(data.value, constraints)

    if not validation_result["is_valid"]:
        return Response({
            "error": "Constraint validation failed",
            "validation_errors": validation_result["errors"]
        }, status=400)

    # Proceed with creation
    dimension_value = create_dimension_value_record(data)
    return Response(dimension_value, status=201)
```

**Important:**
- Validation should be **required** for dimension value creation/update
- Return clear error messages indicating which constraints failed
- Use HTTP 400 Bad Request for validation failures

---

## Field Name Conversion

The frontend uses **camelCase** for all fields, but the backend should use **snake_case**.

### Conversion Required

Frontend → Backend:
- `constraintType` → `constraint_type`
- `errorMessage` → `error_message`
- `isActive` → `is_active`
- `createdBy` → `created_by`
- `createdByName` → `created_by_name`
- `lastUpdated` → `last_updated`

Backend → Frontend (response):
- `constraint_type` → `constraintType`
- `error_message` → `errorMessage`
- `is_active` → `isActive`
- `created_by` → `createdBy`
- `created_by_name` → `createdByName`
- `last_updated` → `lastUpdated`

**Note:** The existing `apiFetch` utility in the frontend automatically handles this conversion.

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error description",
  "field_errors": {
    "constraint_type": ["This field is required"],
    "value": ["Invalid regex pattern"]
  }
}
```

### Common Error Scenarios

1. **Invalid Constraint Type**
   - Status: `400 Bad Request`
   - Message: `"Invalid constraint type: {type}"`

2. **Missing Required Value**
   - Status: `400 Bad Request`
   - Message: `"Constraint type '{type}' requires a configuration value"`

3. **Order Conflict**
   - Status: `409 Conflict`
   - Message: `"A constraint with order {order} already exists for this dimension"`

4. **Dimension Not Found**
   - Status: `404 Not Found`
   - Message: `"Dimension with id {id} not found"`

5. **Constraint Validation Failed**
   - Status: `400 Bad Request`
   - Include validation errors in response

---

## Performance Considerations

1. **Index on dimension_id**: Ensure fast lookups for constraints by dimension
2. **Caching**: Consider caching constraints for frequently accessed dimensions
3. **Batch Validation**: When bulk creating dimension values, validate all values in a single query
4. **Order Management**: When deleting constraints, consider if you want to reorder or leave gaps

---

## Migration Strategy

### For Existing Dimensions with Values

When constraints are added to a dimension that already has values:

1. **Option 1: Soft Enforcement**
   - New values must comply with constraints
   - Existing values are grandfathered in
   - Provide an API endpoint to check compliance: `GET /api/dimensions/{id}/constraint-violations`

2. **Option 2: Validation Report**
   - Return a report of violations when creating constraints
   - Allow admin to decide: fix values, adjust constraints, or accept violations

3. **Option 3: Hard Enforcement** (Not Recommended)
   - Reject constraint creation if existing values violate it

**Recommendation:** Start with Option 1 (Soft Enforcement)

---

## Testing Checklist

- [ ] Create constraint for each type
- [ ] Update constraint (change type, value, order)
- [ ] Delete constraint
- [ ] Bulk create constraints
- [ ] Reorder constraints
- [ ] Validate that inactive constraints are ignored
- [ ] Test constraint ordering (correct application order)
- [ ] Test dimension value creation with constraints
- [ ] Test dimension value creation with invalid values
- [ ] Test each constraint type validation
- [ ] Test constraints with special characters in values
- [ ] Test regex constraint with invalid patterns
- [ ] Test numeric values for max_length/min_length
- [ ] Test cascade delete (dimension deletion removes constraints)
- [ ] Test permissions (users can only manage constraints for their workspace)

---

## Security Considerations

1. **Workspace Isolation**: Ensure users can only manage constraints for dimensions in their workspace
2. **Regex Validation**: Validate regex patterns to prevent ReDoS attacks
3. **Input Sanitization**: Sanitize error messages to prevent XSS
4. **Rate Limiting**: Apply rate limits to validation endpoints

---

## Frontend Integration Status

✅ **Fully Implemented:**
- Type definitions
- API integration layer (awaiting endpoints)
- Validation utilities (client-side)
- React hooks with TanStack Query
- UI components (Manager, Builder, etc.)
- Real-time validation in forms
- Constraint presets
- Dedicated constraints page
- Navigation and routing

The frontend will work immediately once the backend endpoints are available.

---

## Questions?

For any questions or clarifications, please contact the frontend team or refer to:
- Frontend constraint types: `src/types/dimension-constraint.ts`
- Validation logic: `src/utils/dimension-constraints/validator.ts`
- API integration: `src/lib/api/dimension-constraints.ts`
