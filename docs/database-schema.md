# TUX Backend Database Schema Documentation

## Overview

This document provides a comprehensive overview of the database schema for the TUX backend system. The system uses Django ORM with PostgreSQL and implements a multi-tenant architecture based on workspaces.

## Database Architecture

The system follows a multi-tenant architecture where:

- **Workspaces** are the primary isolation mechanism
- Most models inherit from `WorkspaceMixin` for automatic workspace filtering
- **Platforms** and **Fields** are shared globally across all workspaces
- **Users** can belong to multiple workspaces with different roles

## Base Models

### TimeStampModel (Abstract)

Base model providing audit fields for all models.

| Field          | Type             | Description                                 |
| -------------- | ---------------- | ------------------------------------------- |
| `created`      | DateTimeField    | When the record was created (auto_now_add)  |
| `last_updated` | DateTimeField    | When the record was last updated (auto_now) |
| `created_by`   | ForeignKey(User) | User who created the record (nullable)      |

### WorkspaceMixin (Abstract)

Mixin providing workspace relationship and automatic filtering.

| Field       | Type                  | Description                      |
| ----------- | --------------------- | -------------------------------- |
| `workspace` | ForeignKey(Workspace) | Workspace this record belongs to |

## Core Tables

### 1. Workspace

Represents a logical grouping or organization unit.

| Field          | Type             | Constraints              | Description             |
| -------------- | ---------------- | ------------------------ | ----------------------- |
| `id`           | AutoField        | Primary Key              | Unique identifier       |
| `name`         | CharField(100)   | Unique                   | Workspace name          |
| `slug`         | SlugField(50)    | Unique, Auto-generated   | URL-friendly identifier |
| `logo`         | ImageField       | Nullable                 | Workspace logo image    |
| `status`       | CharField(100)   | Choices: ACTIVE/INACTIVE | Current status          |
| `created`      | DateTimeField    | Auto                     | Creation timestamp      |
| `last_updated` | DateTimeField    | Auto                     | Last update timestamp   |
| `created_by`   | ForeignKey(User) | Nullable                 | Creator user            |

**Relationships:**

- Has many: `Platform`, `Field`, `Dimension`, `Rule`, `String`, `Submission`, etc.

### 2. Platform

Represents different platforms where naming conventions apply (shared globally).

| Field           | Type             | Constraints | Description             |
| --------------- | ---------------- | ----------- | ----------------------- |
| `id`            | AutoField        | Primary Key | Unique identifier       |
| `platform_type` | CharField(100)   | Required    | Platform category       |
| `name`          | CharField(100)   | Required    | Human-readable name     |
| `slug`          | SlugField(50)    | Unique      | URL-friendly identifier |
| `icon_name`     | CharField(100)   | Nullable    | Icon name for display   |
| `created`       | DateTimeField    | Auto        | Creation timestamp      |
| `last_updated`  | DateTimeField    | Auto        | Last update timestamp   |
| `created_by`    | ForeignKey(User) | Nullable    | Creator user            |

**Relationships:**

- Has many: `Field`, `Rule`

### 3. Field

Represents hierarchical components of naming conventions (shared globally).

| Field          | Type                 | Constraints | Description                        |
| -------------- | -------------------- | ----------- | ---------------------------------- |
| `id`           | AutoField            | Primary Key | Unique identifier                  |
| `platform`     | ForeignKey(Platform) | Required    | Platform this field belongs to     |
| `next_field`   | ForeignKey(Field)    | Nullable    | Next field in hierarchy            |
| `name`         | CharField(100)       | Required    | Field name (e.g., 'environment')   |
| `field_level`  | SmallIntegerField    | Required    | Hierarchical level (1, 2, 3, etc.) |
| `created`      | DateTimeField        | Auto        | Creation timestamp                 |
| `last_updated` | DateTimeField        | Auto        | Last update timestamp              |
| `created_by`   | ForeignKey(User)     | Nullable    | Creator user                       |

**Relationships:**

- Belongs to: `Platform`
- Has one: `next_field` (self-referencing)
- Has many: `child_fields` (reverse of next_field)
- Has many: `RuleDetail`, `String`

**Constraints:**

- Unique together: `(platform, name, field_level)`

### 4. Dimension

Represents categories for structuring naming conventions (workspace-scoped).

