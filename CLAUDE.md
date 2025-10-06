# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST API backend called "tuxonomy.com" that manages master data for multi-tenant SaaS applications. The system handles workspaces, platforms, dimensions, rules, and string generation with complex propagation logic.

## Architecture

### Core Django Apps

- **main/**: Django project configuration with environment-specific settings
- **master_data/**: Primary business logic app containing all core models and APIs
- **users/**: User authentication and workspace relationship management

### Key Models (master_data/models/)

- **Workspace**: Multi-tenant isolation boundary
- **Platform**: Data platforms (Snowflake, dbt, etc.)
- **Dimension/DimensionValue**: Hierarchical data categorization
- **Rule/RuleDetail**: Business rules for string generation
- **String/StringDetail**: Generated naming conventions
- **Propagation models**: Background job management for data propagation

### Service Architecture (master_data/services/)

- **DimensionCatalogService**: Optimized dimension queries with caching
- **PropagationService**: Handles complex string propagation logic
- **RuleService**: Unified rule management and optimization
- **InheritanceService**: Manages dimension inheritance hierarchies

## Common Development Commands

### Running the Server

```bash
# Development server
python manage.py runserver

# With specific settings
DJANGO_SETTINGS_MODULE=main.local_settings python manage.py runserver
```

### Database Operations

```bash
# Apply migrations
python manage.py migrate

# Create migrations for changes
python manage.py makemigrations

# Create initial workspace
python manage.py create_workspace "Client Name" --admin-email admin@client.com
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test master_data.tests.test_propagation_service

# Run with coverage (if installed)
coverage run --source='.' manage.py test
coverage report
```

### Management Commands

```bash
# Create superuser
python manage.py createsuperuser

# Assign user to workspace
python manage.py assign_user_to_workspace user@email.com workspace_slug

# Seed platform data
python manage.py seed_platforms
```

## Environment Configuration

The project uses environment-specific settings:

- **Local Development**: `main/local_settings.py` (PostgreSQL, DEBUG=True)
- **Production**: `main/production_settings.py` (PostgreSQL, DEBUG=False)

Environment detection via `DJANGO_ENV` variable:

- `DJANGO_ENV=PRODUCTION` → production settings
- Otherwise → local development settings

## API Structure

### Versioned Endpoints

All API endpoints are versioned: `/api/v1/` or `/api/v2/`

### Key API Endpoints

- `/api/v1/workspaces/` - Workspace management
- `/api/v1/platforms/` - Platform CRUD
- `/api/v1/dimensions/` - Dimension management
- `/api/v1/rules/` - Business rule configuration
- `/api/v1/strings/` - String generation and management
- `/api/v1/propagation/` - String propagation operations

### Authentication

- JWT-based authentication via `djangorestframework_simplejwt`
- Token endpoints: `/api/v1/token/` and `/api/v1/token/refresh/`

## Multi-Tenant Architecture

### Workspace Isolation

- All core models inherit from `WorkspaceMixin` for automatic workspace filtering
- Users can be assigned to multiple workspaces with different roles
- API responses automatically filter by user's accessible workspaces

### Development vs Production Workspace Access

- **Development**: Direct access via `localhost:8000` (workspace filtering via user authentication)
- **Production**: Subdomain-based workspace detection (optional)

## Caching & Performance

### Automatic Cache Invalidation

The system uses Django signals for intelligent cache invalidation:

- Located in `master_data/signals/cache_invalidation.py`
- Automatically clears caches when models change
- Workspace-aware invalidation

### Cache Keys

- `dimension_catalog:{rule_id}`
- `optimized_dimension_catalog:{rule_id}`
- `complete_rule_data:{rule_id}`
- `field_templates:{rule_id}`
- `inheritance_matrix:{rule_id}`

## Development Setup

### CORS Configuration

Development environment automatically allows:

- `http://localhost:3000` (React/Next.js)
- `http://localhost:8000` (Django dev server)
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8000`

### Database Migrations

- Clean migrations available in `master_data/migrations/`
- For new deployments, use standard `python manage.py migrate`
- Legacy migration backups in `migrations_legacy/` and `migrations_backup/`

## String Propagation System

### Core Concept

The system automatically propagates string changes across related entities when dimension values or rules change.

### Propagation Flow

1. User updates dimension value or rule
2. System identifies affected strings via `PropagationService`
3. Background jobs (via `PropagationJob` model) regenerate affected strings
4. Cache invalidation ensures fresh data

### Key Files

- `master_data/services/propagation_service.py` - Core propagation logic
- `master_data/signals/string_propagation.py` - Automatic propagation triggers
- `master_data/tasks/propagation_tasks.py` - Background job processing

## API Documentation

### Swagger/OpenAPI

- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
- **Schema**: `/api/schema/`

### Admin Interface

- **URL**: `/admin/`
- Full CRUD interface for all models
- User and workspace management

## Testing Strategy

### Test Organization

- Unit tests in `master_data/tests/`
- Specific test files for major features:
  - `test_propagation_service.py` - String propagation logic
  - `test_phase4_batch_operations.py` - Batch operations
  - `test_dimension_catalog.py` - Dimension management

### Test Database

Tests use separate test database automatically managed by Django test runner.
