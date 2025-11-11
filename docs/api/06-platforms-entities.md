# Platforms & Entities API

Platforms represent external advertising/marketing platforms (Meta Ads, Google Ads, TikTok, etc.). Each platform has multiple entities (campaign, ad group, ad, etc.) that form a hierarchy.

**Base Path**: `/api/v1/platforms/` and `/api/v1/entities/`

---

## Endpoints Overview

### Platforms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/platforms/` | List all platforms |
| GET | `/platforms/{id}/` | Get platform details |

### Entities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/entities/` | List all entities |
| GET | `/entities/?platform_id={id}` | List entities for platform |
| GET | `/entities/{id}/` | Get entity details |

---

## Data Models

### Platform Object

```json
{
  "id": 1,
  "name": "Meta Ads",
  "slug": "meta-ads",
  "platform_type": "meta",
  "description": "Facebook and Instagram advertising platform",
  "is_active": true,
  "entities": [
    {
      "id": 1,
      "name": "account",
      "entity_level": 0
    },
    {
      "id": 2,
      "name": "campaign",
      "entity_level": 1
    },
    {
      "id": 3,
      "name": "ad_set",
      "entity_level": 2
    },
    {
      "id": 4,
      "name": "ad",
      "entity_level": 3
    }
  ]
}
```

### Entity Object

```json
{
  "id": 2,
  "name": "campaign",
  "entity_level": 1,
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "platform_type": "meta"
  },
  "parent_entity": {
    "id": 1,
    "name": "account",
    "entity_level": 0
  },
  "child_entities": [
    {
      "id": 3,
      "name": "ad_set",
      "entity_level": 2
    }
  ],
  "rules": [
    {
      "id": 5,
      "name": "Campaign Naming Rule",
      "pattern": "{client}-{year}-{region}-{quarter}-{objective}"
    }
  ]
}
```

### Platform Types

- `meta` - Meta (Facebook/Instagram)
- `google` - Google Ads
- `tiktok` - TikTok Ads
- `linkedin` - LinkedIn Ads
- `twitter` - Twitter/X Ads
- `custom` - Custom platform

### Entity Levels

Entity levels define hierarchy (0 = root, higher numbers = children):
- **Level 0**: Account (root)
- **Level 1**: Campaign
- **Level 2**: Ad Group/Ad Set
- **Level 3**: Ad/Creative

---

## List Platforms

**GET** `/api/v1/platforms/`

Get all available platforms.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform_type` | string | Filter by type |
| `is_active` | boolean | Filter active/inactive platforms |

### Example Request

```bash
GET /api/v1/platforms/?is_active=true
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
[
  {
    "id": 1,
    "name": "Meta Ads",
    "slug": "meta-ads",
    "platform_type": "meta",
    "description": "Facebook and Instagram advertising",
    "is_active": true,
    "entities": [...]
  },
  {
    "id": 2,
    "name": "Google Ads",
    "slug": "google-ads",
    "platform_type": "google",
    "description": "Google advertising platform",
    "is_active": true,
    "entities": [...]
  }
]
```

---

## Get Platform Details

**GET** `/api/v1/platforms/{id}/`

Get detailed information about a platform including all entities and rules.

### Example Response (200 OK)

```json
{
  "id": 1,
  "name": "Meta Ads",
  "slug": "meta-ads",
  "platform_type": "meta",
  "description": "Facebook and Instagram advertising platform",
  "is_active": true,
  "entities": [
    {
      "id": 1,
      "name": "account",
      "entity_level": 0,
      "parent_entity": null,
      "rules_count": 1
    },
    {
      "id": 2,
      "name": "campaign",
      "entity_level": 1,
      "parent_entity": {
        "id": 1,
        "name": "account"
      },
      "rules_count": 3
    },
    {
      "id": 3,
      "name": "ad_set",
      "entity_level": 2,
      "parent_entity": {
        "id": 2,
        "name": "campaign"
      },
      "rules_count": 2
    }
  ],
  "total_rules": 6,
  "total_entities": 4
}
```

---

## List Entities

**GET** `/api/v1/entities/`

Get all entities or filter by platform.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform_id` | integer | Filter by platform |
| `entity_level` | integer | Filter by hierarchy level |

### Example Request

```bash
GET /api/v1/entities/?platform_id=1
Authorization: Bearer <token>
```

### Example Response (200 OK)

```json
[
  {
    "id": 1,
    "name": "account",
    "entity_level": 0,
    "platform": {
      "id": 1,
      "name": "Meta Ads",
      "platform_type": "meta"
    },
    "parent_entity": null,
    "child_entities": [
      {
        "id": 2,
        "name": "campaign"
      }
    ]
  },
  {
    "id": 2,
    "name": "campaign",
    "entity_level": 1,
    "platform": {
      "id": 1,
      "name": "Meta Ads",
      "platform_type": "meta"
    },
    "parent_entity": {
      "id": 1,
      "name": "account"
    },
    "child_entities": [
      {
        "id": 3,
        "name": "ad_set"
      }
    ]
  }
]
```

---

## Get Entity Details

