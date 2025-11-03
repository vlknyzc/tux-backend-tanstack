# Frontend API Endpoints List

This document lists all API endpoints used by the frontend. Use this list to compare with backend endpoints and identify unused endpoints that can be cleaned up.

## Authentication Endpoints

- `POST /jwt/create/` - Login (creates JWT tokens)
- `POST /jwt/logout/` - Logout
- `POST /jwt/refresh/` - Refresh access token
- `GET /health/` - Health check endpoint

## User Management

### Current User
- `GET /users/me/` - Get current user profile
- `PATCH /users/me/` - Update current user profile

### All Users (Admin)
- `GET /users/` - Get all users (admin only)
- `POST /users/` - Create new user (admin only)
- `PATCH /users/{userId}/` - Update user (admin only)
- `DELETE /users/{userId}/` - Delete user (admin only)

## Workspaces

### Workspace Management
- `GET /workspaces/` - List all workspaces (with optional filters)
- `GET /workspaces/{workspaceId}/` - Get workspace by ID
- `POST /workspaces/` - Create workspace (superuser only)
- `PUT /workspaces/{workspaceId}/` - Update workspace
- `DELETE /workspaces/{workspaceId}/` - Delete workspace (superuser only)
- `GET /workspaces/stats/` - Get workspace statistics
- `GET /workspaces/{workspaceId}/stats/` - Get specific workspace statistics
- `POST /workspaces/{workspaceId}/switch/` - Switch workspace context

### Workspace Users
- `GET /workspace-users/` - Get workspace users (with filters: workspace, user)
- `POST /workspace-users/` - Add user to workspace
- `PUT /workspace-users/{assignmentId}/` - Update workspace user role
- `DELETE /workspace-users/{assignmentId}/` - Remove user from workspace
- `POST /workspaces/{workspaceId}/users/invite/` - Invite user to workspace

## Invitations

- `GET /invitations/` - List invitations (with filters: workspaceId, email, status)
- `POST /invitations/` - Create invitation
- `GET /invitations/{token}/validate/` - Validate invitation token (public)
- `POST /register-via-invitation/` - Accept invitation and register (public)
- `DELETE /invitations/{invitationId}/` - Revoke invitation
- `POST /invitations/{invitationId}/resend/` - Resend invitation email
- `GET /invitations/stats/` - Get invitation statistics

## Dimensions

### Dimension Management
- `GET /workspaces/{workspaceId}/dimensions/` - List dimensions (with filters)
- `GET /workspaces/{workspaceId}/dimensions/{dimensionId}/` - Get dimension by ID
- `POST /workspaces/{workspaceId}/dimensions/` - Create dimension
- `PUT /workspaces/{workspaceId}/dimensions/{dimensionId}/` - Update dimension
- `DELETE /workspaces/{workspaceId}/dimensions/{dimensionId}/` - Delete dimension
- `POST /workspaces/{workspaceId}/dimensions/bulk_create/` - Bulk create dimensions

### Dimension Utilities
- `GET /workspaces/{workspaceId}/dimensions/{dimensionId}/hierarchy/` - Get dimension hierarchy
- `GET /workspaces/{workspaceId}/dimensions/{dimensionId}/usage/` - Get dimension usage statistics
- `GET /workspaces/{workspaceId}/dimensions/{dimensionId}/value-stats/` - Get dimension value statistics
- `GET /workspaces/{workspaceId}/dimensions/workspace_summary/` - Get workspace dimension summary
- `GET /workspaces/{workspaceId}/dimensions/stats/` - Get dimension statistics

## Dimension Values

### Dimension Value Management
- `GET /workspaces/{workspaceId}/dimension-values/` - List dimension values (with filters)
- `GET /workspaces/{workspaceId}/dimension-values/{dimensionValueId}/` - Get dimension value by ID
- `POST /workspaces/{workspaceId}/dimension-values/` - Create dimension value
- `PUT /workspaces/{workspaceId}/dimension-values/{dimensionValueId}/` - Update dimension value
- `DELETE /workspaces/{workspaceId}/dimension-values/{dimensionValueId}/` - Delete dimension value
- `POST /workspaces/{workspaceId}/dimension-values/bulk_create/` - Bulk create dimension values
- `POST /workspaces/{workspaceId}/dimension-values/bulk-update-parents/` - Bulk update parent assignments
- `POST /workspaces/{workspaceId}/dimension-values/bulk_update/` - Bulk update dimension values
- `POST /workspaces/{workspaceId}/dimension-values/bulk_delete/` - Bulk delete dimension values

### Dimension Value Utilities
- `GET /workspaces/{workspaceId}/dimension-values/{dimensionValueId}/usage/` - Check if dimension value is in use

## Dimension Constraints

