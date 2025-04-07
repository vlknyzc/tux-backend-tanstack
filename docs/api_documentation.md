# API Documentation

This documentation provides comprehensive information about all available API endpoints in the TUX Backend system. It is designed to help frontend developers understand and integrate with the backend services.

## Table of Contents

1. [Authentication](#authentication)
2. [Users API](#users-api)
3. [Rules API](#rules-api)
4. [Strings API](#strings-api)
5. [Dimensions API](#dimensions-api)
6. [Workspaces API](#workspaces-api)
7. [Submissions API](#submissions-api)
8. [Conventions API](#conventions-api)

## Authentication

- In development mode (DEBUG=True), most endpoints are publicly accessible
- In production, authentication is required for most endpoints
- Some endpoints require specific permissions (e.g., admin privileges)

## Common Response Formats

### Success Response Format

```json
{
    "status": "success",
    "data": { ... }
}
```

### Error Response Format

```json
{
  "detail": "Error message"
}
```

### Field-specific Error Format

```json
{
  "field_name": ["Error message"]
}
```

### Pagination Format

```json
{
    "count": number,
    "next": string (url),
    "previous": string (url),
    "results": array
}
```

## Common Status Codes

- `200 OK`: Successful GET, PUT, PATCH requests
- `201 Created`: Successful POST request
- `400 Bad Request`: Invalid data provided
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found

## Users API

### Base URL

```
/api/users/
```

### Endpoints

#### 1. List Users

**GET** `/api/users/`

Retrieves a list of all users.

**Response Format:**

```json
[
  {
    "id": number,
    "username": string,
    "email": string,
    "first_name": string,
    "last_name": string,
    "is_active": boolean,
    "date_joined": string (datetime)
  }
]
```

#### 2. Get Single User

**GET** `/api/users/{id}/`

Retrieves detailed information about a specific user.

**Response Format:**

```json
{
  "id": number,
  "username": string,
  "email": string,
  "first_name": string,
  "last_name": string,
  "is_active": boolean,
  "is_staff": boolean,
  "date_joined": string (datetime),
  "last_login": string (datetime)
}
```

#### 3. Create User

**POST** `/api/users/`

Creates a new user. Requires admin privileges.

**Request Body:**

```json
{
  "username": string (required),
  "email": string (required),
  "first_name": string,
  "last_name": string,
  "password": string (required),
  "password2": string (required),
  "is_active": boolean
}
```

#### 4. Update User

**PUT/PATCH** `/api/users/{id}/`

Updates user information.

**Request Body:**

```json
{
  "email": string,
  "first_name": string,
  "last_name": string,
  "is_active": boolean
}
```

## Rules API

### Base URL

```
/api/rules/
```

### Endpoints

#### 1. List Rules

**GET** `/api/rules/`

Retrieves a list of all rules.

**Query Parameters:**

- `platform` (number, optional): Filter by platform ID
- `field` (number, optional): Filter by field ID

**Response Format:**

```json
[
  {
    "id": number,
    "platform": number,
    "status": string,
    "name": string
  }
]
```

#### 2. Get Single Rule

**GET** `/api/rules/{id}/`

Retrieves detailed information about a specific rule.

**Response Format:** Same as List Rules

#### 3. Create Rule

**POST** `/api/rules/`

Creates a new rule.

**Request Body:**

```json
{
  "platform": number,
  "status": string,
  "name": string
}
```

#### 4. Update Rule

**PUT/PATCH** `/api/rules/{id}/`

Updates rule information.

**Request Body:** Same as Create Rule

### Rule Details API

#### Base URL

```
/api/rule-details/
```

#### 1. List Rule Details

**GET** `/api/rule-details/`

Retrieves a list of all rule details.

**Query Parameters:**

- `platform` (number, optional): Filter by platform ID
- `field` (number, optional): Filter by field ID

**Response Format:**

```json
[
  {
    "id": number,
    "rule": number,
    "rule_name": string,
    "platform_id": number,
    "platform_name": string,
    "field": number,
    "field_id": number,
    "field_name": string,
    "field_level": number,
    "next_field": string,
    "dimension": number,
    "dimension_name": string,
    "dimension_type": string,
    "dimension_order": number,
    "prefix": string,
    "suffix": string,
    "delimiter": string,
    "parent_dimension_name": string,
    "parent_dimension_id": number,
    "in_parent_field": boolean,
    "is_max_field_level": boolean
  }
]
```

#### 2. Get Single Rule Detail

**GET** `/api/rule-details/{id}/`

Retrieves detailed information about a specific rule detail.

**Response Format:** Same as List Rule Details

#### 3. Create Rule Detail

**POST** `/api/rule-details/`

Creates a new rule detail.

**Request Body:**

```json
{
  "rule": number,
  "field": number,
  "dimension": number,
  "dimension_order": number,
  "prefix": string,
  "suffix": string,
  "delimiter": string
}
```

#### 4. Update Rule Detail

**PUT/PATCH** `/api/rule-details/{id}/`

Updates rule detail information.

**Request Body:** Same as Create Rule Detail

### Nested Rules API

#### Base URL

```
/api/rules-nested/
```

#### 1. List Nested Rules

**GET** `/api/rules-nested/`

Retrieves a list of all rules with their associated details.

**Response Format:**

```json
[
  {
    "id": number,
    "name": string,
    "field_details": [
      {
        // Same structure as Rule Detail
      }
    ]
  }
]
```

## Strings API

### Base URL

```
/api/strings/
```

### Endpoints

#### 1. List Strings

**GET** `/api/strings/`

Retrieves a list of all strings.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `field` (number, optional): Filter by field ID
- `parent` (number, optional): Filter by parent string ID

**Response Format:**

```json
[
  {
    "id": number,
    "submission": number,
    "last_updated": string (datetime),
    "created": string (datetime),
    "field": number,
    "field_name": string,
    "field_level": number,
    "platform_id": number,
    "platform_name": string,
    "string_uuid": string,
    "value": string,
    "parent": number,
    "parent_uuid": string
  }
]
```

#### 2. Get Single String

**GET** `/api/strings/{id}/`

Retrieves detailed information about a specific string.

**Response Format:** Same as List Strings

#### 3. Create String

**POST** `/api/strings/`

Creates a new string.

**Request Body:**

```json
{
  "submission": number,
  "field": number,
  "string_uuid": string,
  "value": string,
  "parent": number,
  "parent_uuid": string
}
```

#### 4. Update String

**PUT/PATCH** `/api/strings/{id}/`

Updates string information.

**Request Body:** Same as Create String

### String Details API

#### Base URL

```
/api/string-details/
```

#### 1. List String Details

**GET** `/api/string-details/`

Retrieves a list of all string details.

**Query Parameters:**

- `string` (number, optional): Filter by string ID
- `rule` (number, optional): Filter by rule ID
- `dimension_value` (number, optional): Filter by dimension value ID

**Response Format:**

```json
[
  {
    "id": number,
    "submission_name": string,
    "string": number,
    "dimension_value_id": number,
    "dimension_value": string,
    "dimension_value_label": string,
    "dimension_value_freetext": string,
    "dimension_id": number,
    "created": string (datetime),
    "last_updated": string (datetime)
  }
]
```

#### 2. Get Single String Detail

**GET** `/api/string-details/{id}/`

Retrieves detailed information about a specific string detail.

**Response Format:** Same as List String Details

#### 3. Create String Detail

**POST** `/api/string-details/`

Creates a new string detail.

**Request Body:**

```json
{
  "string": number,
  "rule": number,
  "dimension_value_id": number,
  "dimension_value_freetext": string
}
```

**Notes:**

- For mastered dimensions:
  - `dimension_value_id` is required
  - `dimension_value_freetext` cannot be set
- For free text dimensions:
  - `dimension_value_id` cannot be set
  - `dimension_value_freetext` is used

#### 4. Update String Detail

**PUT/PATCH** `/api/string-details/{id}/`

Updates string detail information.

**Request Body:** Same as Create String Detail

## Dimensions API

### Base URL

```
/api/dimensions/
```

### Endpoints

#### 1. List Dimensions

**GET** `/api/dimensions/`

Retrieves a list of all dimensions.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `dimension_type` (string, optional): Filter by dimension type

**Response Format:**

```json
[
  {
    "id": number,
    "definition": string,
    "dimension_type": string,
    "dimension_type_label": string,
    "name": string,
    "parent": number,
    "parent_name": string,
    "status": string
  }
]
```

#### 2. Get Single Dimension

**GET** `/api/dimensions/{id}/`

Retrieves detailed information about a specific dimension.

**Response Format:** Same as List Dimensions

#### 3. Create Dimension

**POST** `/api/dimensions/`

Creates a new dimension.

**Request Body:**

```json
{
  "definition": string,
  "dimension_type": string,
  "name": string,
  "parent": number,
  "status": string
}
```

#### 4. Update Dimension

**PUT/PATCH** `/api/dimensions/{id}/`

Updates dimension information.

**Request Body:** Same as Create Dimension

### Dimension Values API

#### Base URL

```
/api/dimension-values/
```

#### 1. List Dimension Values

**GET** `/api/dimension-values/`

Retrieves a list of all dimension values.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID
- `dimension` (number, optional): Filter by dimension ID

**Response Format:**

```json
[
  {
    "id": number,
    "valid_from": string (datetime),
    "definition": string,
    "dimension_value": string,
    "valid_until": string (datetime),
    "dimension_value_label": string,
    "dimension_value_utm": string,
    "dimension": number,
    "dimension_name": string,
    "dimension_parent_name": string,
    "dimension_parent": number,
    "parent": number,
    "parent_name": string,
    "parent_value": string
  }
]
```

#### 2. Get Single Dimension Value

**GET** `/api/dimension-values/{id}/`

Retrieves detailed information about a specific dimension value.

**Response Format:** Same as List Dimension Values

#### 3. Create Dimension Value

**POST** `/api/dimension-values/`

Creates a new dimension value.

**Request Body:**

```json
{
  "valid_from": string (datetime),
  "definition": string,
  "dimension_value": string,
  "valid_until": string (datetime),
  "dimension_value_label": string,
  "dimension_value_utm": string,
  "dimension": number,
  "parent": number
}
```

#### 4. Update Dimension Value

**PUT/PATCH** `/api/dimension-values/{id}/`

Updates dimension value information.

**Request Body:** Same as Create Dimension Value

## Workspaces API

### Base URL

```
/api/workspaces/
```

### Endpoints

#### 1. List Workspaces

**GET** `/api/workspaces/`

Retrieves a list of all workspaces.

**Query Parameters:**

- `id` (number, optional): Filter by workspace ID

**Response Format:**

```json
[
  {
    "id": number,
    "name": string,
    "logo": string (url),
    "created_by": number,
    "created": string (datetime),
    "last_updated": string (datetime)
  }
]
```

#### 2. Get Single Workspace

**GET** `/api/workspaces/{id}/`

Retrieves detailed information about a specific workspace.

**Response Format:** Same as List Workspaces

#### 3. Create Workspace

**POST** `/api/workspaces/`

Creates a new workspace.

**Request Body:**

```json
{
  "name": string,
  "logo": string (url),
  "created_by": number
}
```

#### 4. Update Workspace

**PUT/PATCH** `/api/workspaces/{id}/`

Updates workspace information.

**Request Body:** Same as Create Workspace

### Platforms API

#### Base URL

```
/api/platforms/
```

#### 1. List Platforms

**GET** `/api/platforms/`

Retrieves a list of all platforms.

**Response Format:**

```json
[
  {
    "id": number,
    "platform_type": string,
    "name": string
  }
]
```

#### 2. Get Single Platform

**GET** `/api/platforms/{id}/`

Retrieves detailed information about a specific platform.

**Response Format:** Same as List Platforms

#### 3. Create Platform

**POST** `/api/platforms/`

Creates a new platform.

**Request Body:**

```json
{
  "platform_type": string,
  "name": string
}
```

#### 4. Update Platform

**PUT/PATCH** `/api/platforms/{id}/`

Updates platform information.

**Request Body:** Same as Create Platform

### Platform Fields API

#### Base URL

```
/api/fields/
```

#### 1. List Fields

**GET** `/api/fields/`

Retrieves a list of all platform fields.

**Response Format:**

```json
[
  {
    "id": number,
    "platform": number,
    "platform_name": string,
    "name": string,
    "field_level": number,
    "next_field": number,
    "next_field_name": string
  }
]
```

#### 2. Get Single Field

**GET** `/api/fields/{id}/`

Retrieves detailed information about a specific field.

**Response Format:** Same as List Fields

#### 3. Create Field

**POST** `/api/fields/`

Creates a new field.

**Request Body:**

```json
{
  "platform": number,
  "name": string,
  "field_level": number,
  "next_field": number
}
```

#### 4. Update Field

**PUT/PATCH** `/api/fields/{id}/`

Updates field information.

**Request Body:** Same as Create Field

## Submissions API

### Base URL

```
/api/submissions/
```

### Endpoints

#### 1. List Submissions

**GET** `/api/submissions/`

Retrieves a list of all submissions.

**Query Parameters:**

- `workspace` (number, optional): Filter by workspace ID

**Response Format:**

```json
[
  {
    "id": number,
    "name": string,
    "description": string,
    "status": string
  }
]
```

#### 2. Get Single Submission

**GET** `/api/submissions/{id}/`

Retrieves detailed information about a specific submission.

**Response Format:** Same as List Submissions

#### 3. Create Submission

**POST** `/api/submissions/`

Creates a new submission.

**Request Body:**

```json
{
  "name": string,
  "description": string,
  "status": string
}
```

#### 4. Update Submission

**PUT/PATCH** `/api/submissions/{id}/`

Updates submission information.

**Request Body:** Same as Create Submission

## Authentication and Security

### Development vs Production

- In development mode (DEBUG=True):
  - Most endpoints are publicly accessible
  - Authentication is not required for most operations
- In production mode:
  - Most endpoints require authentication
  - Some endpoints require specific permissions (e.g., admin privileges)
  - JWT authentication is used

### Common Headers

For authenticated requests in production:

```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### Error Handling

All endpoints follow standard HTTP status codes:

- `200 OK`: Successful GET, PUT, PATCH requests
- `201 Created`: Successful POST request
- `400 Bad Request`: Invalid data provided
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

### Pagination

List endpoints return paginated results in the following format:

```json
{
  "count": number,
  "next": string (url),
  "previous": string (url),
  "results": array
}
```

## Data Relationships

### Workspace Hierarchy

- Workspaces contain multiple platforms
- Each platform has multiple fields
- Fields can have parent-child relationships

### Rules and Dimensions

- Rules are associated with platforms and fields
- Dimensions can have parent-child relationships
- Dimension values are associated with dimensions

### Strings and Submissions

- Strings are associated with submissions and fields
- String details link strings with rules and dimension values

## Best Practices

### Rate Limiting

- Production API has rate limiting enabled
- Implement appropriate caching on the frontend
- Use bulk operations where available

### Error Handling

- Always check response status codes
- Handle validation errors appropriately
- Implement proper error messages in the UI

### Data Validation

- Validate data on the frontend before submission
- Handle required fields appropriately
- Follow the data type specifications in the API

### Security

- Never store sensitive data in client-side storage
- Always use HTTPS in production
- Implement proper token management
- Handle session expiration gracefully

## Getting Started

1. **Authentication**

   - Obtain JWT token through authentication endpoint
   - Include token in all subsequent requests

2. **Workspace Setup**

   - Create a workspace
   - Add platforms and fields
   - Configure dimensions and rules

3. **Data Management**

   - Create submissions
   - Add strings and string details
   - Manage dimension values

4. **Error Handling**
   - Implement proper error handling
   - Show appropriate error messages
   - Handle network issues gracefully

## Support

For additional support or questions:

- Check the API status endpoint
- Contact the backend team for technical issues
- Refer to the internal documentation for detailed information
