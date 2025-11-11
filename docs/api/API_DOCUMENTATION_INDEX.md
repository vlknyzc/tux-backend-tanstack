# API Documentation Index

Complete API documentation for Tuxonomy frontend integration.

---

## 📚 Documentation Files

### Core Documentation
1. **[README](./README.md)** - API Overview, Quick Start, Design Principles
2. **[Authentication](./01-authentication.md)** - JWT authentication, token management
3. **[Projects](./03-projects.md)** - Project CRUD, team management, approval workflows
4. **[Strings](./04-strings.md)** - String generation, CRUD, bulk operations, export
5. **[String Registry](./05-string-registry.md)** - External platform validation & import

### Coming Soon
- **Workspaces** - Multi-tenant workspace management
- **Platforms & Entities** - Platform and entity configuration
- **Dimensions** - Dimension and dimension value management
- **Rules** - Business rule configuration
- **Propagation** - String propagation and inheritance

---

## 🚀 Quick Navigation by Feature

### Authentication & Setup
- [Get JWT Token](./01-authentication.md#1-login-get-token)
- [Refresh Token](./01-authentication.md#2-refresh-token)
- [Using Tokens](./01-authentication.md#using-tokens-in-requests)

### Project Management
- [List Projects](./03-projects.md#list-projects)
- [Create Project](./03-projects.md#create-project)
- [Get Project Details](./03-projects.md#get-project-details)
- [Update Project](./03-projects.md#update-project)
- [Submit for Approval](./03-projects.md#submit-for-approval)
- [Approve/Reject Project](./03-projects.md#approve-project)

### String Management
- [List Strings](./04-strings.md#list-strings)
- [Create Strings (Bulk)](./04-strings.md#create-strings-bulk)
- [Get String Details](./04-strings.md#get-string-with-details)
- [Update String](./04-strings.md#update-string)
- [Delete String](./04-strings.md#delete-string)
- [Bulk Update](./04-strings.md#bulk-update-strings)
- [Export Strings](./04-strings.md#export-strings)

### External Platform Integration
- [Validate CSV](./05-string-registry.md#validate-only)
- [Import to Project](./05-string-registry.md#import-to-project)
- [Import Selected Strings](./05-string-registry.md#import-selected-strings)
- [Validate Single String](./05-string-registry.md#validate-single-string)
- [CSV Format Requirements](./05-string-registry.md#csv-format)

---

## 📋 Common Workflows

### 1. User Authentication Flow
```
Login → Get Tokens → Store Tokens → Use in Requests → Auto-Refresh
```
See: [Authentication Guide](./01-authentication.md)

### 2. Create Project & Add Strings
```
Create Project → Assign Platforms → Create Strings → Review → Submit for Approval
```
See: [Projects](./03-projects.md) + [Strings](./04-strings.md)

### 3. Import External Platform Strings
```
Upload CSV → Validate → Review Results → Import Selected → Track in Project
```
See: [String Registry Guide](./05-string-registry.md)

### 4. String Hierarchy Management
```
Create Parent String → Create Child Strings → Manage Inheritance → Export
```
See: [Strings Hierarchy](./04-strings.md#common-workflows)

---

## 🔗 API Endpoints Summary

### Authentication
- `POST /api/v1/token/` - Login
- `POST /api/v1/token/refresh/` - Refresh token
- `POST /api/v1/token/verify/` - Verify token

### Projects
- `GET /api/v1/workspaces/{id}/projects/` - List projects
- `POST /api/v1/workspaces/{id}/projects/` - Create project
- `GET /api/v1/workspaces/{id}/projects/{id}/` - Get project
- `PATCH /api/v1/workspaces/{id}/projects/{id}/` - Update project
- `DELETE /api/v1/workspaces/{id}/projects/{id}/` - Delete project
- `POST /api/v1/workspaces/{id}/projects/{id}/submit/` - Submit for approval
- `POST /api/v1/workspaces/{id}/projects/{id}/approve/` - Approve
- `POST /api/v1/workspaces/{id}/projects/{id}/reject/` - Reject

### Strings
- `GET /workspaces/{id}/projects/{id}/platforms/{id}/strings` - List strings
- `POST /workspaces/{id}/projects/{id}/platforms/{id}/strings/bulk` - Create strings
- `GET /workspaces/{id}/projects/{id}/platforms/{id}/strings/{id}/expanded` - Get details
- `PUT /workspaces/{id}/projects/{id}/platforms/{id}/strings/{id}` - Update string
- `DELETE /workspaces/{id}/projects/{id}/platforms/{id}/strings/{id}/delete` - Delete string
- `POST /workspaces/{id}/projects/{id}/platforms/{id}/strings/{id}/unlock` - Unlock string
- `POST /workspaces/{id}/projects/{id}/platforms/{id}/strings/bulk-update` - Bulk update
- `GET /workspaces/{id}/projects/{id}/platforms/{id}/strings/export` - Export

### String Registry
- `POST /api/v1/workspaces/{id}/string-registry/validate/` - Validate CSV
- `POST /api/v1/workspaces/{id}/string-registry/import/` - Import to project
- `POST /api/v1/workspaces/{id}/string-registry/import-selected/` - Import selected
- `POST /api/v1/workspaces/{id}/string-registry/validate_single/` - Validate single

---

## 🛠️ Development Tools

### Postman Collection
Import the collection for easy API testing:
- **File**: `string-registry.postman_collection.json`
- **Location**: Root directory

### OpenAPI Schema
- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **Schema File**: `schema.yml`

---

## 📝 Code Examples

All documentation includes:
- ✅ cURL examples for testing
- ✅ JavaScript/Fetch examples
- ✅ Axios integration examples
- ✅ Complete request/response samples
- ✅ Error handling patterns
- ✅ Common workflow implementations

---

## 🎯 Frontend Integration Checklist

### Setup Phase
- [ ] Set up API base URL configuration
- [ ] Implement authentication service (login, refresh, logout)
- [ ] Create API client with interceptors
- [ ] Set up token storage (localStorage/sessionStorage)
- [ ] Implement automatic token refresh

### Project Features
- [ ] Project listing with filters
- [ ] Project creation form
- [ ] Project detail view
- [ ] Team member management
- [ ] Approval workflow UI

### String Features
- [ ] String listing with filters
- [ ] String creation (bulk)
- [ ] String detail view with hierarchy
- [ ] String editing with validation
- [ ] String export functionality

### String Registry Features
- [ ] CSV upload component
- [ ] Validation results display
- [ ] Selective import interface
- [ ] Real-time single string validation
- [ ] Error handling and user feedback

### Common Features
- [ ] Loading states
- [ ] Error handling and display
- [ ] Success notifications
- [ ] Pagination
- [ ] Search and filtering
- [ ] Export functionality

---

## 📊 Response Format Standards

### Success Response
```json
{
  "id": 123,
  "field": "value",
  ...
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Specific error"]
  }
}
```

### List Response (Paginated)
```json
{
  "count": 100,
  "next": "url",
  "previous": "url",
  "results": [...]
}
```

---

## 🔒 Security Notes

- All endpoints require JWT authentication
- Tokens expire after 60 minutes
- Rate limiting applies to all endpoints
- Use HTTPS in production
- Never expose tokens in URLs
- Implement CSRF protection for state-changing operations

---

## 📞 Support

- **Interactive Docs**: `/api/schema/swagger-ui/`
- **Schema**: `/api/schema/`
- **GitHub Issues**: Report bugs and feature requests

---

## 🔄 Recent Updates

### November 2024
- ✅ Complete API documentation for core features
- ✅ Updated Postman collection (ProjectString → String)
- ✅ Added frontend integration examples
- ✅ Documented String Registry workflows
- ✅ Added CSV format specifications