- `GET /workspaces/{workspaceId}/dimension-constraints/` - List dimension constraints
- `GET /workspaces/{workspaceId}/dimension-constraints/by-dimension/{dimensionId}/` - Get constraints for a dimension
- `GET /workspaces/{workspaceId}/dimension-constraints/{constraintId}/` - Get constraint by ID
- `POST /workspaces/{workspaceId}/dimension-constraints/` - Create dimension constraint
- `PUT /workspaces/{workspaceId}/dimension-constraints/{constraintId}/` - Update dimension constraint
- `DELETE /workspaces/{workspaceId}/dimension-constraints/{constraintId}/` - Delete dimension constraint
- `POST /workspaces/{workspaceId}/dimension-constraints/bulk-create/{dimensionId}/` - Bulk create constraints
- `PUT /workspaces/{workspaceId}/dimension-constraints/reorder/{dimensionId}/` - Reorder constraints
- `POST /workspaces/{workspaceId}/dimension-constraints/validate/{dimensionId}/` - Validate value against constraints
- `GET /workspaces/{workspaceId}/dimension-constraints/violations/{dimensionId}/` - Check for constraint violations

## Platforms

- `GET /platforms/` - List platforms (with filters)
- `GET /platforms/{platformId}/` - Get platform by ID
- `POST /platforms/` - Create platform
- `PUT /platforms/{platformId}/` - Update platform
- `DELETE /platforms/{platformId}/` - Delete platform
- `GET /platforms/{platformId}/with-fields/` - Get platform with fields
- `GET /platforms/stats/` - Get platform statistics

## Fields

- `GET /fields/` - List fields (with filters: platform, fieldLevel, search)
- `GET /fields/{fieldId}/` - Get field by ID
- `POST /fields/` - Create field
- `PUT /fields/{fieldId}/` - Update field
- `DELETE /fields/{fieldId}/` - Delete field

## Rules

### Rule Management
- `GET /workspaces/{workspaceId}/rules/` - List rules (with filters)
- `GET /workspaces/{workspaceId}/rules/{ruleId}/` - Get rule by ID
- `POST /workspaces/{workspaceId}/rules/` - Create rule
- `PUT /workspaces/{workspaceId}/rules/{ruleId}/` - Update rule
- `DELETE /workspaces/{workspaceId}/rules/{ruleId}/` - Delete rule
- `POST /workspaces/{workspaceId}/rules/{ruleId}/set_default/` - Set rule as default
- `GET /workspaces/{workspaceId}/rules/{ruleId}/validate/` - Get rule validation
- `POST /workspaces/{workspaceId}/rules/{ruleId}/preview/` - Preview rule generation
- `POST /workspaces/{workspaceId}/rules/{ruleId}/clone/` - Clone rule
- `GET /workspaces/{workspaceId}/rules/stats/` - Get rule statistics

### Rule Configuration
- `GET /workspaces/{workspaceId}/rules/{ruleId}/configuration/` - Get rule configuration
- `GET /workspaces/{workspaceId}/rules/{ruleId}/fields/{fieldId}/` - Get field configuration

### Rule Details
- `GET /workspaces/{workspaceId}/rule-details/` - List rule details (with filters)
- `GET /workspaces/{workspaceId}/rule-details/{ruleDetailId}/` - Get rule detail by ID
- `POST /workspaces/{workspaceId}/rule-details/` - Create rule detail
- `PUT /workspaces/{workspaceId}/rule-details/{ruleDetailId}/` - Update rule detail
- `DELETE /workspaces/{workspaceId}/rule-details/{ruleDetailId}/` - Delete rule detail
- `POST /workspaces/{workspaceId}/rule-details/batch/` - Batch create rule details
- `PUT /workspaces/{workspaceId}/rule-details/batch/` - Batch update rule details
- `GET /workspaces/{workspaceId}/rule-details/validate/` - Validate rule detail configuration

### Nested Rules
- `GET /workspaces/{workspaceId}/rule-nested/` - List nested rules (with filters)
- `GET /workspaces/{workspaceId}/rule-nested/{ruleNestedId}/` - Get nested rule by ID
- `POST /workspaces/{workspaceId}/rule-nested/` - Create nested rule
- `PUT /workspaces/{workspaceId}/rule-nested/{ruleNestedId}/` - Update nested rule
- `DELETE /workspaces/{workspaceId}/rule-nested/{ruleNestedId}/` - Delete nested rule

## Projects

### Project Management
- `GET /workspaces/{workspaceId}/projects/` - List projects (with filters: status, search, page, page_size)
- `GET /workspaces/{workspaceId}/projects/{projectId}/` - Get project by ID
- `POST /workspaces/{workspaceId}/projects/` - Create project
- `PUT /workspaces/{workspaceId}/projects/{projectId}/` - Update project
- `DELETE /workspaces/{workspaceId}/projects/{projectId}/` - Delete project

### Project Approval
- `POST /workspaces/{workspaceId}/projects/{projectId}/submit-for-approval/` - Submit project for approval
- `POST /workspaces/{workspaceId}/projects/{projectId}/approve/` - Approve project
- `POST /workspaces/{workspaceId}/projects/{projectId}/reject/` - Reject project

