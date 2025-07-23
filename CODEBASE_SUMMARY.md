# TUX Backend - Codebase Summary

## Overview
TUX Backend is a Django REST API application designed for managing naming conventions and rules across different platforms in a multi-tenant environment. The system provides workspace-based organization for managing dimensions, rules, fields, and string generation for various cloud platforms and environments.

## Architecture

### Technology Stack
- **Framework**: Django 4.2.20 with Django REST Framework 3.16.0
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: JWT tokens with djoser, session-based auth
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Deployment**: Railway with Gunicorn, AWS SES for email
- **Storage**: WhiteNoise for static files, potential S3 integration

### Core Architecture Patterns
- **Multi-tenant**: Workspace-based data isolation with role-based access control
- **Audit Trail**: TimeStampModel base class provides created/updated timestamps and user tracking
- **Thread-local Context**: Workspace context management using thread-local storage
- **Service Layer**: Business logic separated into service classes
- **API Versioning**: URL path versioning (v1, v2)

## Core Domain Models

### Workspace Management
- **Workspace**: Central tenant entity with name, slug, logo, and status
- **UserAccount**: Custom user model with email-based authentication
- **WorkspaceUser**: Junction table managing user-workspace relationships with roles (admin, user, viewer)

### Master Data Models
- **Platform**: Target environments (AWS, Azure, Kubernetes) - workspace-agnostic
- **Dimension**: Categorization entities (environment, region, cost center) with hierarchical support
- **DimensionValue**: Specific values within dimensions
- **Field**: Template components for naming patterns
- **Rule**: Naming convention rules with platform associations
- **RuleDetail**: Detailed rule configurations linking fields and dimensions
- **String**: Generated naming strings based on rules
- **StringDetail**: Components that make up generated strings
- **Submission**: User submission tracking for rule applications

## Key Features

### Multi-Tenancy Implementation
- Workspace-based data isolation using WorkspaceMixin
- Automatic workspace filtering via custom WorkspaceManager
- Thread-local workspace context for request-scoped filtering
- Role-based permissions (admin, user, viewer)
- Superuser bypass for cross-workspace access

### Business Logic Services
- **RuleService**: Core rule processing and validation
- **StringGenerationService**: Automated string generation based on rules
- **DimensionCatalogService**: Dimension management and organization
- **FieldTemplateService**: Field template processing
- **InheritanceMatrixService**: Hierarchical dimension inheritance
- **NamingPatternValidator**: Validation of naming patterns

### API Design
- RESTful endpoints with consistent versioning
- Comprehensive filtering using django-filter
- Pagination and search capabilities
- API documentation via Swagger/OpenAPI
- CORS support for frontend integration

## File Structure Highlights

### Core Django Structure
- `main/`: Django project configuration with environment-specific settings
- `master_data/`: Primary application containing all business logic
- `users/`: Custom user management and workspace relationships

### Key Directories
- `master_data/models/`: Domain models with clear separation of concerns
- `master_data/services/`: Business logic services
- `master_data/serializers/`: API serialization logic
- `master_data/views/`: API viewsets and endpoints
- `docs/`: Comprehensive API documentation
- `static/`: Static file management

## Security & Configuration
- Environment-based configuration (local vs production)
- Secret key management for different environments
- CORS configuration for cross-origin requests
- JWT token authentication with refresh capability
- Database connection security for PostgreSQL

## Testing & Development
- Test structure in place (`tests/` directories)
- Development vs production environment separation
- Database migration management
- Management commands for workspace and user setup

## Notable Design Decisions

### Workspace Context Management
The system uses thread-local storage to maintain workspace context throughout request processing, enabling automatic filtering without explicit workspace parameters in every query.

### Model Inheritance Strategy
- TimeStampModel for audit trails
- WorkspaceMixin for multi-tenancy
- Custom managers for workspace-aware queries

### Service Layer Pattern
Business logic is extracted into dedicated service classes, keeping views thin and promoting reusability.

### API Versioning Strategy
URL-path versioning allows for backward compatibility while supporting future API evolution.

## Current State
The codebase appears to be in active development with recent commits focusing on rule updates and nested submissions. The architecture supports a scalable multi-tenant naming convention management system with comprehensive API capabilities.