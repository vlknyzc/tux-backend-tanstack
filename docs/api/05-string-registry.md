# String Registry API

The String Registry validates and imports external platform strings (from Meta Ads, Google Ads, TikTok, etc.) into Tuxonomy projects. It uses a dual-model architecture to track both validation results and imported strings.

**Base Path**: `/api/v1/workspaces/{workspace_id}/string-registry/`

---

## Architecture

### Dual-Model System

1. **ExternalString** - Stores ALL uploaded strings (valid + invalid) with validation results
2. **String** - Stores only VALID strings that have been imported to projects

### Workflows

#### Workflow 1: Validate Only
```
CSV Upload → Validate → Create ExternalStrings → Review → Import Selected
```

#### Workflow 2: Direct Import
```
CSV Upload → Validate → Create ExternalStrings + Strings (valid only)
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/validate/` | Validate CSV without importing |
| POST | `/import/` | Validate and import to project |
| POST | `/import-selected/` | Import specific ExternalStrings |
| POST | `/validate_single/` | Validate single string (no DB storage) |

---

## CSV Format

All CSV upload endpoints require this format:

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `string_value` | The naming string to validate | `ACME-2024-US-Q4-Awareness` |
| `external_platform_id` | Platform's unique identifier | `campaign_123456` |
| `entity_name` | Entity type (campaign, ad_group, ad) | `campaign` |
| `parent_external_id` | Parent's platform ID (optional for root) | `account_999` |

### Example CSV

```csv
string_value,external_platform_id,entity_name,parent_external_id
ACME-2024,account_999,account,
ACME-2024-US-Q4-Awareness,campaign_123,campaign,account_999
ACME-2024-US-Q4-Awareness-BrandAwareness,adgroup_456,ad_group,campaign_123
```

### File Requirements

- **Format**: CSV (UTF-8 encoded)
- **Max Size**: 5 MB
- **Max Rows**: 1,000 rows per upload
- **Required Headers**: Must include all 4 columns
- **Empty Values**: Use empty string for optional `parent_external_id`

---

## Validate Only

**POST** `/api/v1/workspaces/{workspace_id}/string-registry/validate/`

Validate strings without importing to a project. Creates ExternalString records for tracking.

### Use Cases

- **Quality Check**: Validate before deciding which strings to import
- **Audit**: Track validation history without cluttering projects
- **Selective Import**: Review results, then import specific strings later

### Request (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | CSV file |
| `platform_id` | integer | Yes | Platform ID |
| `rule_id` | integer | Yes | Rule to validate against |

### Example Request

```bash
curl -X POST \
  'http://localhost:8000/api/v1/workspaces/1/string-registry/validate/' \
  -H 'Authorization: Bearer <token>' \
  -F 'file=@strings.csv' \
  -F 'platform_id=1' \
  -F 'rule_id=5'
```

### Example Response (200 OK)

```json
{
  "success": true,
  "batch_id": 42,
  "operation_type": "validation",
  "summary": {
    "total_rows": 3,
    "uploaded_rows": 3,
    "processed_rows": 3,
    "skipped_rows": 0,
    "created": 3,
    "valid": 2,
    "warnings": 1,
    "failed": 0
  },
  "results": [
    {
      "row_number": 2,
      "string_value": "ACME-2024",
      "external_platform_id": "account_999",
      "entity_name": "account",
      "parent_external_id": null,
      "validation_status": "valid",
      "external_string_id": 101,
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 3,
      "string_value": "ACME-2024-US-Q4-Awareness",
      "external_platform_id": "campaign_123",
      "entity_name": "campaign",
      "parent_external_id": "account_999",
      "validation_status": "valid",
      "external_string_id": 102,
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 4,
      "string_value": "ACME-2024-US-Q4-Awareness-Premium",
      "external_platform_id": "adgroup_456",
      "entity_name": "ad_group",
      "parent_external_id": "campaign_123",
      "validation_status": "warning",
      "external_string_id": 103,
      "errors": [],
      "warnings": [
        {
          "type": "optional_dimension_missing",
          "field": "targeting",
          "message": "Optional dimension 'targeting' not found in string"
        }
      ]
    }
  ]
}
```

### Validation Status Types

| Status | Meaning | Can Import? |
|--------|---------|-------------|
| `valid` | Passes all validations | ✅ Yes |
| `warning` | Passes required, missing optional | ✅ Yes |
| `invalid` | Fails validation | ❌ No |
| `entity_mismatch` | Entity doesn't match rule | ❌ No |
| `skipped` | Duplicate or system error | ❌ No |

### Error Types

| Type | Description |
|------|-------------|
| `invalid_dimension_value` | Dimension value not in allowed list |
| `required_dimension_missing` | Required dimension not found in string |
| `invalid_pattern` | String doesn't match rule pattern |
| `entity_mismatch` | Entity not compatible with rule |
| `parent_not_found` | Parent string doesn't exist |
| `parent_entity_mismatch` | Parent entity incompatible |

---

## Import to Project

