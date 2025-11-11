# String Models Refactoring Plan

## Executive Summary

**Objective**: Rename `ProjectString` → `String` and `ProjectStringDetail` → `StringDetail` after removing deprecated submission-based models.

**Status**: Phase 1 (Cleanup) completed. Ready for Phase 2 (Rename).

**Estimated Complexity**: HIGH - 50+ files affected, database schema changes required.

---

## Current State (After Phase 1 Cleanup)

### ✅ Removed (Phase 1 Completed)
- ❌ `master_data/models/submission.py` - DELETED
- ❌ `master_data/models/string.py` (old String/StringDetail) - DELETED
- ❌ `master_data/views/string_views.py` - DELETED
- ❌ `master_data/views/string_detail_views.py` - DELETED
- ❌ `master_data/views/multi_operations_views.py` - DELETED
- ❌ `master_data/serializers/string.py` - DELETED
- ❌ `master_data/urls_main_api.py` - DELETED

### ✅ Active Models (Ready for Rename)
- ✓ `ProjectString` in `master_data/models/project_string.py`
- ✓ `ProjectStringDetail` in `master_data/models/project_string.py`

---

## Target State (After Phase 2)

### Model Names
- `ProjectString` → `String`
- `ProjectStringDetail` → `StringDetail`

### File Structure
```
master_data/
├── models/
│   └── string.py (renamed from project_string.py)
│       ├── class String (was ProjectString)
│       ├── class StringDetail (was ProjectStringDetail)
│       ├── class StringQuerySet (was ProjectStringQuerySet)
│       └── class StringManager (was ProjectStringManager)
├── serializers/
│   └── string.py (renamed from project_string.py)
├── views/
│   └── string_views.py (renamed from project_string_views.py)
└── ...
```

### Database Tables
- `master_data_projectstring` → `master_data_string`
- `master_data_projectstringdetail` → `master_data_stringdetail`

### API Endpoints
- `/api/v1/workspaces/{id}/projects/{project_id}/strings/` (keep as-is, just update implementation)

---

## Files Requiring Changes

### Category 1: Core Model Files (3 files)
**High Priority - Must be done first**

1. **master_data/models/project_string.py → string.py**
   - Rename file
   - Rename classes: `ProjectString` → `String`
   - Rename classes: `ProjectStringDetail` → `StringDetail`
   - Rename classes: `ProjectStringQuerySet` → `StringQuerySet`
   - Rename classes: `ProjectStringManager` → `StringManager`
   - Update `db_table` in Meta (for migration compatibility)
   - Update verbose names
   - Update related_names:
     - `project_strings` → `strings` (keep project-scoped)
     - `project_entity_strings` → `entity_strings`
     - `project_rule_strings` → `rule_strings`
     - `created_project_strings` → `created_strings`
     - `imported_project_strings` → `imported_strings`
     - `project_string_details` → `string_details`

2. **master_data/models/__init__.py**
   - Change import: `from .project_string import ProjectString, ProjectStringDetail`
   - To: `from .string import String, StringDetail`
   - Update __all__ list

3. **master_data/models/external_string.py**
   - Update FK reference: `imported_project_strings` → `imported_strings`

### Category 2: Serializers (2 files)

4. **master_data/serializers/project_string.py → string.py**
   - Rename file
   - Rename all serializer classes (keep detailed names for clarity):
     - `ProjectStringSerializer` → `StringSerializer`
     - `ProjectStringDetailSerializer` → `StringDetailSerializer`
     - `ProjectStringDetailNestedSerializer` → `StringDetailNestedSerializer`
     - `ProjectStringDetailWriteSerializer` → `StringDetailWriteSerializer`
     - `ListProjectStringsSerializer` → `ListStringsSerializer`
   - Update model references in Meta classes

5. **master_data/serializers/__init__.py**
   - Update import statement
   - Update __all__ list

### Category 3: Views (1 file)

6. **master_data/views/project_string_views.py → string_views.py**
   - Rename file
   - Keep URL paths as-is (project-scoped: `/projects/{id}/strings/`)
   - Update all model references
   - Update serializer imports
   - Update docstrings and comments

