# Strings API

Strings are the core naming convention objects in Tuxonomy. Each string represents a generated name for a marketing resource (campaign, ad group, ad, etc.) within a project.

**Base Path**: `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/`

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/strings` | List strings for a platform in project |
| POST | `/strings/bulk` | Create multiple strings |
| GET | `/strings/{id}/expanded` | Get string with full details |
| PUT | `/strings/{id}` | Update string |
| DELETE | `/strings/{id}/delete` | Delete string |
| POST | `/strings/{id}/unlock` | Unlock approved string |
| POST | `/strings/bulk-update` | Bulk update multiple strings |
| GET | `/strings/export` | Export strings to CSV/JSON |

---

## Data Models

### String Object

```json
{
  "id": 501,
  "string_uuid": "abc123-def456-ghi789",
  "value": "ACME-2024-US-Q4-Awareness",
  "project": 10,
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "platform_type": "meta"
  },
  "entity": {
    "id": 3,
    "name": "campaign",
    "entity_level": 1
  },
  "rule": {
    "id": 5,
    "name": "Campaign Naming Rule"
  },
  "parent_uuid": "abc123-def456-xyz999",
  "external_platform_id": "campaign_meta_12345",
  "external_parent_id": "account_meta_999",
  "validation_source": "internal",
  "sync_status": "synced",
  "is_locked": false,
  "created_by": {
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "created": "2024-11-05T12:00:00Z",
  "last_updated": "2024-11-10T14:30:00Z"
}
```

### String Detail Object

```json
{
  "id": 1001,
  "dimension": {
    "id": 1,
    "name": "region",
    "type": "text"
  },
  "dimension_value": {
    "id": 10,
    "value": "US",
    "label": "United States"
  },
  "dimension_value_freetext": null,
  "is_inherited": false
}
```

### Validation Source

- `internal` - Created within Tuxonomy
- `external` - Imported from external platform

### Sync Status

- `synced` - In sync with parent
- `out_of_sync` - Parent changed, needs update
- `conflict` - Manual changes conflict with parent

---

## List Strings

**GET** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings`

Get all strings for a specific platform within a project.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | integer | Filter by entity |
| `search` | string | Search in string values |
| `validation_source` | string | Filter by: `internal` or `external` |
| `sync_status` | string | Filter by sync status |
| `is_locked` | boolean | Filter locked/unlocked strings |
| `external_platform_id` | string | Filter by external platform ID |
| `page` | integer | Page number |
| `page_size` | integer | Results per page (max: 100) |

### Example Request

```bash
GET /api/v1/workspaces/1/projects/10/platforms/1/strings?entity_id=3&page_size=50
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
{
  "count": 125,
  "next": "http://api.tuxonomy.com/api/v1/.../strings?page=2",
  "previous": null,
  "results": [
    {
      "id": 501,
      "string_uuid": "abc123-def456-ghi789",
      "value": "ACME-2024-US-Q4-Awareness",
      "project": 10,
      "platform": {...},
      "entity": {...},
      "rule": {...},
      "parent_uuid": null,
      "is_locked": false,
      "created": "2024-11-05T12:00:00Z",
      "last_updated": "2024-11-10T14:30:00Z"
    }
  ]
}
```

---

## Create Strings (Bulk)

**POST** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/bulk`

Create multiple strings at once.

### Request Body

```json
{
  "strings": [
    {
      "entity_id": 3,
      "rule_id": 5,
      "parent_uuid": null,
      "external_platform_id": "campaign_meta_12345",
      "details": [
        {
          "dimension_id": 1,
          "dimension_value_id": 10
        },
        {
          "dimension_id": 2,
          "dimension_value_freetext": "Q4"
        },
        {
          "dimension_id": 3,
          "dimension_value_id": 25
        }
      ]
    },
    {
      "entity_id": 4,
      "rule_id": 6,
      "parent_uuid": "abc123-def456-ghi789",
      "external_platform_id": "adgroup_meta_67890",
      "details": [...]
    }
  ]
}
```

### Field Requirements

**String Level**:
- `entity_id`: Required
- `rule_id`: Required
- `parent_uuid`: Optional (null for root-level entities)
- `external_platform_id`: Optional (for external tracking)
- `details`: Required, array of dimension values

**Detail Level**:
- `dimension_id`: Required
- `dimension_value_id`: Required if dimension type is `select` or `multi_select`
- `dimension_value_freetext`: Required if dimension type is `text` or `number`

### Example Response (201 Created)

```json
{
  "success": true,
  "created_count": 2,
  "failed_count": 0,
  "results": [
    {
      "id": 501,
      "string_uuid": "abc123-def456-ghi789",
      "value": "ACME-2024-US-Q4-Awareness",
      "status": "created"
    },
    {
      "id": 502,
      "string_uuid": "def456-ghi789-jkl012",
      "value": "ACME-2024-US-Q4-Awareness-BrandAwareness",
      "status": "created"
    }
  ],
  "errors": []
}
```

### Error Response (400 Bad Request)

```json
{
  "errors": [
    {
      "index": 0,
      "field": "details.0.dimension_value_id",
      "message": "Dimension value 999 not found for dimension 'region'"
    }
  ]
}
```

---

## Get String with Details

**GET** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{id}/expanded`

