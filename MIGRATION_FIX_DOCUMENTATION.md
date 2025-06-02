# Migration Fix Documentation

## Issue Description

A critical migration file `0002_add_platform_slug_safe.py` was deleted from the codebase, which created a dangerous situation for deployments.

## Problem Details

### What was the issue?

- The `Platform` model has a `slug` field defined: `slug = models.SlugField(max_length=50, unique=True)`
- Migration `0002_add_platform_slug_safe.py` was responsible for creating this field in the database
- The migration was deleted, creating a gap: `0001_initial` → `0003_submission_created_by` → `0004_add_created_by_to_all_models`
- This would cause **deployment failures** on fresh environments

### Why was this dangerous?

1. **Fresh deployments** would fail because Django would try to create a table with a `slug` field but no migration existed to create it
2. **Model/database mismatch** where the Python model expects a field that doesn't exist in the database
3. **Migration dependency issues** if other migrations depended on the deleted one

## Solution Implemented

### Created Migration `0005_recreate_platform_slug.py`

- **Safe migration** that checks if the `slug` column already exists before trying to create it
- **SQLite compatible** using `PRAGMA table_info()` instead of `information_schema`
- **Populates slugs** for existing Platform records using `slugify(platform.name)`
- **Handles uniqueness** by appending numbers to duplicate slugs

### Key Features of the Fix:

1. **Idempotent**: Can be run multiple times safely
2. **Database agnostic**: Works with SQLite, PostgreSQL, etc.
3. **Data preservation**: Doesn't lose existing data
4. **Backward compatible**: Includes proper reverse migration

## Current Migration State

```
master_data
 [X] 0001_initial
 [X] 0003_submission_created_by
 [X] 0004_add_created_by_to_all_models
 [X] 0005_recreate_platform_slug
```

## Deployment Safety

✅ **Safe for deployment**: The migration chain is now complete and consistent

✅ **Fresh environments**: Will work correctly with the new migration

✅ **Existing environments**: Migration detects existing columns and skips creation

## Lessons Learned

1. **Never delete migrations** from the middle of a chain
2. **Always check migration dependencies** before removing files
3. **Test migrations** on fresh databases before deployment
4. **Use version control** to track migration changes

## For Future Reference

If you need to remove a migration:

1. Use `python manage.py migrate app_name migration_number` to roll back first
2. Then delete the migration file
3. Or use `--fake` flag if the migration was never applied to production
