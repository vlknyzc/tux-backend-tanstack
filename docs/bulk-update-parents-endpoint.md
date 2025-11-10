# Bulk Update Dimension Value Parents Endpoint

## Overview

Endpoint for bulk updating parent relationships for dimension values within a workspace.

## Endpoint Details

- **URL**: `/api/v1/workspaces/{workspace_id}/dimension-values/bulk-update-parents/`
- **Method**: `POST`
- **Authentication**: Required
- **Content-Type**: `application/json`

## Request Format

### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_id` | integer | Yes | The ID of the workspace |

### Request Body

```json
{
    "assignments": [
        {
            "dimension_value_id": integer,
            "parent": integer | null
        }
    ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assignments` | array | Yes | List of parent assignment updates |
| `assignments[].dimension_value_id` | integer | Yes | ID of the dimension value to update |
| `assignments[].parent` | integer\|null | No | ID of the parent dimension value (null to remove parent) |

## Response Format

### Success Response (200 OK)

```json
{
    "success_count": 2,
    "error_count": 0,
    "updated_values": [
        {
            "id": 11,
            "value": "at",
            "label": "Austria",
            "dimension": 2,
            "dimension_name": "Country",
            "parent": 28,
            "parent_name": "Europe",
            "parent_value": "europe",
            "workspace": 1,
            "created": "2025-11-02T19:56:02.997936Z",
            "last_updated": "2025-11-03T23:54:01.014523Z"
        }
    ],
    "errors": []
}
```

### Partial Success Response (200 OK)

When some assignments fail but others succeed:

```json
{
    "success_count": 1,
    "error_count": 1,
    "updated_values": [
        {
            "id": 11,
            "value": "at",
            "parent": 28
        }
    ],
    "errors": [
        {
            "index": 1,
            "dimension_value_id": 99,
            "error": "Failed to update parent assignment"
        }
    ]
}
```

### Error Responses

#### 400 Bad Request

```json
{
    "assignments": [
        "Assignment at index 0: Parent dimension value must belong to dimension 'Region', but got dimension 'Country'"
    ]
}
```

#### 401 Unauthorized

```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 404 Not Found

```json
{
    "error": "Workspace with id 999 does not exist"
}
```

#### 500 Internal Server Error

```json
{
    "error": "Bulk parent update failed. Please try again or contact support."
}
```

## Examples

### Example 1: Update Single Parent Relationship

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/1/dimension-values/bulk-update-parents/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "assignments": [
        {
            "dimension_value_id": 11,
            "parent": 28
        }
    ]
}'
```

**Response:**

```json
{
    "success_count": 1,
    "error_count": 0,
    "updated_values": [
        {
            "id": 11,
            "value": "at",
            "label": "Austria",
            "parent": 28,
            "parent_name": "Europe"
        }
    ],
    "errors": []
}
```

### Example 2: Update Multiple Parent Relationships

**Request:**

```json
{
    "assignments": [
        {
            "dimension_value_id": 11,
            "parent": 28
        },
        {
            "dimension_value_id": 12,
            "parent": 28
        },
        {
            "dimension_value_id": 13,
            "parent": 29
        }
    ]
}
```

### Example 3: Remove Parent Relationship

**Request:**

```json
{
    "assignments": [
        {
            "dimension_value_id": 11,
            "parent": null
        }
    ]
}
```

## Validation Rules

The endpoint validates the following:

1. **Workspace Existence**: The workspace must exist
2. **Dimension Value Existence**: Each dimension value must exist in the specified workspace
3. **Parent Dimension Value Existence**: Each parent dimension value must exist in the specified workspace
4. **Dimension Hierarchy**: The parent's dimension must be the parent dimension of the child's dimension
5. **No Duplicates**: No duplicate `dimension_value_id` values in a single request
6. **At Least One Assignment**: The `assignments` array must contain at least one item

### Validation Example

If you have:
- Dimension "Region" (parent dimension)
- Dimension "Country" (child dimension with parent = "Region")
- DimensionValue "Europe" in "Region" dimension (ID: 28)
- DimensionValue "Austria" in "Country" dimension (ID: 11)

Then you CAN assign:
```json
{
    "dimension_value_id": 11,  // Austria (Country)
    "parent": 28               // Europe (Region)
}
```

But you CANNOT assign:
```json
{
    "dimension_value_id": 11,  // Austria (Country)
    "parent": 12               // Germany (Country) - wrong dimension!
}
```

## Transaction Behavior

- All updates are performed within a **database transaction**
- If any critical error occurs, **all changes are rolled back**
- Individual assignment failures are tracked but don't prevent other assignments from succeeding
- Cache invalidation occurs automatically for affected rules

## Side Effects

When parent relationships are updated:

1. **Cache Invalidation**: Related rule caches are automatically invalidated
2. **String Propagation**: If the dimension value is used in any strings, propagation jobs may be triggered
3. **Timestamp Update**: The `last_updated` field is updated for each modified dimension value

## Performance Considerations

- Recommended batch size: Up to 100 assignments per request
- For larger updates, consider splitting into multiple requests
- Cache invalidation is performed once per affected rule, not per dimension value

## Related Endpoints

- `GET /api/v1/workspaces/{workspace_id}/dimension-values/` - List dimension values
- `GET /api/v1/workspaces/{workspace_id}/dimension-values/{id}/` - Get single dimension value
- `PATCH /api/v1/workspaces/{workspace_id}/dimension-values/{id}/` - Update single dimension value
- `POST /api/v1/workspaces/{workspace_id}/dimension-values/bulk_create/` - Bulk create dimension values