### Category 4: Services (6 files)
**Medium Priority**

7. **master_data/services/string_registry_service.py**
   - Update model imports
   - Update method references

8. **master_data/services/string_generation_service.py**
   - Update model imports (likely has old String references to remove)

9. **master_data/services/batch_update_service.py**
   - Update model references

10. **master_data/services/conflict_resolution_service.py**
    - Update model references

11. **master_data/services/inheritance_service.py**
    - Update model references

12. **master_data/services/propagation_service.py**
    - Update model references

### Category 5: Admin (1 file)

13. **master_data/admin.py**
    - Update model imports
    - Update admin class registrations

### Category 6: Signals (1 file)

14. **master_data/signals/string_propagation.py**
    - Update model references

### Category 7: Tests (10+ files)
**Lower Priority - Update after core changes**

15. **master_data/tests/test_string_registry_api.py**
16. **master_data/tests/test_string_registry_service.py**
17. **master_data/tests/test_string_serializer_workspace_isolation.py**
18. **master_data/tests/test_query_optimization.py**
19. **Other test files** (grep for ProjectString references)

### Category 8: Management Commands (1 file)

20. **master_data/management/commands/fix_parent_uuid_sync.py**
    - Update model references

### Category 9: Documentation

21. **Validation and sync brief.md**
    - Update model references

22. **CLAUDE.md**
    - Update references to String models

