# Dimension Constraints API - Frontend Integration Guide

## Overview

The Dimension Constraints API is now fully implemented and ready for frontend integration. All endpoints follow RESTful conventions and automatically convert between `camelCase` (frontend) and `snake_case` (backend).

**Base URL:** `/api/v1/dimension-constraints/`

---

## Quick Reference

| Operation | Method | Endpoint | Use Case |
|-----------|--------|----------|----------|
| List constraints for dimension | GET | `/by-dimension/{dimensionId}/` | Load constraints in dimension settings |
| Create single constraint | POST | `/` | Add one constraint manually |
| Update constraint | PUT | `/{constraintId}/` | Edit existing constraint |
| Delete constraint | DELETE | `/{constraintId}/` | Remove constraint |
| Bulk create constraints | POST | `/bulk-create/{dimensionId}/` | Apply preset templates |
| Reorder constraints | PUT | `/reorder/{dimensionId}/` | Drag-and-drop reordering |
| Validate value | POST | `/validate/{dimensionId}/` | Real-time validation preview |
| Check violations | GET | `/violations/{dimensionId}/` | Report existing invalid values |

---

## Detailed Endpoint Documentation

### 1. Get Constraints for a Dimension

**Endpoint:** `GET /api/v1/dimension-constraints/by-dimension/{dimensionId}/`

**Use Case:** Load all constraints when opening dimension settings page

**Response:**
```json
[
  {
    "id": 1,
    "dimension": 123,
    "dimensionName": "Environment",
    "constraintType": "lowercase",
    "value": null,
    "errorMessage": "Value must be lowercase",
    "order": 1,
    "isActive": true,
    "createdBy": 1,
    "createdByName": "John Doe",
    "created": "2024-01-15T10:30:00Z",
    "lastUpdated": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "dimension": 123,
    "constraintType": "maxLength",
    "value": "50",
    "errorMessage": null,
    "order": 2,
    "isActive": true,
    "createdBy": 1,
    "createdByName": "John Doe",
    "created": "2024-01-15T10:30:00Z",
    "lastUpdated": "2024-01-15T10:30:00Z"
  }
]
```

---

### 2. Create Single Constraint

**Endpoint:** `POST /api/v1/dimension-constraints/`

**Use Case:** Add a new constraint manually via UI

**Request Body:**
```json
{
  "dimension": 123,
  "constraintType": "lowercase",
  "value": null,  // Optional - only for constraints that need it
  "errorMessage": "Custom error message",  // Optional
  "order": 1,  // Optional - auto-calculated if omitted
  "isActive": true  // Optional - defaults to true
}
```

**Response:** `201 Created` with constraint object (same structure as GET)

**Error Response:** `400 Bad Request`
```json
{
  "value": ["Constraint type 'maxLength' requires a configuration value"]
}
```

---

### 3. Update Constraint

**Endpoint:** `PUT /api/v1/dimension-constraints/{constraintId}/`

**Use Case:** Edit existing constraint settings

**Request Body:** (all fields optional)
```json
{
  "constraintType": "minLength",
  "value": "10",
  "errorMessage": "Updated message",
  "order": 2,
  "isActive": false
}
```

**Response:** `200 OK` with updated constraint object

---

### 4. Delete Constraint

**Endpoint:** `DELETE /api/v1/dimension-constraints/{constraintId}/`

**Use Case:** Remove unwanted constraint

**Response:** `204 No Content`

---

### 5. Bulk Create Constraints (Apply Preset)

**Endpoint:** `POST /api/v1/dimension-constraints/bulk-create/{dimensionId}/`

**Use Case:** Apply preset constraint templates (e.g., "URL Safe", "Lowercase Alphanumeric")

**Request Body:**
```json
{
  "constraints": [
    {
      "constraintType": "lowercase",
      "errorMessage": "Must be lowercase"
    },
    {
      "constraintType": "noSpaces",
      "errorMessage": "No spaces allowed"
    },
    {
      "constraintType": "maxLength",
      "value": "50"
    }
  ]
}
```

**Response:** `201 Created` with array of created constraints

**Notes:**
- Orders are auto-assigned sequentially
- Transaction: All or nothing (rollback on any error)

---

### 6. Reorder Constraints

**Endpoint:** `PUT /api/v1/dimension-constraints/reorder/{dimensionId}/`

**Use Case:** Update constraint execution order after drag-and-drop

**Request Body:**
```json
{
  "constraintIds": [3, 1, 2]  // New order by ID
}
```

**Response:** `200 OK` with reordered constraints array

**Validation:**
- All IDs must belong to the specified dimension
- All existing constraints must be included

---

### 7. Validate Value (Preview)

**Endpoint:** `POST /api/v1/dimension-constraints/validate/{dimensionId}/`

**Use Case:** Real-time validation as user types in dimension value field

**Request Body:**
```json
{
  "value": "test-value-123"
}
```

**Response:** `200 OK`
```json
{
  "isValid": false,
  "errors": [
    {
      "constraintType": "noSpecialChars",
      "errorMessage": "Only letters, numbers, and underscores allowed"
    }
  ]
}
```

**Notes:**
- Always returns `200 OK` (validation result, not an error)
- Apply constraints in order
- Returns all violations, not just the first one

---

### 8. Check Existing Value Violations

**Endpoint:** `GET /api/v1/dimension-constraints/violations/{dimensionId}/`

**Use Case:** Show warning when adding constraints to dimension with existing values