| Field          | Type                  | Constraints              | Description               |
| -------------- | --------------------- | ------------------------ | ------------------------- |
| `id`           | AutoField             | Primary Key              | Unique identifier         |
| `workspace`    | ForeignKey(Workspace) | Required                 | Workspace this belongs to |
| `parent`       | ForeignKey(Dimension) | Nullable                 | Parent dimension          |
| `name`         | CharField(100)        | Required                 | Dimension name            |
| `slug`         | SlugField(50)         | Auto-generated           | URL-friendly identifier   |
| `description`  | TextField             | Nullable                 | Description               |
| `type`         | CharField(100)        | Choices: LIST/TEXT       | Dimension type            |
| `status`       | CharField(100)        | Choices: ACTIVE/INACTIVE | Current status            |
| `created`      | DateTimeField         | Auto                     | Creation timestamp        |
| `last_updated` | DateTimeField         | Auto                     | Last update timestamp     |
| `created_by`   | ForeignKey(User)      | Nullable                 | Creator user              |

**Relationships:**

- Belongs to: `Workspace`
- Has one: `parent` (self-referencing)
- Has many: `child_dimensions` (reverse of parent)
- Has many: `DimensionValue`, `RuleDetail`, `StringDetail`

**Constraints:**

- Unique together: `(workspace, name)`

### 5. DimensionValue

Represents specific values within dimensions (workspace-scoped).

| Field          | Type                       | Constraints | Description               |
| -------------- | -------------------------- | ----------- | ------------------------- |
| `id`           | AutoField                  | Primary Key | Unique identifier         |
| `workspace`    | ForeignKey(Workspace)      | Required    | Workspace this belongs to |
| `dimension`    | ForeignKey(Dimension)      | Required    | Parent dimension          |
| `parent`       | ForeignKey(DimensionValue) | Nullable    | Parent value              |
| `value`        | CharField(100)             | Required    | The actual value          |
| `label`        | CharField(200)             | Required    | Human-readable label      |
| `utm`          | CharField(50)              | Required    | UTM tracking code         |
| `description`  | TextField                  | Nullable    | Description               |
| `valid_from`   | DateField                  | Nullable    | Valid from date           |
| `valid_until`  | DateField                  | Nullable    | Valid until date          |
| `created`      | DateTimeField              | Auto        | Creation timestamp        |
| `last_updated` | DateTimeField              | Auto        | Last update timestamp     |
| `created_by`   | ForeignKey(User)           | Nullable    | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `Dimension`
- Has one: `parent` (self-referencing)
- Has many: `child_dimension_values` (reverse of parent)
- Has many: `StringDetail`

**Constraints:**

- Unique together: `(workspace, dimension, value)`

## Rule Management Tables

### 6. Rule

Represents naming convention rules for platforms (workspace-scoped).

| Field          | Type                  | Constraints              | Description                      |
| -------------- | --------------------- | ------------------------ | -------------------------------- |
| `id`           | AutoField             | Primary Key              | Unique identifier                |
| `workspace`    | ForeignKey(Workspace) | Required                 | Workspace this belongs to        |
| `platform`     | ForeignKey(Platform)  | Required                 | Platform this rule applies to    |
| `name`         | CharField(200)        | Required                 | Rule name                        |
| `slug`         | SlugField(50)         | Auto-generated           | URL-friendly identifier          |
| `description`  | TextField             | Nullable                 | Description                      |
| `status`       | CharField(100)        | Choices: ACTIVE/INACTIVE | Current status                   |
| `is_default`   | BooleanField          | Default: False           | Whether this is the default rule |
| `created`      | DateTimeField         | Auto                     | Creation timestamp               |
| `last_updated` | DateTimeField         | Auto                     | Last update timestamp            |
| `created_by`   | ForeignKey(User)      | Nullable                 | Creator user                     |

**Relationships:**

- Belongs to: `Workspace`, `Platform`
- Has many: `RuleDetail`, `String`, `Submission`

**Constraints:**

- Unique together: `(workspace, platform, name)`

### 7. RuleDetail

Represents detailed configuration for rule formatting (workspace-scoped).

| Field             | Type                  | Constraints   | Description               |
| ----------------- | --------------------- | ------------- | ------------------------- |
| `id`              | AutoField             | Primary Key   | Unique identifier         |
| `workspace`       | ForeignKey(Workspace) | Required      | Workspace this belongs to |
| `rule`            | ForeignKey(Rule)      | Required      | Parent rule               |
| `field`           | ForeignKey(Field)     | Required      | Field this applies to     |
| `dimension`       | ForeignKey(Dimension) | Required      | Dimension this applies to |
| `prefix`          | CharField(20)         | Nullable      | Text to prepend           |
| `suffix`          | CharField(20)         | Nullable      | Text to append            |
| `delimiter`       | CharField(10)         | Default: '-'  | Separator character       |
| `dimension_order` | SmallIntegerField     | Required      | Order in sequence         |
| `is_required`     | BooleanField          | Default: True | Whether required          |
| `created`         | DateTimeField         | Auto          | Creation timestamp        |
| `last_updated`    | DateTimeField         | Auto          | Last update timestamp     |
| `created_by`      | ForeignKey(User)      | Nullable      | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `Rule`, `Field`, `Dimension`

