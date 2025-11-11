# Dimensions API

Dimensions are the building blocks of naming rules. They represent categorical or freeform values that make up a naming string (e.g., region, quarter, objective).

**Base Path**: `/api/v1/workspaces/{workspace_id}/dimensions/`

---

## Endpoints Overview

### Dimensions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dimensions/` | List all dimensions |
| POST | `/dimensions/` | Create dimension |
| GET | `/dimensions/{id}/` | Get dimension details |
| PATCH | `/dimensions/{id}/` | Update dimension |
| DELETE | `/dimensions/{id}/` | Delete dimension |

### Dimension Values
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dimension-values/` | List all dimension values |
| POST | `/dimension-values/` | Create dimension value |
| GET | `/dimension-values/{id}/` | Get value details |
| PATCH | `/dimension-values/{id}/` | Update value |
| DELETE | `/dimension-values/{id}/` | Delete value |

---

## Data Models

### Dimension Object

```json
{
  "id": 1,
  "name": "region",
  "description": "Geographic region for campaign targeting",
  "type": "select",
  "is_required": true,
  "is_active": true,
  "order": 3,
  "values": [
    {
      "id": 10,
      "value": "US",
      "label": "United States",
      "description": "United States market"
    },
    {
      "id": 11,
      "value": "EU",
      "label": "Europe",
      "description": "European Union market"
    },
    {
      "id": 12,
      "value": "APAC",
      "label": "Asia Pacific",
      "description": "Asia Pacific region"
    }
  ],
  "values_count": 3,
  "created": "2024-01-10T10:00:00Z",
  "last_updated": "2024-11-05T14:30:00Z"
}
```

### Dimension Value Object

```json
{
  "id": 10,
  "dimension": {
    "id": 1,
    "name": "region",
    "type": "select"
  },
  "value": "US",
  "label": "United States",
  "description": "United States market",
  "utm": "us",
  "valid_from": "2024-01-01",
  "valid_until": null,
  "is_active": true,
  "order": 1,
  "parent": null,
  "children": []
}
```

### Dimension Types

| Type | Description | Use Case |
|------|-------------|----------|
| `select` | Single selection from predefined values | Region, quarter, objective |
| `multi_select` | Multiple selections from predefined values | Target audiences |
| `text` | Free-form text input | Custom descriptors |
| `number` | Numeric input | Budget codes, IDs |

---

## List Dimensions

**GET** `/api/v1/workspaces/{workspace_id}/dimensions/`

Get all dimensions in a workspace.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by type |
| `is_required` | boolean | Filter required/optional |
| `is_active` | boolean | Filter active/inactive |
| `search` | string | Search by name |

### Example Request

```bash
GET /api/v1/workspaces/1/dimensions/?type=select&is_active=true
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
[
  {
    "id": 1,
    "name": "region",
    "description": "Geographic region",
    "type": "select",
    "is_required": true,
    "is_active": true,
    "order": 1,
    "values_count": 5,
    "created": "2024-01-10T10:00:00Z"
  },
  {
    "id": 2,
    "name": "quarter",
    "description": "Fiscal quarter",
    "type": "text",
    "is_required": true,
    "is_active": true,
    "order": 2,
    "values_count": 0,
    "created": "2024-01-10T10:05:00Z"
  }
]
```

---

## Create Dimension

**POST** `/api/v1/workspaces/{workspace_id}/dimensions/`

Create a new dimension.

### Request Body

```json
{
  "name": "objective",
  "description": "Campaign objective",
  "type": "select",
  "is_required": true,
  "is_active": true,
  "order": 4
}
```

### Validation Rules

- `name`: Required, max 100 characters, unique per workspace
- `type`: Required, one of: `select`, `multi_select`, `text`, `number`
- `is_required`: Optional, default: `false`
- `is_active`: Optional, default: `true`
- `order`: Optional, integer for display ordering

### Example Response (201 Created)

```json
{
  "id": 15,
  "name": "objective",
  "description": "Campaign objective",
  "type": "select",
  "is_required": true,
  "is_active": true,
  "order": 4,
  "values": [],
  "values_count": 0,
  "created": "2024-11-11T10:00:00Z",
  "last_updated": "2024-11-11T10:00:00Z"
}
```

---

## Get Dimension Details

**GET** `/api/v1/workspaces/{workspace_id}/dimensions/{id}/`

Get detailed dimension information including all values.

### Example Response (200 OK)

```json
{
  "id": 1,
  "name": "region",
  "description": "Geographic region for campaign targeting",
  "type": "select",
  "is_required": true,
  "is_active": true,
  "order": 3,
  "values": [
    {
      "id": 10,
      "value": "US",
      "label": "United States",
      "description": "United States market",
      "utm": "us",
      "valid_from": "2024-01-01",
      "valid_until": null,
      "is_active": true,
      "order": 1
    },
    {
      "id": 11,
      "value": "EU",
      "label": "Europe",
      "description": "European Union market",
      "utm": "eu",
      "valid_from": "2024-01-01",
      "valid_until": null,
      "is_active": true,
      "order": 2
    }
  ],
  "values_count": 2,
  "rules_using": [
    {
      "id": 5,
      "name": "Campaign Naming Rule",
      "platform": "Meta Ads"
    }
  ],
  "created": "2024-01-10T10:00:00Z",
  "last_updated": "2024-11-05T14:30:00Z"
}
```

---

## Update Dimension

**PATCH** `/api/v1/workspaces/{workspace_id}/dimensions/{id}/`

Update dimension properties.

### Request Body (Partial Update)

```json
{
  "description": "Updated description",
  "is_required": false,
  "order": 5
}
```

### Example Response (200 OK)

Returns updated dimension object.

---

## Delete Dimension

**DELETE** `/api/v1/workspaces/{workspace_id}/dimensions/{id}/`

Delete a dimension. **Cannot delete if used in active rules**.

### Example Response (204 No Content)

No response body.

### Error Response (400 Bad Request)

```json
{
  "error": "Cannot delete dimension used in active rules",
  "rules": [
    {
      "id": 5,
      "name": "Campaign Naming Rule"
    }
  ]
}
```

---

## List Dimension Values

**GET** `/api/v1/workspaces/{workspace_id}/dimension-values/`

Get all dimension values or filter by dimension.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `dimension_id` | integer | Filter by dimension |
| `is_active` | boolean | Filter active/inactive |
| `search` | string | Search by value or label |

### Example Request

```bash
GET /api/v1/workspaces/1/dimension-values/?dimension_id=1
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
[
  {
    "id": 10,
    "dimension": {
      "id": 1,
      "name": "region",
      "type": "select"
    },
    "value": "US",
    "label": "United States",
    "description": "United States market",
    "utm": "us",
    "valid_from": "2024-01-01",
    "valid_until": null,
    "is_active": true,
    "order": 1
  }
]
```

---

## Create Dimension Value

**POST** `/api/v1/workspaces/{workspace_id}/dimension-values/`

Add a new value to a dimension.

### Request Body

```json
{
  "dimension_id": 1,
  "value": "LATAM",
  "label": "Latin America",
  "description": "Latin American market",
  "utm": "latam",
  "valid_from": "2024-11-01",
  "is_active": true,
  "order": 4
}
```

### Example Response (201 Created)

```json
{
  "id": 25,
  "dimension": {
    "id": 1,
    "name": "region",
    "type": "select"
  },
  "value": "LATAM",
  "label": "Latin America",
  "description": "Latin American market",
  "utm": "latam",
  "valid_from": "2024-11-01",
  "valid_until": null,
  "is_active": true,
  "order": 4,
  "parent": null,
  "children": []
}
```

---

## Frontend Integration Examples

### Fetch Dimensions

```javascript
async function fetchDimensions(workspaceId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/dimensions/?${params}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
}