**Response:** `200 OK`
```json
{
  "hasViolations": true,
  "totalValues": 10,
  "violatingValues": 3,
  "violations": [
    {
      "dimensionValueId": 45,
      "value": "Test Value",
      "label": "Test Value Label",
      "errors": [
        {
          "constraintType": "lowercase",
          "errorMessage": "Only lowercase letters allowed"
        }
      ]
    }
  ]
}
```

---

## Constraint Types Reference

### Constraints That Do NOT Require `value` Field:

- `noSpaces` - No whitespace allowed
- `lowercase` - Only lowercase letters
- `uppercase` - Only uppercase letters
- `noSpecialChars` - Alphanumeric + underscore only
- `alphanumeric` - Letters and numbers only
- `numeric` - Numbers only
- `noUppercase` - No uppercase letters
- `noNumbers` - No numeric characters
- `urlSafe` - URL-safe characters (a-z, A-Z, 0-9, -, _, .)

### Constraints That REQUIRE `value` Field:

- `maxLength` - Maximum character length (value: `"50"`)
- `minLength` - Minimum character length (value: `"3"`)
- `regex` - Custom regex pattern (value: `"^[a-z0-9-]+$"`)
- `startsWith` - Must start with string (value: `"utm_"`)
- `endsWith` - Must end with string (value: `"_campaign"`)
- `allowedChars` - Whitelist of characters (value: `"abcdefghijklmnopqrstuvwxyz0123456789-_"`)

---

## Integration with Dimension Values

When creating or updating dimension values, constraints are **automatically validated**.

**Endpoint:** `POST /api/v1/dimension-values/`

**Success:** `201 Created` (value passes all active constraints)

**Validation Failure:** `400 Bad Request`
```json
{
  "error": "Constraint validation failed",
  "validationErrors": [
    {
      "constraintType": "lowercase",
      "errorMessage": "Value must be lowercase"
    }
  ]
}
```

**Enforcement Policy:**
- **New values:** Validated against all active constraints
- **Existing values:** Grandfathered in (not validated retroactively)

---

## Recommended UI Flows

### 1. Dimension Settings Page

```javascript
// Load constraints when page opens
const constraints = await fetch(`/api/v1/dimension-constraints/by-dimension/${dimensionId}/`);

// Display in list with drag handles for reordering
// Show toggle for isActive
// Edit/Delete buttons per constraint
```

### 2. Adding a Constraint

```javascript
// User selects constraint type from dropdown
// If type requires value, show input field
// Optional: Custom error message input
// On save:
await fetch('/api/v1/dimension-constraints/', {
  method: 'POST',
  body: JSON.stringify({
    dimension: dimensionId,
    constraintType: selectedType,
    value: requiresValue ? inputValue : null,
    errorMessage: customMessage || null
  })
});
```

### 3. Applying a Preset

```javascript
// User clicks "Apply URL Safe Preset"
const preset = {
  constraints: [
    { constraintType: 'lowercase' },
    { constraintType: 'noSpaces' },
    { constraintType: 'urlSafe' }
  ]
};

await fetch(`/api/v1/dimension-constraints/bulk-create/${dimensionId}/`, {
  method: 'POST',
  body: JSON.stringify(preset)
});
```

### 4. Drag-and-Drop Reordering

```javascript
// After user reorders constraints via drag-and-drop
const newOrder = [3, 1, 2]; // IDs in new order

await fetch(`/api/v1/dimension-constraints/reorder/${dimensionId}/`, {
  method: 'PUT',
  body: JSON.stringify({ constraintIds: newOrder })
});
```

### 5. Real-Time Validation (Dimension Value Form)

```javascript
// As user types in dimension value input
const response = await fetch(`/api/v1/dimension-constraints/validate/${dimensionId}/`, {
  method: 'POST',
  body: JSON.stringify({ value: currentInputValue })
});

const { isValid, errors } = await response.json();

if (!isValid) {
  // Show error messages below input
  errors.forEach(err => showError(err.errorMessage));
}
```

### 6. Warning When Adding Constraints

```javascript
// Before creating constraint, check for violations
const violations = await fetch(`/api/v1/dimension-constraints/violations/${dimensionId}/`);
const { hasViolations, violatingValues } = await violations.json();

if (hasViolations) {
  showWarning(`${violatingValues} existing values will not comply with this constraint`);
  // Give user option to proceed or cancel
}
```

---

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Success (GET, PUT)
- `201 Created` - Resource created (POST)
- `204 No Content` - Resource deleted (DELETE)
- `400 Bad Request` - Validation error or missing required fields
- `403 Forbidden` - User lacks workspace access
- `404 Not Found` - Dimension or constraint doesn't exist
- `409 Conflict` - Order already exists for dimension

### Example Error Response

```json
{
  "value": ["Constraint type 'regex' requires a configuration value"]
}
```

---

## Performance Notes

- Constraints are **cached** (15 minutes) for validation performance
- Cache automatically cleared when constraints are modified
- Validation happens **server-side** on dimension value create/update
- Use the `/validate/` endpoint for **client-side** preview only

---

## Questions or Issues?

If you encounter any issues or need clarification:
1. Check the API response for detailed error messages
2. Verify constraint type and value requirements
3. Ensure user has workspace access for the dimension
4. Contact backend team for additional support

---

**Last Updated:** January 2025
**Backend Version:** v1
**Feature Status:** ✅ Production Ready
