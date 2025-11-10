# Field → Entity Refactoring Summary

## Overview
We have successfully renamed the `Field` model to `Entity` throughout the Django backend codebase. This change better describes the model's purpose as it represents entities within a platform's naming structure (e.g., environment, project, service).

## 🔄 Backend Changes Summary

### Database Schema Changes
The following database tables and columns will be renamed:

| Old Name | New Name |
|----------|----------|
| `master_data_field` | `master_data_entity` |
| `field_level` | `entity_level` |
| `next_field` | `next_entity` |
| `next_field_id` | `next_entity_id` |
| Foreign key references to `field_id` | `entity_id` |

### Models Updated
1. **Entity** (formerly Field) - `master_data/models/entity.py`
2. **RuleDetail** - ForeignKey `field` → `entity`
3. **ProjectString** - ForeignKey `field` → `entity`
4. **String** - ForeignKey `field` → `entity`
5. **StringUpdateBatch** - ForeignKey `field` → `entity`
6. **Submission** - ForeignKey `starting_field` → `starting_entity`

### API Endpoints Changed

#### ⚠️ BREAKING CHANGES FOR FRONTEND

| Old Endpoint | New Endpoint |
|-------------|--------------|
| `GET /api/v1/fields/` | `GET /api/v1/entities/` |
| `POST /api/v1/fields/` | `POST /api/v1/entities/` |
| `GET /api/v1/fields/{id}/` | `GET /api/v1/entities/{id}/` |
| `PUT /api/v1/fields/{id}/` | `PUT /api/v1/entities/{id}/` |
| `PATCH /api/v1/fields/{id}/` | `PATCH /api/v1/entities/{id}/` |
| `DELETE /api/v1/fields/{id}/` | `DELETE /api/v1/entities/{id}/` |
| `GET /api/v1/workspaces/{workspace_id}/rules/{rule_id}/fields/{field_id}/` | `GET /api/v1/workspaces/{workspace_id}/rules/{rule_id}/entities/{entity_id}/` |

### JSON Response Field Names Changed

All API responses that previously contained `field` or `field_*` properties now use `entity` or `entity_*`:

```json
// OLD Response
{
  "id": 1,
  "platform": 1,
  "field_level": 1,
  "next_field": 2,
  "next_field_name": "project",
  "fields": [...]
}

// NEW Response
{
  "id": 1,
  "platform": 1,
  "entity_level": 1,
  "next_entity": 2,
  "next_entity_name": "project",
  "entities": [...]
}
```

### Query Parameters Changed

| Old Parameter | New Parameter |
|--------------|---------------|
| `?field_level=1` | `?entity_level=1` |
| `?field=1` | `?entity=1` |

## 📋 Frontend Migration Checklist

### 1. API Client Updates
- [ ] Update all API endpoint paths from `/fields/` to `/entities/`
- [ ] Update query parameters from `field_level` to `entity_level`
- [ ] Update URL parameters from `field_id` to `entity_id`

### 2. Type Definitions / Interfaces
```typescript
// OLD
interface Field {
  id: number;
  platform: number;
  platform_name: string;
  name: string;
  field_level: number;
  next_field: number | null;
  next_field_name: string | null;
  created_by: number | null;
  created: string;
  last_updated: string;
}

// NEW
interface Entity {
  id: number;
  platform: number;
  platform_name: string;
  name: string;
  entity_level: number;
  next_entity: number | null;
  next_entity_name: string | null;
  created_by: number | null;
  created: string;
  last_updated: string;
}
```

### 3. Component Props
Replace all occurrences of:
- `field` → `entity`
- `fieldLevel` → `entityLevel`
- `nextField` → `nextEntity`
- `fieldId` → `entityId`
- `FieldSelector` → `EntitySelector`
- `FieldForm` → `EntityForm`
- etc.

### 4. State Management
Update Redux/Zustand/Context slices:
- `fieldsSlice` → `entitiesSlice`
- `selectedField` → `selectedEntity`
- `fetchFields()` → `fetchEntities()`
- etc.

### 5. Form Fields
Update form field names in all forms that create/edit entities:
- `field_level` → `entity_level`
- `next_field` → `next_entity`

### 6. API Response Handling
Update response mappers and serializers:
```typescript
// OLD
const mapFieldResponse = (data: any) => ({
  ...data,
  fieldLevel: data.field_level,
  nextField: data.next_field,
});

// NEW
const mapEntityResponse = (data: any) => ({
  ...data,
  entityLevel: data.entity_level,
  nextEntity: data.next_entity,
});
```