// Usage
const dimensions = await fetchDimensions(1, { is_active: true });
```

### Dimension Form Builder

```javascript
async function buildDimensionForm(workspaceId) {
  const dimensions = await fetchDimensions(workspaceId, {
    is_active: true
  });

  return dimensions.map(dim => {
    if (dim.type === 'select') {
      return {
        type: 'select',
        name: dim.name,
        label: dim.description,
        required: dim.is_required,
        options: dim.values.map(v => ({
          value: v.id,
          label: v.label
        }))
      };
    } else if (dim.type === 'text') {
      return {
        type: 'text',
        name: dim.name,
        label: dim.description,
        required: dim.is_required
      };
    }
    // ... handle other types
  });
}

// Usage: Generate form fields dynamically
const formFields = await buildDimensionForm(1);
```

### Create Dimension with Values

```javascript
async function createDimensionWithValues(workspaceId, dimensionData, values) {
  // Step 1: Create dimension
  const dimension = await fetch(
    `${API_BASE}/workspaces/${workspaceId}/dimensions/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(dimensionData)
    }
  ).then(r => r.json());

  // Step 2: Add values
  const createdValues = await Promise.all(
    values.map((value, index) =>
      fetch(
        `${API_BASE}/workspaces/${workspaceId}/dimension-values/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            dimension_id: dimension.id,
            ...value,
            order: index + 1
          })
        }
      ).then(r => r.json())
    )
  );

  return { dimension, values: createdValues };
}

// Usage
const result = await createDimensionWithValues(1,
  {
    name: 'audience',
    description: 'Target audience',
    type: 'select',
    is_required: false
  },
  [
    { value: 'B2B', label: 'Business to Business' },
    { value: 'B2C', label: 'Business to Consumer' }
  ]
);
```

---

## Common Use Cases

### 1. Dimension Management UI

```javascript
function DimensionList({ workspaceId }) {
  const [dimensions, setDimensions] = useState([]);

  useEffect(() => {
    async function load() {
      const data = await fetchDimensions(workspaceId);
      setDimensions(data);
    }
    load();
  }, [workspaceId]);

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Required</th>
          <th>Values</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {dimensions.map(dim => (
          <tr key={dim.id}>
            <td>{dim.name}</td>
            <td>{dim.type}</td>
            <td>{dim.is_required ? 'Yes' : 'No'}</td>
            <td>{dim.values_count}</td>
            <td>
              <button onClick={() => editDimension(dim.id)}>Edit</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 2. Dynamic Form Field Generator

```javascript
function DimensionField({ dimension, value, onChange }) {
  if (dimension.type === 'select') {
    return (
      <select
        value={value}
        onChange={(e) => onChange(dimension.id, e.target.value)}
        required={dimension.is_required}
      >
        <option value="">Select {dimension.name}</option>
        {dimension.values.map(v => (
          <option key={v.id} value={v.id}>{v.label}</option>
        ))}
      </select>
    );
  } else if (dimension.type === 'text') {
    return (
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(dimension.id, e.target.value)}
        required={dimension.is_required}
        placeholder={dimension.description}
      />
    );
  }
  // Handle other types...
}
```

---

## Notes

- Dimensions can be reused across multiple rules
- Dimension values can have time-based validity (`valid_from`, `valid_until`)
- Deleting a dimension used in active rules will fail
- Dimension ordering affects display in forms and UI
- Hierarchical dimension values supported via `parent` field
