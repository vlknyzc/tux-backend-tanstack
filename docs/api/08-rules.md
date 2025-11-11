# Rules API

Rules define naming patterns for entities. They combine dimensions into structured naming conventions (e.g., `{client}-{year}-{region}-{quarter}-{objective}` for campaigns).

**Base Path**: `/api/v1/workspaces/{workspace_id}/rules/`

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rules/` | List all rules |
| POST | `/rules/` | Create rule |
| GET | `/rules/{id}/` | Get rule details |
| PATCH | `/rules/{id}/` | Update rule |
| DELETE | `/rules/{id}/` | Delete rule |
| POST | `/rules/{id}/validation/` | Validate rule pattern |
| POST | `/rules/generation-preview/` | Preview string generation |

---

## Data Models

### Rule Object

```json
{
  "id": 5,
  "name": "Campaign Naming Rule",
  "description": "Naming convention for Meta campaign entities",
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "platform_type": "meta"
  },
  "pattern": "{client}-{year}-{region}-{quarter}-{objective}",
  "separator": "-",
  "is_active": true,
  "details": [
    {
      "id": 101,
      "entity": {
        "id": 2,
        "name": "campaign",
        "entity_level": 1
      },
      "dimension": {
        "id": 1,
        "name": "region",
        "type": "select"
      },
      "order": 3,
      "is_required": true,
      "can_inherit": false
    },
    {
      "id": 102,
      "entity": {
        "id": 2,
        "name": "campaign",
        "entity_level": 1
      },
      "dimension": {
        "id": 2,
        "name": "quarter",
        "type": "text"
      },
      "order": 4,
      "is_required": true,
      "can_inherit": false
    }
  ],
  "entities": [
    {
      "id": 2,
      "name": "campaign",
      "entity_level": 1
    }
  ],
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-11-05T14:30:00Z",
  "created_by": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@example.com"
  }
}
```

### Rule Detail Object

```json
{
  "id": 101,
  "rule": 5,
  "entity": {
    "id": 2,
    "name": "campaign",
    "entity_level": 1
  },
  "dimension": {
    "id": 1,
    "name": "region",
    "type": "select",
    "values": [...]
  },
  "order": 3,
  "is_required": true,
  "can_inherit": false,
  "default_value": null
}
```

---

## List Rules

**GET** `/api/v1/workspaces/{workspace_id}/rules/`

Get all rules in a workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform_id` | integer | Filter by platform |
| `entity_id` | integer | Filter rules for specific entity |
| `is_active` | boolean | Filter active/inactive |
| `search` | string | Search by name or pattern |

### Example Request

```bash
GET /api/v1/workspaces/1/rules/?platform_id=1&is_active=true
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
[
  {
    "id": 5,
    "name": "Campaign Naming Rule",
    "description": "Naming convention for Meta campaigns",
    "platform": {...},
    "pattern": "{client}-{year}-{region}-{quarter}-{objective}",
    "separator": "-",
    "is_active": true,
    "entities_count": 1,
    "dimensions_count": 5,
    "created": "2024-01-15T10:00:00Z"
  },
  {
    "id": 6,
    "name": "Ad Set Naming Rule",
    "description": "Naming convention for Meta ad sets",
    "platform": {...},
    "pattern": "{parent}-{audience}-{placement}",
    "separator": "-",
    "is_active": true,
    "entities_count": 1,
    "dimensions_count": 3,
    "created": "2024-01-15T10:30:00Z"
  }
]
```

---

## Create Rule

**POST** `/api/v1/workspaces/{workspace_id}/rules/`

Create a new naming rule.

### Request Body

```json
{
  "name": "Ad Group Naming Rule",
  "description": "Naming rule for Google Ads ad groups",
  "platform_id": 2,
  "pattern": "{parent}-{audience}-{bidstrategy}",
  "separator": "-",
  "is_active": true,
  "details": [
    {
      "entity_id": 4,
      "dimension_id": 8,
      "order": 1,
      "is_required": true,
      "can_inherit": false
    },
    {
      "entity_id": 4,
      "dimension_id": 9,
      "order": 2,
      "is_required": true,
      "can_inherit": false
    }
  ]
}
```

### Validation Rules

- `name`: Required, max 200 characters, unique per workspace
- `platform_id`: Required, must be valid platform
- `pattern`: Required, must include placeholders matching dimensions
- `separator`: Optional, default: `-`
- `details`: Required, at least one dimension