**Constraints:**

- Unique together: `(workspace, rule, field, dimension, dimension_order)`

## String Generation Tables

### 8. String

Represents generated naming strings (workspace-scoped).

| Field                 | Type                   | Constraints    | Description                    |
| --------------------- | ---------------------- | -------------- | ------------------------------ |
| `id`                  | AutoField              | Primary Key    | Unique identifier              |
| `workspace`           | ForeignKey(Workspace)  | Required       | Workspace this belongs to      |
| `parent`              | ForeignKey(String)     | Nullable       | Parent string in hierarchy     |
| `field`               | ForeignKey(Field)      | Required       | Field this string belongs to   |
| `submission`          | ForeignKey(Submission) | Required       | Submission that generated this |
| `rule`                | ForeignKey(Rule)       | Required       | Rule used for generation       |
| `value`               | CharField(255)         | Required       | Generated string value         |
| `string_uuid`         | UUIDField              | Unique         | Unique identifier              |
| `parent_uuid`         | UUIDField              | Nullable       | Parent UUID for linking        |
| `is_auto_generated`   | BooleanField           | Default: False | Whether auto-generated         |
| `generation_metadata` | JSONField              | Default: {}    | Generation metadata            |
| `version`             | IntegerField           | Default: 1     | Version number                 |
| `created`             | DateTimeField          | Auto           | Creation timestamp             |
| `last_updated`        | DateTimeField          | Auto           | Last update timestamp          |
| `created_by`          | ForeignKey(User)       | Nullable       | Creator user                   |

**Relationships:**

- Belongs to: `Workspace`, `Field`, `Submission`, `Rule`
- Has one: `parent` (self-referencing)
- Has many: `child_strings` (reverse of parent)
- Has many: `StringDetail`, `StringModification`, `PropagationError`

**Constraints:**

- Unique together: `(workspace, rule, field, value)`

### 9. StringDetail

Represents dimension values used in string generation (workspace-scoped).

| Field                      | Type                       | Constraints | Description               |
| -------------------------- | -------------------------- | ----------- | ------------------------- |
| `id`                       | AutoField                  | Primary Key | Unique identifier         |
| `workspace`                | ForeignKey(Workspace)      | Required    | Workspace this belongs to |
| `string`                   | ForeignKey(String)         | Required    | Parent string             |
| `dimension`                | ForeignKey(Dimension)      | Required    | Dimension this represents |
| `dimension_value`          | ForeignKey(DimensionValue) | Nullable    | Predefined value          |
| `dimension_value_freetext` | CharField(255)             | Nullable    | Free-text value           |
| `created`                  | DateTimeField              | Auto        | Creation timestamp        |
| `last_updated`             | DateTimeField              | Auto        | Last update timestamp     |
| `created_by`               | ForeignKey(User)           | Nullable    | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `String`, `Dimension`, `DimensionValue`
- Has many: `PropagationError`

**Constraints:**

- Unique together: `(workspace, string, dimension)`
- Either `dimension_value` or `dimension_value_freetext` must be provided

### 10. Submission

Represents submissions for naming convention generation (workspace-scoped).

| Field                    | Type                  | Constraints                                | Description               |
| ------------------------ | --------------------- | ------------------------------------------ | ------------------------- |
| `id`                     | AutoField             | Primary Key                                | Unique identifier         |
| `workspace`              | ForeignKey(Workspace) | Required                                   | Workspace this belongs to |
| `rule`                   | ForeignKey(Rule)      | Required                                   | Naming rule to apply      |
| `selected_parent_string` | ForeignKey(String)    | Nullable                                   | Parent string             |
| `starting_field`         | ForeignKey(Field)     | Required                                   | Starting field            |
| `name`                   | CharField(100)        | Required                                   | Submission name           |
| `slug`                   | SlugField(50)         | Auto-generated                             | URL-friendly identifier   |
| `description`            | TextField             | Nullable                                   | Description               |
| `status`                 | CharField(100)        | Choices: DRAFT/SUBMITTED/APPROVED/REJECTED | Status                    |
| `created`                | DateTimeField         | Auto                                       | Creation timestamp        |
| `last_updated`           | DateTimeField         | Auto                                       | Last update timestamp     |
| `created_by`             | ForeignKey(User)      | Nullable                                   | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `Rule`, `Field`
- Has many: `String`