### 7. Router Updates
```typescript
// OLD
<Route path="/fields" element={<FieldsPage />} />
<Route path="/fields/:fieldId" element={<FieldDetailPage />} />

// NEW
<Route path="/entities" element={<EntitiesPage />} />
<Route path="/entities/:entityId" element={<EntityDetailPage />} />
```

### 8. Search & Replace Suggestions

Run these find-and-replace operations in your codebase (case-sensitive):

1. **URL Paths:**
   - `'/fields'` → `'/entities'`
   - `'/fields/'` → `'/entities/'`
   - `/fields/` → `/entities/`

2. **Properties:**
   - `field_level` → `entity_level`
   - `fieldLevel` → `entityLevel`
   - `next_field` → `next_entity`
   - `nextField` → `nextEntity`
   - `field_id` → `entity_id`
   - `fieldId` → `entityId`

3. **Types/Interfaces:**
   - `Field` → `Entity` (where it refers to the model, not generic field)
   - `IField` → `IEntity`
   - `FieldType` → `EntityType`

4. **Components:**
   - `FieldList` → `EntityList`
   - `FieldForm` → `EntityForm`
   - `FieldSelector` → `EntitySelector`
   - `FieldPicker` → `EntityPicker`

5. **Hooks:**
   - `useField` → `useEntity`
   - `useFields` → `useEntities`
   - `useFetchFields` → `useFetchEntities`

6. **Actions/Functions:**
   - `fetchFields` → `fetchEntities`
   - `createField` → `createEntity`
   - `updateField` → `updateEntity`
   - `deleteField` → `deleteEntity`
   - `getFieldById` → `getEntityById`

## ⚠️ Important Notes

### Backward Compatibility
- **No backward compatibility** - this is a breaking change
- All frontend code must be updated before deploying
- Consider using feature flags if deploying incrementally

### Testing Checklist
After updating frontend code, test:
- [ ] Entity list displays correctly
- [ ] Entity creation works
- [ ] Entity editing works
- [ ] Entity deletion works
- [ ] Entity filtering by platform works
- [ ] Entity filtering by level works
- [ ] Rule configuration with entities works
- [ ] String generation with entities works
- [ ] Project string creation with entities works

### Swagger/API Documentation
- Swagger UI will automatically reflect the new endpoints
- API documentation at `/api/schema/swagger-ui/` shows updated schemas
- All serializers and responses will show `entity` instead of `field`

## 🔍 Example Migration Pattern

### Before (Old Code):
```typescript
// API Client
const fetchFields = async (platformId: number) => {
  const response = await api.get(`/api/v1/fields/?platform=${platformId}`);
  return response.data;
};

// Component
const FieldSelector: React.FC<{ onSelect: (field: Field) => void }> = ({ onSelect }) => {
  const [fields, setFields] = useState<Field[]>([]);

  useEffect(() => {
    fetchFields(platformId).then(setFields);
  }, [platformId]);

  return (
    <select onChange={(e) => onSelect(fields[e.target.value])}>
      {fields.map(field => (
        <option key={field.id} value={field.id}>
          Level {field.field_level}: {field.name}
        </option>
      ))}
    </select>
  );
};
```

### After (New Code):
```typescript
// API Client
const fetchEntities = async (platformId: number) => {
  const response = await api.get(`/api/v1/entities/?platform=${platformId}`);
  return response.data;
};

// Component
const EntitySelector: React.FC<{ onSelect: (entity: Entity) => void }> = ({ onSelect }) => {
  const [entities, setEntities] = useState<Entity[]>([]);

  useEffect(() => {
    fetchEntities(platformId).then(setEntities);
  }, [platformId]);

  return (
    <select onChange={(e) => onSelect(entities[e.target.value])}>
      {entities.map(entity => (
        <option key={entity.id} value={entity.id}>
          Level {entity.entity_level}: {entity.name}
        </option>
      ))}
    </select>
  );
};
```

## 📅 Deployment Strategy

1. **Backend First**: Deploy backend changes with migration
2. **Frontend Update**: Deploy frontend changes immediately after
3. **Testing**: Verify all entity-related features work
4. **Monitoring**: Watch for API errors related to entity endpoints

## 🆘 Rollback Plan

If issues arise:
1. Revert frontend deployment
2. Backend can be kept (field → entity is semantic, data unchanged)
3. Or revert both if necessary

## 📞 Support

If you encounter issues during migration:
- Check Swagger docs: `/api/schema/swagger-ui/`
- Review this document
- Contact backend team for clarification

---

**Last Updated**: 2025-11-09
**Backend Version**: Post Field→Entity Refactoring
**Breaking Change**: YES ⚠️