### Example Response (201 Created)

```json
{
  "id": 15,
  "name": "Ad Group Naming Rule",
  "description": "Naming rule for Google Ads ad groups",
  "platform": {...},
  "pattern": "{parent}-{audience}-{bidstrategy}",
  "separator": "-",
  "is_active": true,
  "details": [...],
  "entities": [...],
  "created": "2024-11-11T10:00:00Z",
  "last_updated": "2024-11-11T10:00:00Z"
}
```

---

## Get Rule Details

**GET** `/api/v1/workspaces/{workspace_id}/rules/{id}/`

Get full rule details including all dimensions and configurations.

### Example Response (200 OK)

```json
{
  "id": 5,
  "name": "Campaign Naming Rule",
  "description": "Naming convention for Meta campaign entities",
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "platform_type": "meta"
  },
  "pattern": "{client}-{year}-{region}-{quarter}-{objective}",
  "separator": "-",
  "is_active": true,
  "details": [
    {
      "id": 101,
      "entity": {
        "id": 2,
        "name": "campaign",
        "entity_level": 1
      },
      "dimension": {
        "id": 1,
        "name": "region",
        "type": "select",
        "values": [
          {"id": 10, "value": "US", "label": "United States"},
          {"id": 11, "value": "EU", "label": "Europe"}
        ]
      },
      "order": 3,
      "is_required": true,
      "can_inherit": false
    }
  ],
  "sample_strings": [
    "ACME-2024-US-Q4-Awareness",
    "ACME-2024-EU-Q3-Conversion"
  ],
  "usage_count": 45,
  "created": "2024-01-15T10:00:00Z",
  "last_updated": "2024-11-05T14:30:00Z"
}
```

---

## Update Rule

**PATCH** `/api/v1/workspaces/{workspace_id}/rules/{id}/`

Update rule properties. **Note**: Changing patterns affects existing strings.

### Request Body (Partial Update)

```json
{
  "description": "Updated description",
  "is_active": false
}
```

### Example Response (200 OK)

Returns updated rule object.

### Warning

Changing `pattern` or `details` affects existing strings and may trigger propagation updates.

---

## Delete Rule

**DELETE** `/api/v1/workspaces/{workspace_id}/rules/{id}/`

Delete a rule. **Cannot delete if used in active strings**.

### Example Response (204 No Content)

No response body.

### Error Response (400 Bad Request)

```json
{
  "error": "Cannot delete rule with active strings",
  "strings_count": 45
}
```

---

## Validate Rule Pattern

**POST** `/api/v1/workspaces/{workspace_id}/rules/{id}/validation/`

Validate that a rule pattern is correctly formatted and all dimensions exist.

### Request Body

```json
{
  "pattern": "{client}-{year}-{region}-{quarter}-{objective}",
  "details": [
    {"dimension_id": 1, "entity_id": 2},
    {"dimension_id": 2, "entity_id": 2}
  ]
}
```

### Example Response (200 OK)

```json
{
  "is_valid": true,
  "parsed_pattern": [
    {"type": "dimension", "name": "client", "position": 0},
    {"type": "separator", "value": "-", "position": 1},
    {"type": "dimension", "name": "year", "position": 2},
    {"type": "separator", "value": "-", "position": 3},
    {"type": "dimension", "name": "region", "position": 4}
  ],
  "errors": [],
  "warnings": []
}
```

### Invalid Pattern Response

```json
{
  "is_valid": false,
  "parsed_pattern": [],
  "errors": [
    {
      "type": "dimension_not_found",
      "message": "Dimension 'invalid_dimension' not found in rule details",
      "field": "invalid_dimension"
    }
  ],
  "warnings": []
}
```

---

## Preview String Generation

**POST** `/api/v1/workspaces/{workspace_id}/rules/generation-preview/`

Preview how strings will be generated with given dimension values.

### Request Body

```json
{
  "rule_id": 5,
  "entity_id": 2,
  "dimension_values": {
    "region": "US",
    "quarter": "Q4",
    "objective": "Awareness"
  }
}
```

### Example Response (200 OK)

