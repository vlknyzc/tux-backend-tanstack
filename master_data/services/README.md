# Master Data Services

This directory contains the service layer for the master data application, providing optimized data access and caching for dimension catalogs, field templates, and rule configurations.

## Services Overview

- **`DimensionCatalogService`**: Manages dimension catalogs with workspace-aware filtering
- **`FieldTemplateService`**: Handles field template generation and caching
- **`InheritanceMatrixService`**: Manages dimension inheritance logic
- **`RuleService`**: Unified service combining all rule optimization services

## Automatic Cache Invalidation

The system includes automatic cache invalidation using Django signals to ensure configuration is always up-to-date when changes occur.

### What Gets Invalidated

The cache invalidation system automatically clears relevant caches when:

- **DimensionValue**: Created, updated, or deleted
- **Dimension**: Created, updated, or deleted
- **Rule**: Created, updated, or deleted
- **RuleDetail**: Created, updated, or deleted
- **Field**: Created, updated, or deleted
- **Platform**: Updated or deleted

### How It Works

1. **Django Signals**: Signal handlers in `signals.py` listen for model changes
2. **Smart Targeting**: Only invalidates caches for rules that are actually affected
3. **Workspace Aware**: Respects workspace boundaries when determining impact
4. **Logging**: All cache invalidations are logged for monitoring and debugging

### Cache Keys Invalidated

For each affected rule, the following cache keys are cleared:

- `dimension_catalog:{rule_id}`
- `optimized_dimension_catalog:{rule_id}`
- `complete_rule_data:{rule_id}`
- `field_templates:{rule_id}`
- `inheritance_matrix:{rule_id}`

### Example Log Output

```
INFO:master_data.signals:Invalidated caches for 1 rules: [22] - DimensionValue created: Country=uk (workspace: Client 1)
```

## Workspace Filtering

All services properly filter data by workspace to ensure multi-tenant isolation:

- **DimensionValue queries**: `DimensionValue.objects.filter(workspace=rule.workspace)`
- **Automatic isolation**: Users only see data from their accessible workspaces
- **Cache separation**: Cached data is workspace-specific

## Performance Features

- **30-minute cache timeout**: Balances performance with data freshness
- **Optimized queries**: Uses `select_related` and `prefetch_related` for efficiency
- **Lazy loading**: Only builds data when actually needed
- **Smart invalidation**: Only clears caches for actually affected rules

## Usage Example

```python
from master_data.services.dimension_catalog_service import DimensionCatalogService
from master_data.models import Rule

# Get optimized catalog for a rule
service = DimensionCatalogService()
rule = Rule.objects.get(id=22)
catalog = service.get_optimized_catalog_for_rule(rule.id)

# Cache will be automatically invalidated when:
# - Dimension values are added/updated/deleted
# - Rule configuration changes
# - Related models are modified
```

## Testing Cache Invalidation

The cache invalidation system is thoroughly tested and logs all operations. You can monitor cache invalidation in your application logs to ensure it's working correctly.
