# Legacy Migrations

This directory contains the original migrations that were squashed into the current `0001_initial.py` migration.

## Migration History

### Original Migrations (Squashed)

1. **0001_initial.py** - Original initial migration with basic models
2. **0002_add_slug_fields.py** - Added slug fields to various models
3. **0003_add_workspace_to_models.py** - Added workspace support to all models
4. **0004_remove_workspace_from_platform_field.py** - Removed workspace from Platform and Field models (made them global)

### Final State

The current `master_data/migrations/0001_initial.py` represents the final state after all these changes:

- **Platform**: Global resource (no workspace field)
- **Field**: Global resource (no workspace field)
- **All other models**: Workspace-scoped with proper relationships

## For New Deployments

New deployments should use only the squashed `0001_initial.py` migration. These legacy migrations are kept for reference and for existing deployments that need to maintain migration history.

## Migration Squashing Process

The migrations were squashed using:

```bash
python manage.py squashmigrations master_data 0001 0004
```

Then cleaned up to:

1. Remove the `replaces` directive
2. Mark as `initial = True`
3. Move legacy migrations to this directory
4. Update dependent migrations in other apps

## Dependencies Updated

- `users/migrations/0002_add_workspace_relationships.py` dependency updated from `master_data.0003_add_workspace_to_models` to `master_data.0001_initial`
