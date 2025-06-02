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

#### 5. Bulk Create Dimensions

**POST** `/api/dimensions/bulk_create/`

Creates multiple dimensions in a single request with transaction safety.

**Request Body:**

```json
{
  "dimensions": [
    {
      "name": "Environment",
      "description": "Deployment environment",
      "type": "list",
      "status": "active",
      "parent": null
    },
    {
      "name": "Region",
      "description": "Geographic region",
      "type": "list",
      "status": "active",
      "parent": null
    }
  ]
}
```

**Response Format:**

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "name": "Environment",
      "slug": "environment",
      "description": "Deployment environment",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Region",
      "slug": "region",
      "description": "Geographic region",
      "type": "list",
      "parent": null,
      "parent_name": null,
      "status": "active",
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    }
  ],
  "errors": []
}
```

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
    "description": string,
    "value": string,
    "valid_until": string (datetime),
    "label": string,
    "utm": string,
    "dimension": number,
    "dimension_name": string,
    "dimension_parent_name": string,
    "dimension_parent": number,
    "parent": number,
    "parent_name": string,
    "parent_value": string,
    "created_by": number,
    "created_by_name": string,
    "created": string (datetime),
    "last_updated": string (datetime)
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
  "description": string,
  "value": string,
  "valid_until": string (datetime),
  "label": string,
  "utm": string,
  "dimension": number,
  "parent": number
}
```

#### 4. Update Dimension Value

**PUT/PATCH** `/api/dimension-values/{id}/`

Updates dimension value information.

**Request Body:** Same as Create Dimension Value

#### 5. Bulk Create Dimension Values

**POST** `/api/dimension-values/bulk_create/`

Creates multiple dimension values in a single request with transaction safety.

**Request Body:**

```json
{
  "dimension_values": [
    {
      "dimension": 1,
      "value": "prod",
      "label": "Production",
      "utm": "prod",
      "description": "Production environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    },
    {
      "dimension": 1,
      "value": "dev",
      "label": "Development",
      "utm": "dev",
      "description": "Development environment",
      "valid_from": "2023-01-01",
      "valid_until": null,
      "parent": null
    }
  ]
}
```

**Response Format:**

```json
{
  "success_count": 2,
  "error_count": 0,
  "results": [
    {
      "id": 1,
      "valid_from": "2023-01-01",
      "description": "Production environment",
      "value": "prod",
      "valid_until": null,
      "label": "Production",
      "utm": "prod",
      "dimension": 1,
      "dimension_name": "Environment",
      "dimension_parent_name": null,
      "dimension_parent": null,
      "parent": null,
      "parent_name": null,
      "parent_value": null,
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    },
    {
      "id": 2,
      "valid_from": "2023-01-01",
      "description": "Development environment",
      "value": "dev",
      "valid_until": null,
      "label": "Development",
      "utm": "dev",
      "dimension": 1,
      "dimension_name": "Environment",
      "dimension_parent_name": null,
      "dimension_parent": null,
      "parent": null,
      "parent_name": null,
      "parent_value": null,
      "created_by": 1,
      "created_by_name": "John Doe",
      "created": "2023-12-01T10:00:00Z",
      "last_updated": "2023-12-01T10:00:00Z"
    }
  ],
  "errors": []
}
```

**Error Response Example:**

```json
{
  "success_count": 1,
  "error_count": 1,
  "results": [
    // ... successful creations
  ],
  "errors": [
    {
      "index": 1,
      "dimension_value": "duplicate_value",
      "dimension_id": 1,
      "error": "UNIQUE constraint failed: master_data_dimensionvalue.dimension_id, master_data_dimensionvalue.value"
    }
  ]
}
```

## Workspaces API

### Base URL

```

```