**POST** `/api/v1/workspaces/{workspace_id}/string-registry/import/`

Validate AND import valid strings to a project in one operation.

### Use Cases

- **Bulk Import**: Import all valid strings from platform export
- **Migration**: Migrate existing campaign structures
- **Sync**: Keep Tuxonomy in sync with platform

### Request (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | CSV file |
| `project_id` | integer | Yes | Target project ID |
| `platform_id` | integer | Yes | Platform ID (must be assigned to project) |
| `rule_id` | integer | Yes | Rule to validate against |

### Example Request

```bash
curl -X POST \
  'http://localhost:8000/api/v1/workspaces/1/string-registry/import/' \
  -H 'Authorization: Bearer <token>' \
  -F 'file=@strings.csv' \
  -F 'project_id=10' \
  -F 'platform_id=1' \
  -F 'rule_id=5'
```

### Example Response (200 OK)

```json
{
  "success": true,
  "batch_id": 43,
  "operation_type": "import",
  "project": {
    "id": 10,
    "name": "Q4 2024 Campaign"
  },
  "summary": {
    "total_rows": 3,
    "uploaded_rows": 3,
    "processed_rows": 3,
    "skipped_rows": 0,
    "created": 2,
    "updated": 0,
    "valid": 2,
    "warnings": 0,
    "failed": 1
  },
  "results": [
    {
      "row_number": 2,
      "string_value": "ACME-2024",
      "external_platform_id": "account_999",
      "entity_name": "account",
      "validation_status": "valid",
      "external_string_id": 201,
      "string_id": 301,
      "import_status": "imported",
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 3,
      "string_value": "ACME-2024-US-Q4-Awareness",
      "external_platform_id": "campaign_123",
      "entity_name": "campaign",
      "validation_status": "valid",
      "external_string_id": 202,
      "string_id": 302,
      "import_status": "imported",
      "errors": [],
      "warnings": []
    },
    {
      "row_number": 4,
      "string_value": "INVALID-Q4-Awareness",
      "external_platform_id": "campaign_456",
      "entity_name": "campaign",
      "validation_status": "invalid",
      "external_string_id": 203,
      "string_id": null,
      "import_status": "failed",
      "errors": [
        {
          "type": "invalid_dimension_value",
          "field": "region",
          "message": "Value 'INVALID' not valid for dimension 'region'",
          "expected": ["US", "EU", "APAC"],
          "received": "INVALID"
        }
      ],
      "warnings": []
    }
  ]
}
```

### Validation Rules

- ✅ Platform must be assigned to project
- ✅ Rule must belong to platform
- ✅ All parent strings must exist before children
- ✅ Entity must be compatible with rule

---

## Import Selected Strings

**POST** `/api/v1/workspaces/{workspace_id}/string-registry/import-selected/`

Import specific ExternalStrings (by ID) to a project.

### Use Case

After validating with `/validate/`, selectively import only specific strings based on review.

### Request Body (JSON)

```json
{
  "project_id": 10,
  "external_string_ids": [101, 102, 105, 108]
}
```

### Example Response (200 OK)

```json
{
  "success": true,
  "summary": {
    "requested": 4,
    "imported": 3,
    "updated": 0,
    "failed": 0,
    "already_imported": 1
  },
  "results": [
    {
      "external_string_id": 101,
      "external_platform_id": "account_999",
      "string_id": 401,
      "status": "imported",
      "message": "Successfully imported to project"
    },
    {
      "external_string_id": 102,
      "external_platform_id": "campaign_123",
      "string_id": 402,
      "status": "imported",
      "message": "Successfully imported to project"
    },
    {
      "external_string_id": 105,
      "external_platform_id": "campaign_789",
      "string_id": 403,
      "status": "imported",
      "message": "Successfully imported to project"
    },
    {
      "external_string_id": 108,
      "external_platform_id": "adgroup_456",
      "string_id": 350,
      "status": "already_imported",
      "message": "String was already imported on 2024-11-01T14:00:00Z"
    }
  ]
}
```

### Import Status

| Status | Meaning |
|--------|---------|
| `imported` | Successfully imported |
| `updated` | Existing String updated |
| `already_imported` | Already imported previously |
| `failed` | Import failed (see message) |

### Error Conditions

- ExternalString doesn't exist
- ExternalString has invalid status (cannot import)
- Platform not assigned to project
- Parent string not found in project

---

## Validate Single String

**POST** `/api/v1/workspaces/{workspace_id}/string-registry/validate_single/`

Validate a single string without creating database records.

### Use Cases

- **Real-time UI Validation**: Validate as user types
- **Testing**: Test rule patterns
- **Preview**: See validation result before bulk upload

### Request Body (JSON)

```json
{
  "platform_id": 1,
  "rule_id": 5,
  "entity_name": "campaign",
  "string_value": "ACME-2024-US-Q4-Awareness",
  "external_platform_id": "campaign_test_123",
  "parent_external_id": "account_999"
}
```

### Example Response (200 OK)