**Constraints:**

- Unique together: `(workspace, name)`

## Audit and Tracking Tables

### 11. StringModification

Tracks modifications to strings for audit trail (workspace-scoped).

| Field             | Type                           | Constraints | Description                         |
| ----------------- | ------------------------------ | ----------- | ----------------------------------- |
| `id`              | UUIDField                      | Primary Key | Unique identifier                   |
| `workspace`       | ForeignKey(Workspace)          | Required    | Workspace this belongs to           |
| `string`          | ForeignKey(String)             | Required    | Modified string                     |
| `version`         | IntegerField                   | Required    | Version number                      |
| `field_updates`   | JSONField                      | Required    | Field updates made                  |
| `string_value`    | TextField                      | Required    | String value after modification     |
| `original_values` | JSONField                      | Required    | Original values before modification |
| `modified_by`     | ForeignKey(User)               | Required    | User who made modification          |
| `modified_at`     | DateTimeField                  | Auto        | Modification timestamp              |
| `change_type`     | CharField(50)                  | Choices     | Type of change                      |
| `batch_id`        | UUIDField                      | Nullable    | Batch operation ID                  |
| `parent_version`  | ForeignKey(StringModification) | Nullable    | Parent version                      |
| `metadata`        | JSONField                      | Default: {} | Additional metadata                 |
| `created`         | DateTimeField                  | Auto        | Creation timestamp                  |
| `last_updated`    | DateTimeField                  | Auto        | Last update timestamp               |
| `created_by`      | ForeignKey(User)               | Nullable    | Creator user                        |

**Relationships:**

- Belongs to: `Workspace`, `String`, `User`
- Has one: `parent_version` (self-referencing)
- Has many: `child_versions` (reverse of parent_version)
- Has many: `StringInheritanceUpdate`

**Constraints:**

- Unique together: `(string, version)`

### 12. StringInheritanceUpdate

Tracks inheritance updates when parent strings are modified (workspace-scoped).

| Field                 | Type                           | Constraints | Description               |
| --------------------- | ------------------------------ | ----------- | ------------------------- |
| `id`                  | UUIDField                      | Primary Key | Unique identifier         |
| `workspace`           | ForeignKey(Workspace)          | Required    | Workspace this belongs to |
| `parent_modification` | ForeignKey(StringModification) | Required    | Parent modification       |
| `child_string`        | ForeignKey(String)             | Required    | Child string              |
| `inherited_fields`    | JSONField                      | Required    | Inherited fields          |
| `applied_at`          | DateTimeField                  | Auto        | Application timestamp     |
| `created`             | DateTimeField                  | Auto        | Creation timestamp        |
| `last_updated`        | DateTimeField                  | Auto        | Last update timestamp     |
| `created_by`          | ForeignKey(User)               | Nullable    | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `StringModification`, `String`

**Constraints:**

- Unique together: `(parent_modification, child_string)`

### 13. StringUpdateBatch

Tracks batch update operations (workspace-scoped).

| Field               | Type                  | Constraints | Description               |
| ------------------- | --------------------- | ----------- | ------------------------- |
| `id`                | UUIDField             | Primary Key | Unique identifier         |
| `workspace`         | ForeignKey(Workspace) | Required    | Workspace this belongs to |
| `rule`              | ForeignKey(Rule)      | Required    | Rule being updated        |
| `field`             | ForeignKey(Field)     | Required    | Field being updated       |
| `initiated_by`      | ForeignKey(User)      | Required    | User who initiated        |
| `initiated_at`      | DateTimeField         | Auto        | Initiation timestamp      |
| `completed_at`      | DateTimeField         | Nullable    | Completion timestamp      |
| `status`            | CharField(20)         | Choices     | Current status            |
| `total_strings`     | IntegerField          | Required    | Total strings to update   |
| `processed_strings` | IntegerField          | Default: 0  | Successfully processed    |
| `failed_strings`    | IntegerField          | Default: 0  | Failed to process         |
| `backup_id`         | UUIDField             | Nullable    | Backup ID                 |
| `metadata`          | JSONField             | Default: {} | Additional metadata       |
| `created`           | DateTimeField         | Auto        | Creation timestamp        |
| `last_updated`      | DateTimeField         | Auto        | Last update timestamp     |
| `created_by`        | ForeignKey(User)      | Nullable    | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `Rule`, `Field`, `User`