**GET** `/api/v1/entities/{id}/`

Get detailed information about an entity.

### Example Response (200 OK)

```json
{
  "id": 2,
  "name": "campaign",
  "entity_level": 1,
  "platform": {
    "id": 1,
    "name": "Meta Ads",
    "slug": "meta-ads",
    "platform_type": "meta"
  },
  "parent_entity": {
    "id": 1,
    "name": "account",
    "entity_level": 0
  },
  "child_entities": [
    {
      "id": 3,
      "name": "ad_set",
      "entity_level": 2
    }
  ],
  "rules": [
    {
      "id": 5,
      "name": "Campaign Naming Rule",
      "pattern": "{client}-{year}-{region}-{quarter}-{objective}",
      "is_active": true
    },
    {
      "id": 8,
      "name": "Alternative Campaign Rule",
      "pattern": "{brand}-{region}-{year}-{quarter}",
      "is_active": true
    }
  ],
  "total_rules": 2,
  "sample_strings": [
    "ACME-2024-US-Q4-Awareness",
    "ACME-2024-EU-Q3-Conversion"
  ]
}
```

---

## Frontend Integration Examples

### Fetch Platforms

```javascript
async function fetchPlatforms() {
  const response = await fetch(`${API_BASE}/platforms/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}

// Usage
const platforms = await fetchPlatforms();
```

### Platform Selector

```javascript
// For platform dropdown in project/string creation
async function getPlatformOptions() {
  const platforms = await fetchPlatforms();
  return platforms
    .filter(p => p.is_active)
    .map(p => ({
      value: p.id,
      label: p.name,
      type: p.platform_type,
      entities: p.entities
    }));
}

// Usage in form
const platformOptions = await getPlatformOptions();
```

### Entity Hierarchy Display

```javascript
async function buildEntityHierarchy(platformId) {
  const response = await fetch(
    `${API_BASE}/entities/?platform_id=${platformId}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  const entities = await response.json();

  // Sort by level
  return entities.sort((a, b) => a.entity_level - b.entity_level);
}

// Usage: Display hierarchy
const hierarchy = await buildEntityHierarchy(1);
hierarchy.forEach(entity => {
  console.log(`${'  '.repeat(entity.entity_level)}${entity.name}`);
});
// Output:
// account
//   campaign
//     ad_set
//       ad
```

### Entity Selection by Level

```javascript
async function getEntitiesForLevel(platformId, level) {
  const response = await fetch(
    `${API_BASE}/entities/?platform_id=${platformId}&entity_level=${level}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
}

// Usage: Get all campaign-level entities
const campaignEntities = await getEntitiesForLevel(1, 1);
```

---

## Common Use Cases

### 1. Platform Configuration UI

```javascript
function PlatformList() {
  const [platforms, setPlatforms] = useState([]);

  useEffect(() => {
    async function loadPlatforms() {
      const data = await fetchPlatforms();
      setPlatforms(data);
    }
    loadPlatforms();
  }, []);

  return (
    <div>
      {platforms.map(platform => (
        <PlatformCard
          key={platform.id}
          name={platform.name}
          type={platform.platform_type}
          entitiesCount={platform.entities.length}
          rulesCount={platform.total_rules}
        />
      ))}
    </div>
  );
}
```

### 2. Entity Selector with Hierarchy

```javascript
function EntitySelector({ platformId, onSelect }) {
  const [entities, setEntities] = useState([]);

  useEffect(() => {
    async function loadEntities() {
      const data = await buildEntityHierarchy(platformId);
      setEntities(data);
    }
    loadEntities();
  }, [platformId]);

  return (
    <select onChange={(e) => onSelect(Number(e.target.value))}>
      {entities.map(entity => (
        <option key={entity.id} value={entity.id}>
          {'\u00A0'.repeat(entity.entity_level * 4)}{entity.name}
        </option>
      ))}
    </select>
  );
}
```

### 3. Rule Selection by Entity

```javascript
async function getRulesForEntity(entityId) {
  const entity = await fetch(
    `${API_BASE}/entities/${entityId}/`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  ).then(r => r.json());

  return entity.rules.filter(rule => rule.is_active);
}

// Usage: When user selects entity, show available rules
const rules = await getRulesForEntity(2); // campaign entity
```

---

## Understanding Platform Hierarchy

### Meta Ads Example

```
Account (Level 0)
└── Campaign (Level 1)
    └── Ad Set (Level 2)
        └── Ad (Level 3)
```

### Google Ads Example

```
Account (Level 0)
└── Campaign (Level 1)
    └── Ad Group (Level 2)
        └── Ad (Level 3)
```

### Entity Relationships

- **Parent**: One level up (e.g., Campaign parent is Account)
- **Child**: One level down (e.g., Campaign child is Ad Set)
- **Siblings**: Same level, same parent (e.g., multiple campaigns under one account)

---

## Notes

- Platforms are pre-configured by administrators
- Entity hierarchies are platform-specific
- Each entity level can have multiple naming rules
- Entity levels determine parent-child relationships in strings
- Platform selection determines available entities and rules