```json
{
  "is_valid": true,
  "entity": {
    "id": 3,
    "name": "campaign",
    "entity_level": 1
  },
  "parsed_dimension_values": {
    "client": "ACME",
    "year": "2024",
    "region": "US",
    "quarter": "Q4",
    "objective": "Awareness"
  },
  "errors": [],
  "warnings": [],
  "expected_string": "ACME-2024-US-Q4-Awareness",
  "should_skip": false
}
```

### Invalid String Response

```json
{
  "is_valid": false,
  "entity": {
    "id": 3,
    "name": "campaign",
    "entity_level": 1
  },
  "parsed_dimension_values": {
    "client": "ACME",
    "year": "2024",
    "region": "INVALID",
    "quarter": "Q4",
    "objective": "Awareness"
  },
  "errors": [
    {
      "type": "invalid_dimension_value",
      "field": "region",
      "message": "Value 'INVALID' not valid for dimension 'region'",
      "expected": ["US", "EU", "APAC"],
      "received": "INVALID"
    }
  ],
  "warnings": [],
  "expected_string": null,
  "should_skip": false
}
```

---

## Frontend Integration Examples

### Upload CSV for Validation

```javascript
async function validateStrings(workspaceId, formData) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/string-registry/validate/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData // FormData with file, platform_id, rule_id
    }
  );

  return await response.json();
}

// Usage
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('platform_id', '1');
formData.append('rule_id', '5');

const result = await validateStrings(1, formData);
console.log(`Valid: ${result.summary.valid}, Failed: ${result.summary.failed}`);
```

### Import with Progress Tracking

```javascript
async function importStrings(workspaceId, projectId, formData, onProgress) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/string-registry/import/`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    }
  );

  const result = await response.json();

  // Show progress
  onProgress({
    total: result.summary.total_rows,
    imported: result.summary.created,
    failed: result.summary.failed
  });

  return result;
}

// Usage
await importStrings(1, 10, formData, (progress) => {
  updateProgressBar(progress.imported / progress.total * 100);
});
```

### Selective Import UI

```javascript
async function importSelectedStrings(workspaceId, projectId, externalStringIds) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/string-registry/import-selected/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        project_id: projectId,
        external_string_ids: externalStringIds
      })
    }
  );

  return await response.json();
}

// Usage: User selects strings from validation results
const selectedIds = checkedRows.map(row => row.external_string_id);
const result = await importSelectedStrings(1, 10, selectedIds);
showNotification(`Imported ${result.summary.imported} strings`);
```

### Real-time String Validation

```javascript
import { debounce } from 'lodash';

const validateStringDebounced = debounce(async (stringValue) => {
  if (!stringValue) return;

  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/string-registry/validate_single/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform_id: platformId,
        rule_id: ruleId,
        entity_name: entityName,
        string_value: stringValue,
        external_platform_id: `test_${Date.now()}`
      })
    }
  );

  const result = await response.json();

  if (result.is_valid) {
    showSuccess('Valid string');
  } else {
    showErrors(result.errors);
  }
}, 500);

// Usage: Validate as user types
stringInput.addEventListener('input', (e) => {
  validateStringDebounced(e.target.value);
});
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/validate/` | 10 uploads per hour |
| `/import/` | 10 uploads per hour |
| `/import-selected/` | 100 requests per hour |
| `/validate_single/` | 100 requests per hour |

---

## Best Practices

### 1. Validate Before Import

```javascript
// Step 1: Validate first
const validationResult = await validateStrings(workspaceId, formData);

// Step 2: Review results
if (validationResult.summary.failed > 0) {
  showReviewDialog(validationResult.results);
} else {
  // Step 3: Import if all valid
  await importStrings(workspaceId, projectId, formData);
}
```

### 2. Handle Large Uploads

```javascript
// Split large CSVs into chunks
const CHUNK_SIZE = 500;
const chunks = splitCSV(csvData, CHUNK_SIZE);

for (const chunk of chunks) {
  const formData = createFormData(chunk);
  await validateStrings(workspaceId, formData);
  await delay(1000); // Rate limit protection
}
```

### 3. Error Display

```javascript
function displayValidationErrors(results) {
  const errorsByType = {};

  results.forEach(row => {
    row.errors.forEach(error => {
      if (!errorsByType[error.type]) {
        errorsByType[error.type] = [];
      }
      errorsByType[error.type].push({
        row: row.row_number,
        value: row.string_value,
        message: error.message
      });
    });
  });

  // Group and display errors
  Object.entries(errorsByType).forEach(([type, errors]) => {
    console.group(`${type} (${errors.length} errors)`);
    errors.forEach(e => console.log(`Row ${e.row}: ${e.message}`));
    console.groupEnd();
  });
}
```

### 4. Batch Processing

```javascript
// Process validation batch
const batch = await validateStrings(workspaceId, formData);

// Filter valid strings
const validIds = batch.results
  .filter(r => r.validation_status === 'valid')
  .map(r => r.external_string_id);

// Import only valid strings
if (validIds.length > 0) {
  await importSelectedStrings(workspaceId, projectId, validIds);
}
```
