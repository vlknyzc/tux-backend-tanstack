# RESTful API Design for Submissions and Strings

This document outlines a comprehensive RESTful API design to replace the current nested-submission endpoint with atomic, resource-based operations.

## Problem Statement

The current nested-submission endpoint works for initial creation but has limitations:

- Not well-suited for adding additional strings to an existing submission
- Difficulty updating existing strings or submission details
- Strings and string details must always be updated in tandem to prevent data gaps

## Solution Overview

A workspace-scoped RESTful API design that:

- Uses clear resource-based naming
- Keeps operations atomic
- Supports standard HTTP methods
- Handles bulk and single-record operations
- Treats strings and string details as a single atomic unit
- **Makes string details the primary update mechanism** (strings are auto-updated via existing service)

## API Endpoint Design

### Core Resource Endpoints

#### Submissions

```
GET    /api/v1/workspaces/{workspace_id}/submissions/           # List submissions
POST   /api/v1/workspaces/{workspace_id}/submissions/           # Create submission
GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/      # Get submission details
PATCH  /api/v1/workspaces/{workspace_id}/submissions/{id}/      # Update submission
PUT    /api/v1/workspaces/{workspace_id}/submissions/{id}/      # Replace submission
DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/      # Delete submission
```

#### Strings (read-only, updated via details)

```
GET    /api/v1/workspaces/{workspace_id}/strings/               # List strings with details
POST   /api/v1/workspaces/{workspace_id}/strings/               # Create string with details
GET    /api/v1/workspaces/{workspace_id}/strings/{id}/          # Get string with details
DELETE /api/v1/workspaces/{workspace_id}/strings/{id}/          # Delete string and details
```

#### String Details (primary update mechanism)

```
GET    /api/v1/workspaces/{workspace_id}/string-details/        # List string details
POST   /api/v1/workspaces/{workspace_id}/string-details/        # Create string detail
GET    /api/v1/workspaces/{workspace_id}/string-details/{id}/   # Get string detail
PATCH  /api/v1/workspaces/{workspace_id}/string-details/{id}/   # Update string detail (triggers string update)
PUT    /api/v1/workspaces/{workspace_id}/string-details/{id}/   # Replace string detail (triggers string update)
DELETE /api/v1/workspaces/{workspace_id}/string-details/{id}/   # Delete string detail (triggers string update)
```

### Nested Resource Endpoints

#### Submission Strings (read-only, updated via details)

```
GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/           # List strings with details
POST   /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/           # Add string with details
GET    /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/{string_id}/ # Get string with details
DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/{string_id}/ # Remove string and details
```

#### String Details for Strings (primary update mechanism)

```
GET    /api/v1/workspaces/{workspace_id}/strings/{id}/details/               # List details for string
POST   /api/v1/workspaces/{workspace_id}/strings/{id}/details/               # Add detail to string (triggers string update)
GET    /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/   # Get specific string detail
PATCH  /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/   # Update string detail (triggers string update)
DELETE /api/v1/workspaces/{workspace_id}/strings/{id}/details/{detail_id}/   # Remove detail from string (triggers string update)
```

### Bulk Operations

```
POST   /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/bulk/      # Create multiple strings from details
DELETE /api/v1/workspaces/{workspace_id}/submissions/{id}/strings/bulk/      # Delete multiple strings

POST   /api/v1/workspaces/{workspace_id}/string-details/bulk/                # Create multiple string details (triggers string updates)
PATCH  /api/v1/workspaces/{workspace_id}/string-details/bulk/                # Update multiple string details (triggers string updates)
DELETE /api/v1/workspaces/{workspace_id}/string-details/bulk/                # Delete multiple string details (triggers string updates)
```

## Request/Response Schemas

### Submission Schemas

#### Create Submission (with optional bulk strings)