```json
{
  "success": true,
  "generated_string": "ACME-2024-US-Q4-Awareness",
  "rule": {
    "id": 5,
    "name": "Campaign Naming Rule",
    "pattern": "{client}-{year}-{region}-{quarter}-{objective}"
  },
  "dimension_breakdown": {
    "client": {
      "value": "ACME",
      "source": "default"
    },
    "year": {
      "value": "2024",
      "source": "system"
    },
    "region": {
      "value": "US",
      "source": "user_input"
    },
    "quarter": {
      "value": "Q4",
      "source": "user_input"
    },
    "objective": {
      "value": "Awareness",
      "source": "user_input"
    }
  },
  "warnings": []
}
```

---

## Frontend Integration Examples

### Fetch Rules

```javascript
async function fetchRules(workspaceId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/rules/?${params}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
}

// Usage
const rules = await fetchRules(1, { platform_id: 1, is_active: true });
```

### Rule Builder Form

```javascript
async function createRule(workspaceId, ruleData) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/rules/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(ruleData)
    }
  );

  if (!response.ok) {
    const errors = await response.json();
    throw new Error(JSON.stringify(errors));
  }

  return await response.json();
}

// Usage
const newRule = await createRule(1, {
  name: 'My Naming Rule',
  platform_id: 1,
  pattern: '{client}-{year}-{region}',
  details: [
    { entity_id: 2, dimension_id: 1, order: 1, is_required: true }
  ]
});
```

### Live Preview

```javascript
async function previewString(workspaceId, ruleId, dimensionValues) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/rules/generation-preview/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        rule_id: ruleId,
        entity_id: entityId,
        dimension_values: dimensionValues
      })
    }
  );

  return await response.json();
}

// Usage: Real-time preview as user fills form
const preview = await previewString(1, 5, {
  region: 'US',
  quarter: 'Q4',
  objective: 'Awareness'
});

displayPreview(preview.generated_string); // "ACME-2024-US-Q4-Awareness"
```

---

## Common Use Cases

### 1. Rule Selection by Entity

```javascript
async function getRulesForEntity(workspaceId, platformId, entityId) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/rules/?platform_id=${platformId}&entity_id=${entityId}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  const rules = await response.json();
  return rules.filter(r => r.is_active);
}

// Usage: When user selects entity, show applicable rules
const campaignRules = await getRulesForEntity(1, 1, 2);
```

### 2. Pattern Validation

```javascript
async function validatePattern(workspaceId, ruleId, pattern, details) {
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/rules/${ruleId}/validation/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ pattern, details })
    }
  );

  const result = await response.json();

  if (!result.is_valid) {
    showErrors(result.errors);
  }

  return result.is_valid;
}
```

### 3. Rule with Dimension Details UI

```javascript
function RuleDetails({ rule }) {
  return (
    <div>
      <h2>{rule.name}</h2>
      <p>Pattern: <code>{rule.pattern}</code></p>

      <h3>Dimensions</h3>
      <table>
        <thead>
          <tr>
            <th>Order</th>
            <th>Dimension</th>
            <th>Type</th>
            <th>Required</th>
            <th>Can Inherit</th>
          </tr>
        </thead>
        <tbody>
          {rule.details.map(detail => (
            <tr key={detail.id}>
              <td>{detail.order}</td>
              <td>{detail.dimension.name}</td>
              <td>{detail.dimension.type}</td>
              <td>{detail.is_required ? 'Yes' : 'No'}</td>
              <td>{detail.can_inherit ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Sample Strings</h3>
      <ul>
        {rule.sample_strings.map((str, i) => (
          <li key={i}><code>{str}</code></li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Pattern Syntax

### Placeholders

- Use `{dimension_name}` for dimension values
- Use literal text for fixed parts
- Separator is configurable (default: `-`)

### Examples

```
{client}-{year}-{region}-{quarter}-{objective}
→ ACME-2024-US-Q4-Awareness

{parent}-{audience}-{placement}
→ ACME-2024-US-Q4-Awareness-Millennials-Feed

{brand}_{region}_{year}_{quarter}
→ ACME_US_2024_Q4
```

### Special Placeholders

- `{parent}` - Inherits full parent string
- `{year}` - Auto-populated with current year (if dimension exists)
- `{quarter}` - Auto-populated with current quarter (if dimension exists)

---

## Notes

- Rules are platform-specific
- Multiple rules can target the same entity
- Changing active rules triggers string regeneration/updates
- Pattern validation occurs before rule creation
- Rules support inheritance from parent entities via `{parent}` placeholder