## Propagation Tables

### 14. PropagationJob

Tracks string propagation operations (workspace-scoped).

| Field               | Type                  | Constraints | Description               |
| ------------------- | --------------------- | ----------- | ------------------------- |
| `id`                | AutoField             | Primary Key | Unique identifier         |
| `workspace`         | ForeignKey(Workspace) | Required    | Workspace this belongs to |
| `batch_id`          | UUIDField             | Unique      | Unique batch identifier   |
| `triggered_by`      | ForeignKey(User)      | Nullable    | User who triggered        |
| `status`            | CharField(20)         | Choices     | Current status            |
| `started_at`        | DateTimeField         | Nullable    | Start timestamp           |
| `completed_at`      | DateTimeField         | Nullable    | Completion timestamp      |
| `total_strings`     | PositiveIntegerField  | Default: 0  | Total to process          |
| `processed_strings` | PositiveIntegerField  | Default: 0  | Successfully processed    |
| `failed_strings`    | PositiveIntegerField  | Default: 0  | Failed to process         |
| `max_depth`         | PositiveIntegerField  | Default: 10 | Maximum depth             |
| `processing_method` | CharField(20)         | Choices     | Processing method         |
| `metadata`          | JSONField             | Default: {} | Additional metadata       |
| `error_message`     | TextField             | Nullable    | Error message             |
| `created`           | DateTimeField         | Auto        | Creation timestamp        |
| `last_updated`      | DateTimeField         | Auto        | Last update timestamp     |
| `created_by`        | ForeignKey(User)      | Nullable    | Creator user              |

**Relationships:**

- Belongs to: `Workspace`, `User`
- Has many: `PropagationError`

### 15. PropagationError

Tracks individual errors during propagation (workspace-scoped).

| Field           | Type                       | Constraints    | Description                    |
| --------------- | -------------------------- | -------------- | ------------------------------ |
| `id`            | AutoField                  | Primary Key    | Unique identifier              |
| `workspace`     | ForeignKey(Workspace)      | Required       | Workspace this belongs to      |
| `job`           | ForeignKey(PropagationJob) | Required       | Parent job                     |
| `string`        | ForeignKey(String)         | Nullable       | String that caused error       |
| `string_detail` | ForeignKey(StringDetail)   | Nullable       | StringDetail that caused error |
| `error_type`    | CharField(30)              | Choices        | Type of error                  |
| `error_message` | TextField                  | Required       | Error message                  |
| `error_code`    | CharField(50)              | Nullable       | Error code                     |
| `stack_trace`   | TextField                  | Nullable       | Stack trace                    |
| `context_data`  | JSONField                  | Default: {}    | Context data                   |
| `retry_count`   | PositiveIntegerField       | Default: 0     | Retry count                    |
| `is_retryable`  | BooleanField               | Default: False | Whether retryable              |
| `resolved`      | BooleanField               | Default: False | Whether resolved               |
| `resolved_at`   | DateTimeField              | Nullable       | Resolution timestamp           |
| `resolved_by`   | ForeignKey(User)           | Nullable       | User who resolved              |
| `created`       | DateTimeField              | Auto           | Creation timestamp             |
| `last_updated`  | DateTimeField              | Auto           | Last update timestamp          |
| `created_by`    | ForeignKey(User)           | Nullable       | Creator user                   |

**Relationships:**

- Belongs to: `Workspace`, `PropagationJob`, `String`, `StringDetail`, `User`

### 16. PropagationSettings

User and workspace-specific propagation settings (workspace-scoped).

| Field          | Type                  | Constraints | Description                   |
| -------------- | --------------------- | ----------- | ----------------------------- |
| `id`           | AutoField             | Primary Key | Unique identifier             |
| `workspace`    | ForeignKey(Workspace) | Required    | Workspace this belongs to     |
| `user`         | ForeignKey(User)      | Required    | User these settings belong to |
| `settings`     | JSONField             | Default: {} | User-specific settings        |
| `created`      | DateTimeField         | Auto        | Creation timestamp            |
| `last_updated` | DateTimeField         | Auto        | Last update timestamp         |
| `created_by`   | ForeignKey(User)      | Nullable    | Creator user                  |

**Relationships:**

- Belongs to: `Workspace`, `User`