**Request: POST /api/v1/workspaces/1/submissions/**

```json
{
  "name": "string",
  "description": "string",
  "rule": "integer (rule_id)",
  "starting_field": "integer (field_id)",
  "selected_parent_string": "integer (string_id)" | null,
  "status": "draft|active|archived",
  "initial_strings": [
    {
      "field": "integer (field_id)",
      "parent": "integer (string_id)" | null,
      "parent_uuid": "uuid" | null,
      "string_uuid": "uuid" | null,
      "details": [
        {
          "dimension": "integer (dimension_id)",
          "dimension_value": "integer (dimension_value_id)" | null,
          "dimension_value_freetext": "string" | null
        }
      ]
    }
  ] | null
}
```

_Note: `initial_strings` is optional. When provided, strings are created atomically with submission. String values are generated from details._

#### Submission Response

```json
{
  "id": "integer",
  "name": "string",
  "slug": "string",
  "description": "string",
  "rule": {
    "id": "integer",
    "name": "string",
    "platform": "integer"
  },
  "starting_field": {
    "id": "integer",
    "name": "string",
    "field_level": "integer"
  },
  "selected_parent_string": {
    "id": "integer",
    "value": "string",
    "string_uuid": "uuid"
  } | null,
  "status": "string",
  "workspace": "integer",
  "created": "datetime",
  "modified": "datetime",
  "created_by": {
    "id": "integer",
    "name": "string"
  }
}
```

### String Schemas (value generated from details)

#### Create String with Details

**Request: POST /api/v1/workspaces/1/strings/**

```json
{
  "submission": "integer (submission_id)",
  "field": "integer (field_id)",
  "parent": "integer (string_id)" | null,
  "parent_uuid": "uuid" | null,
  "string_uuid": "uuid" | null,
  "details": [
    {
      "dimension": "integer (dimension_id)",
      "dimension_value": "integer (dimension_value_id)" | null,
      "dimension_value_freetext": "string" | null
    }
  ]
}
```

_Note: No `value` field in request - it's generated from details using business rules_

#### String Response (with embedded details)

```json
{
  "id": "integer",
  "submission": "integer",
  "field": {
    "id": "integer",
    "name": "string",
    "field_level": "integer"
  },
  "rule": {
    "id": "integer",
    "name": "string"
  },
  "value": "string",
  "string_uuid": "uuid",
  "parent": "integer" | null,
  "parent_uuid": "uuid" | null,
  "is_auto_generated": "boolean",
  "generation_metadata": "object",
  "version": "integer",
  "workspace": "integer",
  "created": "datetime",
  "modified": "datetime",
  "details": [
    {
      "id": "integer",
      "dimension": {
        "id": "integer",
        "name": "string",
        "type": "list|text"
      },
      "dimension_value": {
        "id": "integer",
        "value": "string",
        "label": "string"
      } | null,
      "dimension_value_freetext": "string" | null
    }
  ]
}
```

## Form-Based Creation Flow

When forms provide both submission and string data together (like the current nested-submission flow), there are several approaches:

### Option 1: Two-Step Atomic Flow (Recommended)

This maintains clean separation while ensuring atomicity through service layer:

#### Frontend Implementation

```javascript
const createSubmissionWithStrings = async (formData) => {
  // Service handles both calls atomically
  return await submissionService.createWithStrings({
    submission: {
      name: formData.name,
      description: formData.description,
      rule: formData.rule,
      starting_field: formData.starting_field,
      status: formData.status,
    },
    strings: formData.strings, // Array with embedded details
  });
};
```

#### Backend Service Layer

```python
@transaction.atomic
def create_with_strings(self, workspace_id, submission_data, strings_data):
    # Create submission
    submission = SubmissionSerializer(data=submission_data).save()

    # Create strings with details in bulk
    strings = []
    for string_data in strings_data:
        string_data['submission'] = submission.id
        string = StringWithDetailsSerializer(data=string_data).save()
        strings.append(string)

    return {'submission': submission, 'strings': strings}
```

Add special endpoint for form-based creation with bulk string support:

```
POST /api/v1/workspaces/{workspace_id}/submissions/with-strings/
```

**Request:**

```json
{
  "submission": {
    "name": "Data Pipeline Naming Convention",
    "rule": 15,
    "starting_field": 42,
    "status": "draft"
  },
  "strings": [
    {
      "field": 42,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [
        { "dimension": 8, "dimension_value": 25 },
        { "dimension": 9, "dimension_value_freetext": "production" }
      ]
    },
    {
      "field": 43,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [
        { "dimension": 8, "dimension_value": 25 },
        { "dimension": 11, "dimension_value": 50 }
      ]
    }
  ]
}
```

_Note: Supports creating multiple strings at once - no `value` fields, generated from details_

### Option 3: Extended Submission Creation (Recommended)

Extend the main submission POST endpoint to accept optional initial_strings with bulk support:

**Request: POST /api/v1/workspaces/1/submissions/**

```json
{
  "name": "Data Pipeline Naming Convention",
  "rule": 15,
  "starting_field": 42,
  "status": "draft",
  "initial_strings": [
    {
      "field": 42,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [
        { "dimension": 8, "dimension_value": 25 },
        { "dimension": 9, "dimension_value_freetext": "production" }
      ]
    },
    {
      "field": 43,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [
        { "dimension": 8, "dimension_value": 25 },
        { "dimension": 11, "dimension_value": 50 }
      ]
    }
  ]
}
```

**Response: 201 Created**

```json
{
  "id": 123,
  "name": "Data Pipeline Naming Convention",
  "rule": {"id": 15, "name": "Snowflake Table Naming"},
  "starting_field": {"id": 42, "name": "Database Level"},
  "status": "draft",
  "workspace": 1,
  "created": "2024-01-15T10:30:00Z",
  "strings": [
    {
      "id": 456,
      "field": {"id": 42, "name": "Database Level"},
      "value": "analytics_production_db",  // Generated from details
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [...]
    },
    {
      "id": 457,
      "field": {"id": 43, "name": "Schema Level"},
      "value": "customer_schema",  // Generated from details
      "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "details": [...]
    }
  ]
}
```

**Recommendation:** Use Option 3 (Extended Submission Creation) as it provides the best user experience while maintaining clean API design and supporting bulk string creation from the start.

## Bulk String Creation Scenarios

### Scenario 1: No Submission Exists Yet (Form-based Creation)

**Use:** Extended submission creation with `initial_strings`

```json
POST /api/v1/workspaces/1/submissions/
{
  "name": "My Submission",
  "rule": 15,
  "starting_field": 42,
  "initial_strings": [
    {"field": 42, "details": [...]},
    {"field": 43, "details": [...]}
  ]
}
```

### Scenario 2: Submission Exists, Adding More Strings

**Use:** Submission-specific bulk endpoint

```json
POST /api/v1/workspaces/1/submissions/123/strings/bulk/
{
  "strings": [
    {"field": 44, "details": [...]},
    {"field": 45, "details": [...]}
  ]
}
```

### Scenario 3: Creating Strings Across Multiple Submissions

**Use:** Workspace-level bulk endpoint (if implemented)

```json
POST /api/v1/workspaces/1/strings/bulk/
{
  "strings": [
    {"submission": 123, "field": 42, "details": [...]},
    {"submission": 124, "field": 43, "details": [...]}
  ]
}
```

## String Update Flow via String Details

Since strings are automatically updated when string details change (via existing service), the API design reflects this domain logic:

### How String Updates Work

1. **Client wants to change a string value** (e.g., "analytics_db" → "analytics_production_db")
2. **Client updates the relevant string detail** via PATCH `/api/v1/workspaces/1/string-details/789/`
3. **Backend service automatically regenerates string value** based on updated dimension values
4. **String.value and String.version are updated automatically**
5. **Response includes both updated detail and resulting string**

### Example Flow

```javascript
// Instead of updating string directly (not allowed):
// PATCH /strings/456/ { "value": "new_value" } ❌

// Update via string detail (triggers string regeneration):
PATCH / string -
  details /
    789 /
    {
      dimension_value: 30, // Change from "analytics" to "production"
    };

// Backend automatically:
// 1. Updates StringDetail.dimension_value = 30
// 2. Calls existing string regeneration service
// 3. Updates String.value = "analytics_production_db"
// 4. Increments String.version = 2
// 5. Triggers any propagation logic
```

### Benefits of This Approach

- ✅ **Leverages existing business logic** - Uses your current string regeneration service
- ✅ **Maintains data consistency** - String values always match dimension values
- ✅ **Prevents invalid states** - Can't manually set strings that don't match rules
- ✅ **Automatic propagation** - Existing propagation logic continues to work
- ✅ **Version tracking** - String versions increment on regeneration
- ✅ **Audit trail** - Clear record of what dimension changes triggered string updates

## Improved String Creation Pattern

### Problem with Current Flow

The current approach has a "chicken and egg" problem:

1. Create string with temporary/placeholder value
2. Create string details using the string ID
3. Update string value based on details (making initial value irrelevant)

This results in:

- ❌ Wasteful database operations
- ❌ Temporary invalid states
- ❌ Confusing API (provided value gets ignored)
- ❌ Performance impact from extra updates

### Recommended Solution: Details-First Creation

**New Flow:**

1. Client provides details only (no string value)
2. Backend creates string and details atomically
3. String value is generated immediately from details using existing business logic

**API Changes:**

```json
// Old approach (avoid):
POST /strings/ {
  "value": "temp_value",  // Gets ignored/overwritten
  "details": [...]
}

// New approach (recommended):
POST /strings/ {
  "details": [...]  // Value calculated from these
}
```

**Backend Implementation:**

```python
@transaction.atomic
def create(self, validated_data):
    details_data = validated_data.pop('details')

    # Create string with empty value
    string = String.objects.create(value="", **validated_data)

    # Create details
    for detail_data in details_data:
        StringDetail.objects.create(string=string, **detail_data)

    # Generate correct value using existing service
    string.regenerate_value()  # Calls your existing logic

    return string
```

**Benefits:**

- ✅ **Single transaction** - No intermediate invalid states
- ✅ **Leverages existing logic** - Uses your current string generation service
- ✅ **Clear semantics** - Details drive value, not the other way around
- ✅ **Better performance** - No wasted update operations
- ✅ **Data consistency** - Value always matches details from creation

## Example Usage Scenarios

### 1. Create Submission with Initial Strings and Details

#### Step 1: Create Submission

**Request: POST /api/v1/workspaces/1/submissions/**

```json
{
  "name": "Data Pipeline Naming Convention",
  "description": "Naming convention for Snowflake data pipeline",
  "rule": 15,
  "starting_field": 42,
  "selected_parent_string": null,
  "status": "draft"
}
```

**Response: 201 Created**

```json
{
  "id": 123,
  "name": "Data Pipeline Naming Convention",
  "slug": "data-pipeline-naming-convention",
  "description": "Naming convention for Snowflake data pipeline",
  "rule": {
    "id": 15,
    "name": "Snowflake Table Naming",
    "platform": 3
  },
  "starting_field": {
    "id": 42,
    "name": "Database Level",
    "field_level": 1
  },
  "selected_parent_string": null,
  "status": "draft",
  "workspace": 1,
  "created": "2024-01-15T10:30:00Z",
  "modified": "2024-01-15T10:30:00Z",
  "created_by": {
    "id": 5,
    "name": "John Doe"
  }
}
```

#### Step 2: Add Strings with Details to Submission

**Request: POST /api/v1/workspaces/1/submissions/123/strings/**

```json
{
  "field": 42,
  "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "parent_uuid": null,
  "details": [
    {
      "dimension": 8,
      "dimension_value": 25,
      "dimension_value_freetext": null
    },
    {
      "dimension": 9,
      "dimension_value": null,
      "dimension_value_freetext": "production"
    }
  ]
}
```

_Note: No `value` field - it's generated from dimension values using business rules_

**Response: 201 Created**

```json
{
  "id": 456,
  "submission": 123,
  "field": {
    "id": 42,
    "name": "Database Level",
    "field_level": 1
  },
  "value": "analytics_production_db", // Generated from details
  "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "parent": null,
  "parent_uuid": null,
  "is_auto_generated": true,
  "version": 1,
  "created": "2024-01-15T10:30:00Z",
  "modified": "2024-01-15T10:30:00Z",
  "details": [
    {
      "id": 789,
      "dimension": {
        "id": 8,
        "name": "Environment",
        "type": "list"
      },
      "dimension_value": {
        "id": 25,
        "value": "analytics",
        "label": "Analytics Environment"
      },
      "dimension_value_freetext": null
    },
    {
      "id": 790,
      "dimension": {
        "id": 9,
        "name": "Stage",
        "type": "text"
      },
      "dimension_value": null,
      "dimension_value_freetext": "production"
    }
  ]
}
```

### 2. Add Additional Strings to Existing Submission

#### Single String Addition

**Request: POST /api/v1/workspaces/1/submissions/123/strings/**

```json
{
  "field": 43,
  "value": "customer_schema",
  "string_uuid": "550e8400-e29b-41d4-a716-446655440001",
  "parent_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "details": [
    {
      "dimension": 8,
      "dimension_value": 25
    },
    {
      "dimension": 11,
      "dimension_value_freetext": "customer_data"
    }
  ]
}
```

#### Bulk String Addition

**Request: POST /api/v1/workspaces/1/submissions/123/strings/bulk/**

```json
{
  "strings": [
    {
      "field": 44,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440002",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "details": [
        {
          "dimension": 8,
          "dimension_value": 25
        },
        {
          "dimension": 12,
          "dimension_value": 50
        }
      ]
    },
    {
      "field": 44,
      "string_uuid": "550e8400-e29b-41d4-a716-446655440003",
      "parent_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "details": [
        {
          "dimension": 8,
          "dimension_value": 25
        },
        {
          "dimension": 13,
          "dimension_value": 60
        }
      ]
    }
  ]
}
```

_Note: No `value` fields - values generated from details for each string_

### 3. Update Existing Strings or Submission Details

#### Update Submission

**Request: PATCH /api/v1/workspaces/1/submissions/123/**

```json
{
  "status": "active",
  "description": "Updated naming convention for Snowflake data pipeline - now active"
}
```

#### Update String via String Detail (Recommended)

**Request: PATCH /api/v1/workspaces/1/string-details/789/**

```json
{
  "dimension": 8,
  "dimension_value": 30,
  "dimension_value_freetext": null
}
```

**Response: String automatically updated via existing service**

```json
{
  "id": 789,
  "dimension": {
    "id": 8,
    "name": "Environment",
    "type": "list"
  },
  "dimension_value": {
    "id": 30,
    "value": "production",
    "label": "Production Environment"
  },
  "dimension_value_freetext": null,
  "string": {
    "id": 456,
    "value": "analytics_production_db", // Auto-updated by service
    "version": 2 // Version incremented
  }
}
```

#### Bulk Update String Details

**Request: PATCH /api/v1/workspaces/1/string-details/bulk/**

```json
{
  "details": [
    {
      "id": 789,
      "dimension_value": 30
    },
    {
      "id": 790,
      "dimension_value_freetext": "prod"
    }
  ]
}
```

### 4. Retrieve Submission with All Related Data

**Request: GET /api/v1/workspaces/1/submissions/123/?include=strings,details**

**Response: 200 OK**

```json
{
  "id": 123,
  "name": "Data Pipeline Naming Convention",
  "slug": "data-pipeline-naming-convention",
  "description": "Updated naming convention for Snowflake data pipeline - now active",
  "rule": {
    "id": 15,
    "name": "Snowflake Table Naming",
    "platform": 3
  },
  "starting_field": {
    "id": 42,
    "name": "Database Level",
    "field_level": 1
  },
  "selected_parent_string": null,
  "status": "active",
  "workspace": 1,
  "created": "2024-01-15T10:30:00Z",
  "modified": "2024-01-15T14:20:00Z",
  "created_by": {
    "id": 5,
    "name": "John Doe"
  },
  "strings": [
    {
      "id": 456,
      "field": {
        "id": 42,
        "name": "Database Level",
        "field_level": 1
      },
      "value": "analytics_production_db",
      "string_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "parent": null,
      "parent_uuid": null,
      "is_auto_generated": false,
      "version": 2,
      "details": [
        {
          "id": 789,
          "dimension": {
            "id": 8,
            "name": "Environment",
            "type": "list"
          },
          "dimension_value": {
            "id": 30,
            "value": "production",
            "label": "Production Environment"
          },
          "dimension_value_freetext": null
        }
      ]
    }
  ]
}
```

### 5. Delete Operations

#### Delete String (with all details)

**Request: DELETE /api/v1/workspaces/1/strings/456/**

```
Response: 204 No Content
Note: This will cascade delete all related string details
```

#### Delete Submission (with all strings and details)

**Request: DELETE /api/v1/workspaces/1/submissions/123/**

```
Response: 204 No Content
Note: This will cascade delete all related strings and details
```

#### Bulk Delete Strings

**Request: DELETE /api/v1/workspaces/1/submissions/123/strings/bulk/**

```json
{
  "string_ids": [456, 457, 458]
}
```

## Additional Features

### Filtering and Pagination

```
GET /api/v1/workspaces/1/submissions/?status=active&rule=15&page=1&page_size=20
GET /api/v1/workspaces/1/strings/?submission=123&field_level=2&ordering=-created
```

### Include Related Data

```
GET /api/v1/workspaces/1/submissions/123/?include=strings,details,rule,platform
GET /api/v1/workspaces/1/strings/456/?include=field,submission
```

### Cross-Workspace Operations (for Superusers)

```
GET /api/v1/workspaces/1/submissions/
GET /api/v1/workspaces/2/submissions/
GET /api/v1/workspaces/*/submissions/  # All workspaces (superuser only)
```

## Backend Implementation Strategy

### Atomic Transaction Handling

```python
@transaction.atomic
def create(self, validated_data):
    details_data = validated_data.pop('details', [])

    # Create string
    string = String.objects.create(**validated_data)

    # Create all details
    for detail_data in details_data:
        StringDetail.objects.create(
            string=string,
            workspace=string.workspace,
            **detail_data
        )

    return string

