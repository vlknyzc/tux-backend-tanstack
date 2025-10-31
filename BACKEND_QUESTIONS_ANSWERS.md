# Backend Developer Questions - Answers & Clarifications

**Date:** 2024-12-XX  
**Status:** Official Answers from Frontend Team

---

## Table of Contents

1. [CRITICAL ARCHITECTURE QUESTIONS](#critical-architecture-questions)
2. [IMPLEMENTATION PRIORITY QUESTIONS](#implementation-priority-questions)
3. [BUSINESS LOGIC QUESTIONS](#business-logic-questions)
4. [API DESIGN QUESTIONS](#api-design-questions)
5. [TESTING & DATA MIGRATION](#testing--data-migration)

---

## CRITICAL ARCHITECTURE QUESTIONS

### 1. Project vs Submission Relationship

**Question:** Should we keep both models, migrate, or create wrapper?

**Answer: Option A - Keep Both Models Separate**

**Rationale:**

- Projects are a **new concept** separate from submissions
- Frontend explicitly separates them with different types (`Project` vs `Submission`, `ProjectString` vs `String`)
- Both systems can coexist - submissions won't be deprecated immediately
- Projects will eventually replace submissions, but migration can happen later

**Implementation:**

- Create `Project` model as a completely separate entity
- Create `ProjectString` model alongside existing `String` model
- No migration needed in Phase 1
- Keep submission system intact (don't touch existing code)

**Frontend Evidence:**

- `src/types/project.ts` - Separate `ProjectString` interface
- `src/types/submission.ts` - Separate `Submission` interface
- `src/components/projects/` - Separate project components
- `src/components/submissions/` - Separate submission components

---

### 2. String Model Duplication

**Question:** Should ProjectString inherit, duplicate, or refactor?

**Answer: Option C - Refactor Existing String to Support Both (Long-term), but Option A (Inheritance) for Phase 1**

**Phase 1 Recommendation: Option A - Inheritance/Composition**

**Rationale:**

- **Phase 1:** Use inheritance or composition to reuse existing String logic
- This is safer and faster for initial implementation
- We can refactor later if needed
- Frontend expects same structure (`value`, `string_uuid`, `parent_uuid`, `details`, etc.)

**Implementation Approach:**

```python
# Option A: Inheritance (simplest for Phase 1)
class ProjectString(String):
    project = ForeignKey(Project)
    platform = ForeignKey(Platform)  # via PlatformAssignment

    class Meta:
        # Override parent to remove submission field
        # or make submission nullable/optional
        pass

# OR Option A2: Composition (if inheritance is problematic)
class ProjectString(models.Model):
    # Reuse String model via OneToOne or composition
    string = OneToOneField(String, on_delete=models.CASCADE)
    project = ForeignKey(Project)
    platform = ForeignKey(Platform)

    # Delegate string operations to string instance
```

**Frontend Expectations:**

- `ProjectString` must have same fields as `String`:
  - `id`, `value`, `string_uuid`, `parent_uuid`
  - `details` array with dimension values
  - `created_by`, `created_by_name`, `created`, `last_updated`
- Additional fields: `project_id`, `platform_id`, `field_id`, `rule_id`

**Long-term (Post-Phase 1):**

- Consider Option C: Refactor `String` to be polymorphic (submission OR project)
- But this is out of scope for Phase 1

---

### 3. Workspace URL Pattern

**Question:** Should we use explicit `/workspaces/{workspaceId}/` prefix or auth context?

**Answer: Option A - Explicit `/workspaces/{workspaceId}/` Prefix**

**Rationale:**

- Frontend **explicitly uses** `/workspaces/{workspaceId}/projects/...` pattern
- All frontend routes follow this pattern (see `src/lib/routes.ts`)
- Frontend API client expects workspace ID in URL for routing and context detection
- Consistency with other workspace-scoped endpoints

**Frontend Evidence:**

```typescript
// src/lib/routes.ts
projects: {
  list: (workspaceId: number) => `/workspaces/${workspaceId}/projects`,
  detail: (workspaceId: number, projectId: number | string) =>
    `/workspaces/${workspaceId}/projects/${projectId}`,
  // ...
}

// src/lib/api/strings.ts
const getWorkspaceUrl = (workspaceId: string | number, path: string = "") =>
  `/workspaces/${workspaceId}/strings${path ? `/${path}` : ""}/`;
```

**Implementation:**

- Use explicit `/workspaces/{workspaceId}/projects/...` pattern
- Still validate workspace membership via auth context (double-check)
- Workspace ID in URL is for routing; auth context is for security

**Note:** If backend already uses WorkspaceMixin for filtering, you can still use it, but the URL pattern must match frontend expectations.

---

### 4. Field Model - Workspace Scope

**Question:** Are fields global or workspace-scoped?

**Answer: Option A - Keep Fields Global (Current Implementation)**

**Rationale:**

- Fields are **workspace-agnostic** (shared across all workspaces) - this is correct
- Projects reference **platforms**, platforms reference **rules**, rules reference **fields**
- Fields being global is fine - projects don't need workspace-specific fields
- The workspace isolation happens at the **project level**, not field level

**Frontend Evidence:**

- Fields are fetched once and reused across workspaces
- Project strings reference fields by ID (not workspace-scoped)
- Platform assignments link projects to platforms, which have rules, which have fields

**Implementation:**

- Keep fields global (no changes needed)
- Projects → Platforms → Rules → Fields (this hierarchy is correct)
- No need to create workspace-specific field instances

**Important:** When validating strings in projects:

- Ensure the `field_id` belongs to a rule that belongs to the platform
- Platform belongs to workspace (via project)
- This provides the workspace isolation without making fields workspace-specific

---

## IMPLEMENTATION PRIORITY QUESTIONS

### 5. Phase Scope

**Question:** Should I implement Phase 1 only, Phase 1+2, or all phases?

**Answer: Phase 1 Only (Critical - Blocking Frontend)**

**Rationale:**

- Frontend is **blocked** waiting for Phase 1 endpoints
- Phase 1 endpoints are needed for the grid builder to work
- Phase 2 (approval) can be implemented later without blocking frontend
- Phase 3 (unlock, history) is explicitly marked as "future enhancement"

**Phase 1 Endpoints (Critical):**

1. ✅ Project CRUD (if not already exists)
2. ⚠️ **Bulk Create Strings** (`POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk`)
3. ⚠️ **List Strings** (`GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings`)
4. ⚠️ **Get String Expanded** (`GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/expanded`)
5. ⚠️ **Update String** (`PUT /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}`)
6. ⚠️ **Delete String** (`DELETE /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}`)

**Phase 2 (Can Wait):**

- Approval endpoints (platform and project level)
- Activity tracking
- Approval history

**Phase 3 (Future):**

- Unlock functionality
- String history/versioning
- Bulk update endpoints

---

### 6. Missing Model: created_by Field

**Question:** Should we add `created_by` to base String model or only ProjectString?

**Answer: Add `created_by` to Both (Base String and ProjectString)**

**Rationale:**

- **Existing String model already has `created_by`** (see `src/types/string.ts` line 14-15)
- Frontend expects `created_by` and `created_by_name` in both `String` and `ProjectString`
- Consistency: Both string types should track creator

**Frontend Evidence:**

```typescript
// src/types/string.ts
export interface String {
  createdBy: number | null;
  createdByName: string | null;
  // ...
}

// src/types/project.ts
export interface ProjectString {
  createdBy: number | null;
  createdByName: string | null;
  // ...
}
```

**Implementation:**

- If base `String` model doesn't have `created_by`, add it
- `ProjectString` should also have `created_by` (inherit or add separately)
- Use `created_by_name` for denormalized display (or join on user table)

**Note:** If backend uses audit logs, you can still add `created_by` to the model for easy querying and frontend display.

---

## BUSINESS LOGIC QUESTIONS

### 7. Approval Permissions

**Question:** Who can approve projects/platforms?

**Answer: Workspace Admins Only (Simple Approach for Phase 1)**

**Rationale:**

- Keep it simple for Phase 1
- Workspace admins have full control
- Can enhance later with configurable approvers

**Implementation:**

```python
def can_approve_project(user, project):
    # Simple: workspace admins only
    workspace_user = WorkspaceUser.objects.get(
        workspace=project.workspace,
        user=user
    )
    return workspace_user.role == 'admin'

# Future enhancement: Add ProjectApprover model for configurable approvers
```

**Future Enhancement (Post-Phase 1):**

- Add `ProjectApprover` model for workspace-specific approver configuration
- Allow workspace admins to designate approvers per project or globally
- For now, workspace admins only is sufficient

**Frontend Expectation:**

- Frontend will check user role and show/hide approval buttons accordingly
- Approval buttons only visible to workspace admins (or designated approvers in future)

---

### 8. Cascade Delete for Parent Strings

**Question:** Should we cascade delete children or prevent deletion?

**Answer: Prevent Deletion (Return 400 Error)**

**Rationale:**

- Data integrity is more important than convenience
- Users should explicitly delete children first
- Prevents accidental data loss
- Matches spec recommendation

**Implementation:**

```python
def delete_project_string(string_id, project_id, platform_id):
    string = ProjectString.objects.get(
        id=string_id,
        project_id=project_id,
        platform_id=platform_id
    )

    # Check if string has children
    children_count = ProjectString.objects.filter(
        parent_uuid=string.string_uuid,
        platform_id=platform_id
    ).count()

    if children_count > 0:
        raise ValidationError({
            "error": "Conflict",
            "message": "String has children and cannot be deleted",
            "details": {
                "string_id": string_id,
                "children_count": children_count
            }
        })

    string.delete()
```

**Error Response:**

```json
{
  "error": "Conflict",
  "message": "String has children and cannot be deleted",
  "details": {
    "string_id": 1,
    "children_count": 3
  }
}
```

**Future Enhancement:**

- Could add "cascade delete" option with confirmation
- For now, prevent deletion and return clear error message

---

### 9. Platform Assignment - User Assignment

**Question:** Should we use ManyToManyField or junction table?

**Answer: Use ManyToManyField (Simplest)**

**Rationale:**

- Django's `ManyToManyField` is the standard approach
- No need for custom junction table unless you need additional fields
- Simpler to implement and maintain

**Implementation:**

```python
class PlatformAssignment(models.Model):
    project = ForeignKey(Project, on_delete=models.CASCADE)
    platform = ForeignKey(Platform, on_delete=models.CASCADE)
    assigned_members = ManyToManyField(User, related_name='platform_assignments')
    # ... other fields

    class Meta:
        unique_together = ['project', 'platform']
```

**If You Need Additional Fields Later:**

- If you need to track "assigned_at" or "role" per member, use through model:

```python
class PlatformAssignmentMember(models.Model):
    assignment = ForeignKey(PlatformAssignment, on_delete=models.CASCADE)
    user = ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = DateTimeField(auto_now_add=True)
    # ... other fields if needed

class PlatformAssignment(models.Model):
    assigned_members = ManyToManyField(
        User,
        through='PlatformAssignmentMember',
        related_name='platform_assignments'
    )
```

**For Phase 1:** Simple `ManyToManyField` is sufficient.

---

## API DESIGN QUESTIONS

### 10. API Versioning

**Question:** Should project endpoints be under `/api/v1/` or `/api/v2/`?

**Answer: Follow Existing Backend Pattern**

**Rationale:**

- Frontend doesn't specify API version in routes (handled by baseURL)
- Check what existing backend endpoints use
- Consistency with existing API structure is more important than version number

**Frontend Evidence:**

- Frontend routes are relative: `/workspaces/{workspaceId}/projects/...`
- API client uses `baseURL` which likely includes `/api/v1/` or `/api/v2/`
- Frontend doesn't care about version prefix - backend handles it

**Recommendation:**

- Check existing backend URL patterns (e.g., `/api/v1/submissions/` or `/api/v2/submissions/`)
- Use the same version prefix for projects
- If backend uses `/api/v1/`, use `/api/v1/workspaces/{id}/projects/`
- If backend uses `/api/v2/`, use `/api/v2/workspaces/{id}/projects/`

**Consistency is Key:**

- Whatever pattern backend currently uses, match it
- Don't create new version just for projects

---

### 11. Serializer Inheritance

**Question:** Should we create new serializers or inherit from existing?

**Answer: Inherit from Existing StringSerializer**

**Rationale:**

- Reuse existing serializer logic
- Add project-specific fields
- Consistency with model inheritance approach

**Implementation:**

```python
class ProjectStringSerializer(StringSerializer):
    project_id = IntegerField()
    platform_id = IntegerField()
    rule_id = IntegerField()
    # ... other project-specific fields

    class Meta(StringSerializer.Meta):
        model = ProjectString
        fields = StringSerializer.Meta.fields + [
            'project_id',
            'platform_id',
            'rule_id',
            # ... other fields
        ]
```

**If Inheritance is Problematic:**

- Create shared base serializer for common fields
- Inherit both `StringSerializer` and `ProjectStringSerializer` from base

**Important:** Ensure response format matches frontend expectations:

- Snake_case in JSON (frontend converts to camelCase)
- Include all fields: `created_by`, `created_by_name`, `details`, etc.

---

## TESTING & DATA MIGRATION

### 12. Test Data

**Question:** Should we use management commands, fixtures, or factories?

**Answer: Use Test Factories (Recommended)**

**Rationale:**

- Factories are flexible and maintainable
- Easy to create test data programmatically
- Can be reused across tests
- Modern testing best practice

**Implementation:**

```python
# Using factory_boy or similar
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Test Project {n}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    workspace = factory.SubFactory(WorkspaceFactory)
    owner = factory.SubFactory(UserFactory)
    status = 'planning'

class ProjectStringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectString

    project = factory.SubFactory(ProjectFactory)
    platform = factory.SubFactory(PlatformFactory)
    field = factory.SubFactory(FieldFactory)
    value = factory.Sequence(lambda n: f"Test String {n}")
    string_uuid = factory.LazyFunction(uuid.uuid4)
```

**Alternative: Management Commands**

- Can create management commands for seeding development data
- Useful for local development, not required for tests

**Recommendation:**

- Use factories for tests
- Optional: Create management command for dev seeding (e.g., `python manage.py seed_projects`)

---

### 13. Initial Superuser

**Question:** Is `create_initial_superuser.py` intentional or should it be committed?

**Answer: Not Blocking - Handle as Standard Practice**

**Rationale:**

- This is a deployment/admin concern, not related to projects feature
- Can be committed if it's a standard practice for your backend
- Not blocking for projects implementation

**Recommendation:**

- If it's a standard deployment script, commit it
- If it's temporary/test-only, don't commit
- This doesn't affect projects feature implementation

---

## Summary of Key Decisions

### Architecture

1. ✅ **Option A**: Keep Projects and Submissions separate (both coexist)
2. ✅ **Option A**: Use inheritance/composition for ProjectString (reuse String logic)
3. ✅ **Option A**: Use explicit `/workspaces/{workspaceId}/` prefix in URLs
4. ✅ **Option A**: Keep fields global (workspace-agnostic)

### Implementation

5. ✅ **Phase 1 Only**: Implement critical string endpoints (1-6)
6. ✅ **Add `created_by`**: To both String and ProjectString models
7. ✅ **Workspace Admins Only**: For approval permissions (simple approach)
8. ✅ **Prevent Deletion**: Return 400 error if parent has children
9. ✅ **ManyToManyField**: For platform assignment members

### API Design

10. ✅ **Follow Existing Pattern**: Use same API version as other endpoints
11. ✅ **Inherit Serializers**: Reuse StringSerializer for ProjectStringSerializer

### Testing

12. ✅ **Use Factories**: For test data generation
13. ✅ **Not Blocking**: Handle superuser script as standard practice

---

## Frontend Files Waiting for Backend

These files have TODOs waiting for backend implementation:

1. **`src/hooks/project-grid-builder/useProjectStringSubmission.ts`**
   - Line 220: `addStringsToProject` API
   - Line 237: Bulk create strings
   - Line 291: Update string API

2. **`src/hooks/project-grid-builder/useProjectStringsByField.ts`**
   - Line 13: Create API function
   - Line 21: Fetch strings by field

3. **`src/hooks/project-grid-builder/useProjectParentStringSync.ts`**
   - Line 56: Fetch parent strings
   - Line 61: Use project string fetching
   - Line 109: Fetch expanded parent string

4. **`src/components/projects/ProjectPlatformStringsTable.tsx`**
   - Delete string functionality (needs DELETE endpoint)

---

## Additional Notes

### Response Format

- Use **snake_case** for all JSON fields (frontend converts to camelCase)
- Include all required fields as specified in the API spec
- Use ISO 8601 format for timestamps (`2024-10-25T14:30:00Z`)

### Error Handling

- Use consistent error format as specified in API spec
- Return appropriate HTTP status codes (400, 403, 404, 409, etc.)
- Include helpful error messages for debugging

### Security

- Validate workspace membership on all endpoints
- Validate project membership/role for operations
- Ensure platform assignment belongs to project
- Ensure strings belong to platform/project

---

## Questions?

If you have additional questions or need clarifications, please reach out to the frontend team. We're ready to help!

**Priority:** Focus on Phase 1 endpoints first - these are blocking the frontend grid builder functionality.