Get full string details including all dimension values.

### Example Response (200 OK)

```json
{
  "id": 501,
  "string_uuid": "abc123-def456-ghi789",
  "value": "ACME-2024-US-Q4-Awareness",
  "project": 10,
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "platform_type": "meta"
  },
  "entity": {
    "id": 3,
    "name": "campaign",
    "entity_level": 1
  },
  "rule": {
    "id": 5,
    "name": "Campaign Naming Rule",
    "pattern": "{client}-{year}-{region}-{quarter}-{objective}"
  },
  "parent": {
    "id": 499,
    "string_uuid": "xyz999-abc123-def456",
    "value": "ACME-2024"
  },
  "children": [
    {
      "id": 502,
      "string_uuid": "def456-ghi789-jkl012",
      "value": "ACME-2024-US-Q4-Awareness-BrandAwareness",
      "entity": "ad_group"
    }
  ],
  "details": [
    {
      "id": 1001,
      "dimension": {
        "id": 1,
        "name": "region",
        "type": "select"
      },
      "dimension_value": {
        "id": 10,
        "value": "US",
        "label": "United States"
      },
      "is_inherited": false
    },
    {
      "id": 1002,
      "dimension": {
        "id": 2,
        "name": "quarter",
        "type": "text"
      },
      "dimension_value": null,
      "dimension_value_freetext": "Q4",
      "is_inherited": false
    }
  ],
  "validation_source": "internal",
  "sync_status": "synced",
  "is_locked": false,
  "external_platform_id": "campaign_meta_12345",
  "external_parent_id": null,
  "created_by": {...},
  "created": "2024-11-05T12:00:00Z",
  "last_updated": "2024-11-10T14:30:00Z"
}
```

---

## Update String

**PUT** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{id}`

Update string dimension values. Cannot update locked strings.

### Request Body

```json
{
  "details": [
    {
      "dimension_id": 1,
      "dimension_value_id": 12
    },
    {
      "dimension_id": 2,
      "dimension_value_freetext": "Q1"
    }
  ]
}
```

### Example Response (200 OK)

Returns updated string object (same structure as GET expanded).

### Error Response (403 Forbidden)

```json
{
  "error": "Cannot update locked string. Use unlock endpoint first."
}
```

---

## Delete String

**DELETE** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{id}/delete`

Delete a string. **This also deletes all child strings in the hierarchy**.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cascade` | boolean | Delete children (default: true) |

### Example Response (200 OK)

```json
{
  "success": true,
  "deleted_count": 5,
  "message": "String and 4 children deleted successfully"
}
```

### Error Response (403 Forbidden)

```json
{
  "error": "Cannot delete locked string"
}
```

---

## Unlock String

**POST** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/{id}/unlock`

Unlock an approved string for editing.

### Request Body

```json
{
  "reason": "Need to correct region value"
}
```

### Example Response (200 OK)

```json
{
  "id": 501,
  "is_locked": false,
  "unlocked_by": {
    "id": 5,
    "name": "John Doe"
  },
  "unlocked_at": "2024-11-11T16:00:00Z",
  "unlock_reason": "Need to correct region value"
}
```

---

## Bulk Update Strings