@transaction.atomic
def update(self, instance, validated_data):
    details_data = validated_data.pop('details', None)

    # Update string fields
    for attr, value in validated_data.items():
        setattr(instance, attr, value)
    instance.save()

    # Handle details update
    if details_data is not None:
        # Delete existing details
        instance.string_details.all().delete()

        # Create new details
        for detail_data in details_data:
            StringDetail.objects.create(
                string=instance,
                workspace=instance.workspace,
                **detail_data
            )

    return instance
```

### Permission Strategy

```python
# View-level workspace validation
def dispatch(self, request, *args, **kwargs):
    workspace_id = kwargs.get('workspace_id')

    # Validate user has access to this workspace
    if not request.user.has_workspace_access(workspace_id):
        raise PermissionDenied(f"Access denied to workspace {workspace_id}")

    # Set workspace context for the request
    request.workspace_id = workspace_id
    return super().dispatch(request, *args, **kwargs)
```

### Validation Rules

```python
def validate_details(self, details):
    if not details:
        raise ValidationError("String details are required")

    # Validate no duplicate dimensions
    dimensions = [d.get('dimension') for d in details]
    if len(dimensions) != len(set(dimensions)):
        raise ValidationError("Duplicate dimensions not allowed")

    return details
```

## Benefits of This Design

1. **Clear Workspace Context** - Workspace is always explicit in the URL
2. **Data Integrity** - Strings and details are always created/updated together
3. **Enhanced Security** - Impossible to accidentally access wrong workspace data
4. **Atomic Operations** - All-or-nothing transaction handling
5. **Resource-based URLs** - Clear, predictable endpoint structure
6. **Standard HTTP methods** - Follows REST conventions
7. **Flexible querying** - Support for filtering, pagination, and includes
8. **Bulk operations** - Efficient handling of multiple records
9. **Frontend Simplicity** - Single API call creates complete string
10. **Reduced Complexity** - No need to manage separate detail endpoints
11. **Consistent State** - Prevents orphaned strings without details
12. **Better Performance** - Fewer API calls needed
13. **Easier Error Handling** - Single point of failure/success
14. **Workspace isolation** - Proper multi-tenant support
15. **Comprehensive CRUD** - Full lifecycle management for all resources
16. **Extensible** - Easy to add new operations and relationships

## Design Decisions

### Why Workspace in URL?

- Multi-tenant SaaS requires workspace context in every request
- URL-based scoping provides better security and clarity
- Eliminates need for workspace parameter in request bodies
- Makes permission validation straightforward

### Why Embed String Details?

- Strings and details are tightly coupled in the domain
- Prevents incomplete data states that cause frontend issues
- Reduces API calls and complexity
- Ensures atomic operations for related data

### Why String Details Drive String Updates?

- String values are calculated from dimension values via business rules
- Existing service automatically regenerates strings when details change
- Prevents manual string updates that could break business logic
- Maintains consistency between dimension values and generated strings
- Leverages existing propagation and validation logic

This design provides a clean, secure, and maintainable API that aligns with your multi-tenant architecture and domain requirements while preventing the data integrity issues you've identified.