### Platform Approval
- `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/submit-for-approval/` - Submit platform for approval
- `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/approve/` - Approve platform
- `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/reject/` - Reject platform

### Project Strings
- `GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/` - List project strings (with filters)
- `GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/expanded/` - Get expanded string details
- `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk/` - Bulk create project strings
- `PUT /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/` - Update project string
- `DELETE /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/delete/` - Delete project string
- `PUT /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/bulk-update/` - Bulk update project strings
- `GET /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/export/` - Export strings (CSV/JSON)

### Project String Utilities
- `POST /workspaces/{workspaceId}/projects/{projectId}/platforms/{platformId}/strings/{stringId}/unlock/` - Unlock string for editing

## Strings (Workspace-scoped)

- `GET /workspaces/{workspaceId}/strings/` - List strings (with filters: field, rule, search)
- `GET /workspaces/{workspaceId}/strings/{stringId}/` - Get string by ID
- `POST /workspaces/{workspaceId}/strings/` - Create string
- `PATCH /workspaces/{workspaceId}/strings/{stringId}/` - Update string
- `PUT /workspaces/{workspaceId}/strings/{stringId}/` - Update string (alternative)
- `DELETE /workspaces/{workspaceId}/strings/{stringId}/` - Delete string

## String Details (Workspace-scoped)

- `PATCH /workspaces/{workspaceId}/string-details/{detailId}/` - Update single string detail
- `PATCH /workspaces/{workspaceId}/string-details/bulk-update/` - Bulk update string details
- `POST /workspaces/{workspaceId}/string-details/bulk-create/` - Bulk create string details
- `DELETE /workspaces/{workspaceId}/string-details/bulk-delete/` - Bulk delete string details

## Multi-Operations

- `POST /workspaces/{workspaceId}/multi-operations/execute/` - Execute multiple operations in a transaction
- `POST /workspaces/{workspaceId}/multi-operations/validate/` - Validate operations without executing

## String Updates (Advanced - May not be fully implemented)

- `PUT /strings/batch_update/` - Batch update strings with inheritance management
- `POST /strings/analyze_impact/` - Analyze inheritance impact before updates
- `GET /strings/{stringId}/history/` - Get string modification history
- `POST /strings/rollback/` - Rollback strings to previous versions

## Notes

1. **Workspace Context**: Most endpoints are workspace-scoped and require `{workspaceId}` in the path
2. **Query Parameters**: Many GET endpoints support optional query parameters for filtering, pagination, and search
3. **Bulk Operations**: Multiple bulk operation endpoints are available for efficient batch processing
4. **Authentication**: All endpoints (except public auth endpoints) require JWT authentication via `Authorization: JWT <token>` header
5. **Base URL**: All endpoints are prefixed with `/api/v1/` (configured in apiClient)
6. **String Updates**: Some advanced string update endpoints may have simulation fallbacks if not fully implemented in backend

## Endpoint Summary by Resource

| Resource | GET | POST | PUT | PATCH | DELETE | Count |
|----------|-----|------|-----|-------|--------|-------|
| Authentication | 1 | 3 | 0 | 0 | 0 | 4 |
| Users | 2 | 1 | 0 | 1 | 1 | 5 |
| Workspaces | 4 | 3 | 1 | 0 | 1 | 9 |
| Workspace Users | 1 | 1 | 1 | 0 | 1 | 4 |
| Invitations | 3 | 3 | 0 | 0 | 1 | 7 |
| Dimensions | 7 | 2 | 1 | 0 | 1 | 11 |
| Dimension Values | 3 | 3 | 1 | 0 | 1 | 8 |
| Dimension Constraints | 4 | 2 | 1 | 0 | 1 | 8 |
| Platforms | 3 | 1 | 1 | 0 | 1 | 6 |
| Fields | 2 | 1 | 1 | 0 | 1 | 5 |
| Rules | 4 | 3 | 1 | 0 | 1 | 9 |
| Rule Configuration | 2 | 0 | 0 | 0 | 0 | 2 |
| Rule Details | 4 | 2 | 1 | 0 | 1 | 8 |
| Nested Rules | 2 | 1 | 1 | 0 | 1 | 5 |
| Projects | 2 | 4 | 1 | 0 | 1 | 8 |
| Project Strings | 2 | 1 | 2 | 0 | 1 | 6 |
| Workspace Strings | 2 | 1 | 0 | 1 | 1 | 5 |
| String Details | 0 | 1 | 0 | 1 | 1 | 3 |
| Multi-Operations | 0 | 2 | 0 | 0 | 0 | 2 |
| String Updates | 1 | 2 | 1 | 0 | 0 | 4 |
| **Total** | **50** | **34** | **13** | **3** | **15** | **115** |

**Total Unique Endpoints: 115**