**POST** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/bulk-update`

Update multiple strings at once.

### Request Body

```json
{
  "string_ids": [501, 502, 503],
  "updates": {
    "dimension_updates": [
      {
        "dimension_id": 1,
        "dimension_value_id": 15
      }
    ]
  }
}
```

### Example Response (200 OK)

```json
{
  "success": true,
  "updated_count": 3,
  "failed_count": 0,
  "results": [
    {
      "id": 501,
      "value": "ACME-2024-EU-Q4-Awareness",
      "status": "updated"
    },
    {
      "id": 502,
      "value": "ACME-2024-EU-Q4-Awareness-BrandAwareness",
      "status": "updated"
    },
    {
      "id": 503,
      "value": "ACME-2024-EU-Q4-Awareness-BrandConsideration",
      "status": "updated"
    }
  ]
}
```

---

## Export Strings

**GET** `/api/v1/workspaces/{workspace_id}/projects/{project_id}/platforms/{platform_id}/strings/export`

Export strings to CSV or JSON format.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | `csv` or `json` (default: csv) |
| `entity_id` | integer | Filter by entity |
| `validation_source` | string | Filter by source |
| `include_details` | boolean | Include dimension details (default: true) |

### Example Request

```bash
GET /api/v1/workspaces/1/projects/10/platforms/1/strings/export?format=csv
Authorization: Bearer <token>
```

### CSV Response

```csv
id,string_uuid,value,entity,parent_uuid,external_platform_id,region,quarter,objective,created
501,abc123...,ACME-2024-US-Q4-Awareness,campaign,,campaign_meta_12345,US,Q4,Awareness,2024-11-05T12:00:00Z
502,def456...,ACME-2024-US-Q4-Awareness-BrandAwareness,ad_group,abc123...,adgroup_meta_67890,US,Q4,Brand Awareness,2024-11-05T13:00:00Z
```

---

## Frontend Integration Examples

### Fetch String List

```javascript
async function fetchStrings(workspaceId, projectId, platformId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings?${params}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
}

// Usage
const strings = await fetchStrings(1, 10, 1, {
  entity_id: 3,
  page_size: 100
});
```

### Create Strings

```javascript
async function createStrings(workspaceId, projectId, platformId, stringsData) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/bulk`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ strings: stringsData })
    }
  );

  if (!response.ok) {
    const errors = await response.json();
    throw new Error(JSON.stringify(errors));
  }

  return await response.json();
}

// Usage
const result = await createStrings(1, 10, 1, [
  {
    entity_id: 3,
    rule_id: 5,
    details: [
      { dimension_id: 1, dimension_value_id: 10 },
      { dimension_id: 2, dimension_value_freetext: 'Q4' }
    ]
  }
]);
```

### Update String

```javascript
async function updateString(workspaceId, projectId, platformId, stringId, updates) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );

  return await response.json();
}

// Usage
await updateString(1, 10, 1, 501, {
  details: [
    { dimension_id: 1, dimension_value_id: 15 }
  ]
});
```

### Export Strings

```javascript
async function exportStrings(workspaceId, projectId, platformId, format = 'csv') {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/export?format=${format}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  if (format === 'csv') {
    const blob = await response.blob();
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `strings-export-${Date.now()}.csv`;
    a.click();
  } else {
    return await response.json();
  }
}

// Usage
await exportStrings(1, 10, 1, 'csv');
```

---

## Common Workflows

### 1. String Hierarchy Builder

```javascript
// Create parent (campaign)
const parentResult = await createStrings(workspaceId, projectId, platformId, [
  {
    entity_id: campaignEntityId,
    rule_id: campaignRuleId,
    parent_uuid: null,
    details: campaignDimensions
  }
]);

const parentUuid = parentResult.results[0].string_uuid;

// Create children (ad groups)
const childrenResult = await createStrings(workspaceId, projectId, platformId, [
  {
    entity_id: adGroupEntityId,
    rule_id: adGroupRuleId,
    parent_uuid: parentUuid,
    details: adGroupDimensions
  }
]);
```

### 2. Bulk Region Update

```javascript
// Get all strings for platform
const { results: strings } = await fetchStrings(workspaceId, projectId, platformId);

// Filter strings by entity
const campaignIds = strings
  .filter(s => s.entity.name === 'campaign')
  .map(s => s.id);

// Update region for all campaigns
await bulkUpdateStrings(workspaceId, projectId, platformId, {
  string_ids: campaignIds,
  updates: {
    dimension_updates: [
      { dimension_id: regionDimensionId, dimension_value_id: newRegionId }
    ]
  }
});
```

### 3. String Validation Display

```javascript
// Fetch string with full details
const stringData = await fetch(
  `${API_BASE}/workspaces/${workspaceId}/projects/${projectId}/platforms/${platformId}/strings/${stringId}/expanded`,
  { headers: { 'Authorization': `Bearer ${token}` } }
).then(r => r.json());

// Display validation status
if (stringData.sync_status === 'out_of_sync') {
  showWarning('String is out of sync with parent');
} else if (stringData.validation_source === 'external') {
  showInfo('String imported from external platform');
}
```