23. **Various docs/** files
    - Update as needed

### Category 10: URLs (1 file)

24. **master_data/urls.py** (main URL config)
    - Update view imports
    - URLs stay project-scoped: `/projects/{id}/strings/`

---

## Database Migration Strategy

### Option A: Rename Tables (Recommended)
**Pros**: Clean, preserves data, proper Django way
**Cons**: Slightly more complex migration

```python
# Migration: 0006_rename_projectstring_to_string.py

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('master_data', '0005_create_external_string_and_rename_batch'),
    ]

    operations = [
        # Rename tables
        migrations.AlterModelTable(
            name='projectstring',
            table='master_data_string',
        ),
        migrations.AlterModelTable(
            name='projectstringdetail',
            table='master_data_stringdetail',
        ),

        # Rename models (must come after table rename in same migration)
        migrations.RenameModel(
            old_name='ProjectString',
            new_name='String',
        ),
        migrations.RenameModel(
            old_name='ProjectStringDetail',
            new_name='StringDetail',
        ),
    ]
```

### Option B: Create New Tables + Data Migration (Not Recommended)
Too risky, complex, and unnecessary since there's no production data.

**Recommended: Option A**

---

## Execution Plan (Phase 2)

### Step 1: Prepare Models (Single Commit)
1. Rename `master_data/models/project_string.py` → `string.py`
2. In the file, rename all classes:
   - `ProjectString` → `String`
   - `ProjectStringDetail` → `StringDetail`
   - `ProjectStringQuerySet` → `StringQuerySet`
   - `ProjectStringManager` → `StringManager`
3. Add explicit `db_table` in Meta to maintain table names temporarily:
   ```python
   class String(TimeStampModel, WorkspaceMixin):
       class Meta:
           db_table = 'master_data_projectstring'  # Temporary
   ```
4. Update `master_data/models/__init__.py` imports
5. **Test**: Run `python manage.py check` - should pass

### Step 2: Update Serializers (Single Commit)
1. Rename `master_data/serializers/project_string.py` → `string.py`
2. Update all class names in serializers
3. Update `master_data/serializers/__init__.py`
4. **Test**: Run `python manage.py check` - should pass

### Step 3: Update Views (Single Commit)
1. Rename `master_data/views/project_string_views.py` → `string_views.py`
2. Update all imports and references
3. Update `master_data/views/__init__.py`
4. **Test**: Run `python manage.py check` - should pass

### Step 4: Update Services (Single Commit)
1. Update all 6 service files
2. **Test**: Run `python manage.py check` - should pass

### Step 5: Update Related Files (Single Commit)
1. Update admin.py
2. Update signals
3. Update management commands
4. **Test**: Run `python manage.py check` - should pass

### Step 6: Create Database Migration (Single Commit)
1. Remove temporary `db_table` from Meta classes
2. Run `python manage.py makemigrations`
3. Review generated migration
4. Edit if needed to add table renames
5. **Test**: Run `python manage.py migrate` on clean database

### Step 7: Update Tests (Single Commit)
1. Update all test files
2. **Test**: Run `python manage.py test master_data`

### Step 8: Update Documentation (Single Commit)
1. Update all .md files
2. Update CLAUDE.md
3. Regenerate schema.yml

---

## Testing Strategy

### After Each Step
```bash
# Check for errors
python manage.py check

# Check migrations
python manage.py makemigrations --dry-run

# Verify imports
python manage.py shell
>>> from master_data.models import String, StringDetail
>>> String.objects.count()
```

### After Step 6 (Migration)
```bash
# Test migration on fresh database
python manage.py migrate

# Verify table names
python manage.py dbshell
\dt master_data_*

# Verify data access
python manage.py shell
>>> from master_data.models import String
>>> String.objects.all()
```

### Final Testing
```bash
# Run full test suite
python manage.py test

# Check for any ProjectString references
grep -r "ProjectString" master_data/ --exclude-dir=migrations

# Regenerate schema
python manage.py spectacular --file schema.yml
```

---

## Risk Assessment

### High Risk Areas
1. **Database migration** - Must preserve data and relationships
2. **Foreign key references** - Many models reference ProjectString
3. **Serializers** - Nested serializers with complex field mappings

### Mitigation Strategies
1. **Backup database** before final migration
2. **Test each step** independently with `python manage.py check`
3. **Use db_table temporarily** to decouple model rename from table rename
4. **Update incrementally** - one category at a time
5. **Run tests frequently** after each commit

---

## Rollback Plan

If issues arise:

1. **Before Migration Applied**:
   - Revert code changes via git
   - No database changes to revert

2. **After Migration Applied**:
   - Database changes are harder to revert
   - Would need reverse migration:
   ```python
   # Reverse migration
   operations = [
       migrations.RenameModel(old_name='String', new_name='ProjectString'),
       migrations.RenameModel(old_name='StringDetail', new_name='ProjectStringDetail'),
   ]
   ```

**Best Practice**: Test entire process on development database before applying to any shared environment.

---

## Success Criteria

✅ All tests pass
✅ `python manage.py check` has no errors
✅ No references to "ProjectString" in codebase (except migrations)
✅ Database tables properly renamed
✅ API endpoints work correctly
✅ Admin panel works correctly
✅ Schema.yml updated

---

## Timeline Estimate

- **Step 1-3**: 30 minutes (Core models, serializers, views)
- **Step 4-5**: 20 minutes (Services and related files)
- **Step 6**: 15 minutes (Migration)
- **Step 7**: 30 minutes (Tests)
- **Step 8**: 15 minutes (Documentation)
- **Testing**: 20 minutes (Comprehensive testing)

**Total Estimated Time**: ~2.5 hours

---

## Notes

- Keep URLs project-scoped: `/api/v1/workspaces/{id}/projects/{project_id}/strings/`
- This maintains proper REST hierarchy (strings belong to projects)
- No API breaking changes - only internal model names change
- External API consumers see no difference

---

## Questions to Answer Before Starting

1. ✅ Are there any external API consumers who depend on response field names?
   - **Answer**: No production instance, safe to proceed

2. ✅ Should we keep related_names project-prefixed or simplify?
   - **Recommendation**: Keep `project.strings` for clarity, change others to be simpler

3. ✅ Any custom database indexes or constraints to preserve?
   - **Answer**: Yes, all defined in Meta - migration will handle automatically

---

## Approval

- [ ] Plan reviewed and approved
- [ ] Ready to execute Phase 2
- [ ] Database backup confirmed (if applicable)

**Approved By**: _________________
**Date**: _________________