**Constraints:**

- Unique together: `(user, workspace)`

## User Management Tables

### 17. UserAccount

Custom user model extending Django's AbstractBaseUser.

| Field          | Type            | Constraints    | Description            |
| -------------- | --------------- | -------------- | ---------------------- |
| `id`           | AutoField       | Primary Key    | Unique identifier      |
| `password`     | CharField(128)  | Required       | Hashed password        |
| `last_login`   | DateTimeField   | Nullable       | Last login timestamp   |
| `is_superuser` | BooleanField    | Default: False | Superuser status       |
| `first_name`   | CharField(255)  | Required       | First name             |
| `last_name`    | CharField(255)  | Required       | Last name              |
| `email`        | EmailField(255) | Unique         | Email address          |
| `is_staff`     | BooleanField    | Default: False | Staff status           |
| `is_active`    | BooleanField    | Default: True  | Active status          |
| `date_joined`  | DateTimeField   | Auto           | Registration timestamp |

**Relationships:**

- Has many: `WorkspaceUser` (through relationship)
- Has many: `Workspace` (through WorkspaceUser)
- Has many: `StringModification`, `StringUpdateBatch`, `PropagationJob`, `PropagationError`, `PropagationSettings`

### 18. WorkspaceUser

Through model for User-Workspace relationship with roles.

| Field       | Type                    | Constraints                | Description                  |
| ----------- | ----------------------- | -------------------------- | ---------------------------- |
| `id`        | AutoField               | Primary Key                | Unique identifier            |
| `user`      | ForeignKey(UserAccount) | Required                   | User                         |
| `workspace` | ForeignKey(Workspace)   | Required                   | Workspace                    |
| `role`      | CharField(20)           | Choices: ADMIN/USER/VIEWER | User role                    |
| `is_active` | BooleanField            | Default: True              | Whether assignment is active |
| `created`   | DateTimeField           | Auto                       | Creation timestamp           |
| `updated`   | DateTimeField           | Auto                       | Last update timestamp        |

**Relationships:**

- Belongs to: `UserAccount`, `Workspace`

**Constraints:**

- Unique together: `(user, workspace)`

## Key Relationships Summary

### Hierarchical Relationships

1. **Workspace** → **Dimension** → **DimensionValue** (parent-child)
2. **Platform** → **Field** → **Field** (next_field hierarchy)
3. **String** → **String** (parent-child hierarchy)
4. **StringModification** → **StringModification** (version hierarchy)

### Core Workflows

1. **Submission** → **Rule** → **RuleDetail** → **String** → **StringDetail**
2. **Platform** → **Field** → **Rule** → **String**
3. **Dimension** → **DimensionValue** → **StringDetail**

### Audit Trail

1. **String** → **StringModification** → **StringInheritanceUpdate**
2. **String** → **PropagationJob** → **PropagationError**

### User Access Control

1. **UserAccount** → **WorkspaceUser** → **Workspace**
2. **Workspace** → All workspace-scoped models

## Database Indexes

The system includes comprehensive indexing for performance:

### Primary Indexes

- All primary keys (AutoField/UUIDField)
- Unique constraints on slug fields
- Unique together constraints

### Performance Indexes

- Workspace filtering on all workspace-scoped models
- Status filtering on active/inactive records
- Date-based queries (created, last_updated)
- Foreign key relationships
- UUID-based lookups

### Composite Indexes

- `(workspace, platform, status)` on Rule
- `(workspace, rule, field)` on RuleDetail and String
- `(workspace, string_uuid)` on String
- `(workspace, status)` on PropagationJob

## Multi-Tenancy Implementation

The system implements multi-tenancy through:

1. **WorkspaceMixin**: Automatically filters queries by workspace
2. **WorkspaceManager**: Custom manager with workspace-aware filtering
3. **Thread-local storage**: Maintains current workspace context
4. **User permissions**: WorkspaceUser model controls access

## Data Integrity

The system maintains data integrity through:

1. **Foreign key constraints**: All relationships are properly constrained
2. **Unique constraints**: Prevents duplicate data where appropriate
3. **Validation**: Model-level validation ensures data consistency
4. **Audit trails**: Complete tracking of modifications and changes
5. **Cascade deletes**: Proper cleanup when parent records are deleted

## Migration Strategy

The database schema supports:

1. **Backward compatibility**: New fields are nullable where possible
2. **Data migration**: Comprehensive migration scripts
3. **Rollback capability**: Audit trails enable data recovery
4. **Versioning**: String modifications track all changes
