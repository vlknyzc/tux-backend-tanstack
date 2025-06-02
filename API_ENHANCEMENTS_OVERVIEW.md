# API Enhancements Overview

## 🚀 **Enhanced API Endpoints for String Generation Business Logic**

This document outlines the comprehensive API enhancements that accommodate the new string generation business logic, rule validation, and advanced naming convention management.

---

## 📋 **String API Enhancements**

### **Core Endpoints**

- `GET /api/strings/` - List strings with enhanced filtering
- `POST /api/strings/` - Create string (manual)
- `GET /api/strings/{id}/` - String detail with business logic fields
- `PUT/PATCH /api/strings/{id}/` - Update string
- `DELETE /api/strings/{id}/` - Delete string

### **🔥 New Business Logic Endpoints**

#### **1. Automatic String Generation**

```http
POST /api/strings/generate/
```

**Purpose:** Generate strings automatically using rule-based business logic

**Request Body:**

```json
{
  "submission_id": 1,
  "field_id": 2,
  "dimension_values": {
    "environment": "production",
    "region": "us-east-1",
    "cost_center": "engineering"
  },
  "parent_string_id": 3 // Optional for hierarchy
}
```

**Response:**

```json
{
  "id": 15,
  "value": "production-us-east-1-engineering",
  "is_auto_generated": true,
  "generation_metadata": {
    "generated_at": "2024-06-01T15:30:00Z",
    "rule_used": "AWS Standard",
    "dimension_values_used": {...}
  },
  "dimension_values": {...},
  "hierarchy_path": [...],
  "can_have_children": true,
  "suggested_child_field": {...}
}
```

#### **2. String Regeneration**

```http
POST /api/strings/{id}/regenerate/
```

**Purpose:** Regenerate existing string with new dimension values

**Request Body:**

```json
{
  "dimension_values": {
    "environment": "staging",
    "region": "eu-west-1"
  }
}
```

#### **3. Conflict Detection**

```http
POST /api/strings/check_conflicts/
```

**Purpose:** Check for naming conflicts before string creation

**Request Body:**

```json
{
  "rule_id": 1,
  "field_id": 2,
  "proposed_value": "test-us-east-1-eng",
  "exclude_string_id": 5 // Optional
}
```

**Response:**

```json
{
  "has_conflicts": true,
  "conflicts": [
    "String value 'test-us-east-1-eng' already exists for this rule and field",
    "Similar strings exist: test-us-east-1-engineering, test-us-west-eng"
  ],
  "proposed_value": "test-us-east-1-eng"
}
```

#### **4. Bulk Generation**

```http
POST /api/strings/bulk_generate/
```

**Purpose:** Generate multiple strings in a single atomic transaction

**Request Body:**

```json
{
  "submission_id": 1,
  "generation_requests": [
    {
      "field_id": 1,
      "dimension_values": { "env": "prod", "region": "us-east-1" }
    },
    {
      "field_id": 2,
      "dimension_values": {
        "env": "prod",
        "region": "us-east-1",
        "service": "api"
      }
    }
  ]
}
```

#### **5. Hierarchy Navigation**

```http
GET /api/strings/{id}/hierarchy/
```

**Purpose:** Get complete hierarchy path and child strings

**Response:**

```json
{
  "string_id": 5,
  "hierarchy_path": [
    {"id": 1, "value": "production", "field_level": 1},
    {"id": 5, "value": "production-api", "field_level": 2}
  ],
  "child_strings": [...],
  "can_have_children": true,
  "suggested_child_field": "database"
}
```

#### **6. Conflict Detection Endpoint**

```http
GET /api/strings/conflicts/
```

**Purpose:** Get all strings with naming conflicts

---

## ⚙️ **Rule API Enhancements**

### **Core Endpoints**

- `GET /api/rules/` - List rules with validation status
- `POST /api/rules/` - Create rule
- `GET /api/rules/{id}/` - Rule detail with configuration errors
- `PUT/PATCH /api/rules/{id}/` - Update rule
- `DELETE /api/rules/{id}/` - Delete rule

### **🔥 New Business Logic Endpoints**

#### **1. Rule Preview Generation**

```http
POST /api/rules/{id}/preview/
```

**Purpose:** Preview string generation with sample values

**Request Body:**

```json
{
  "field_id": 2,
  "sample_values": {
    "environment": "test",
    "region": "us-west-2",
    "cost_center": "platform"
  }
}
```

**Response:**

```json
{
  "rule_id": 1,
  "rule_name": "AWS Standard",
  "field_id": 2,
  "field_name": "environment",
  "sample_values": {...},
  "preview": "test-us-west-2-platform",
  "success": true
}
```

#### **2. Rule Configuration Validation**

```http
GET /api/rules/{id}/validate_configuration/
```

**Purpose:** Comprehensive rule configuration validation

**Response:**

```json
{
  "id": 1,
  "name": "AWS Standard",
  "configuration_errors": [
    "Rule details have gaps in dimension_order",
    "No rule details configured for field 'database'"
  ],
  "can_generate_for_fields": {
    "environment": true,
    "application": false
  },
  "required_dimensions_by_field": {
    "environment": {
      "dimensions": ["env", "region"],
      "generation_order": ["env", "region"]
    }
  }
}
```

#### **3. Default Rule Management**

```http
POST /api/rules/{id}/set_default/
```

**Purpose:** Set rule as platform default

```http
GET /api/rules/defaults/
```

**Purpose:** Get all default rules by platform

#### **4. Required Dimensions Query**

```http
GET /api/rules/{id}/required_dimensions/
```

**Purpose:** Get required dimensions for all fields in rule

#### **5. Active Rules Filter**

```http
GET /api/rules/active/?platform_id=1
```

**Purpose:** Get all active rules, optionally filtered by platform

---

## 🔧 **Rule Detail API Enhancements**

### **Enhanced Endpoints**

#### **1. Order Validation**

```http
POST /api/rule-details/validate_order/
```

**Purpose:** Validate dimension order for rule+field combination

**Request Body:**

```json
{
  "rule_id": 1,
  "field_id": 2
}
```

**Response:**

```json
{
  "rule_id": 1,
  "field_id": 2,
  "current_orders": [1, 2, 4],
  "expected_orders": [1, 2, 3],
  "has_gaps": true,
  "is_valid": false
}
```

---

## 📄 **Enhanced Serializers**

### **String Serializers**

#### **1. StringSerializer (Enhanced)**

**New Fields:**

- `is_auto_generated` - Whether string was auto-generated
- `generation_metadata` - JSON metadata about generation
- `dimension_values` - Current dimension values as dict
- `hierarchy_path` - Full hierarchy path
- `can_have_children` - Whether string can have children
- `suggested_child_field` - Next field for child creation
- `naming_conflicts` - Any detected conflicts

#### **2. StringGenerationRequestSerializer**

**Purpose:** Validate string generation requests
**Fields:** `submission_id`, `field_id`, `dimension_values`, `parent_string_id`

#### **3. StringRegenerationSerializer**

**Purpose:** Validate regeneration requests
**Fields:** `dimension_values`

#### **4. StringConflictCheckSerializer**

**Purpose:** Validate conflict checking requests
**Fields:** `rule_id`, `field_id`, `proposed_value`, `exclude_string_id`

#### **5. StringBulkGenerationRequestSerializer**

**Purpose:** Validate bulk generation requests
**Fields:** `submission_id`, `generation_requests[]`

### **Rule Serializers**

#### **1. RuleSerializer (Enhanced)**

**New Fields:**

- `is_default` - Whether this is platform default
- `configuration_errors` - List of validation errors
- `required_dimensions` - Required dimensions by field
- `fields_with_rules` - Fields that have rule details

#### **2. RulePreviewRequestSerializer**

**Purpose:** Validate preview generation requests
**Fields:** `field_id`, `sample_values`

#### **3. RuleValidationSerializer**

**Purpose:** Comprehensive rule validation results
**Fields:** `configuration_errors`, `can_generate_for_fields`, `required_dimensions_by_field`

#### **4. RuleDetailCreateSerializer**

**Purpose:** Enhanced validation for rule detail creation
**Enhanced Validation:** Platform consistency, duplicate checking

---

## 🔍 **Enhanced Filtering & Querying**

### **String Filters (Enhanced)**

- `rule_id` - Filter by rule
- `is_auto_generated` - Filter auto-generated strings
- `has_conflicts` - Filter strings with conflicts
- `platform_id` - Filter by platform
- `field_level` - Filter by field hierarchy level

### **Rule Filters (Enhanced)**

- `status` - Filter by rule status
- `is_default` - Filter default rules
- `platform` - Filter by platform

### **Rule Detail Filters (Enhanced)**

- `is_required` - Filter required dimensions
- `dimension_order` - Filter by order

---

## 🚀 **Usage Examples**

### **Automatic String Generation Workflow**

```javascript
// 1. Check for conflicts first
const conflictCheck = await fetch("/api/strings/check_conflicts/", {
  method: "POST",
  body: JSON.stringify({
    rule_id: 1,
    field_id: 2,
    proposed_value: "prod-us-east-1-api",
  }),
});

// 2. Generate string if no conflicts
if (!conflictCheck.has_conflicts) {
  const generateResponse = await fetch("/api/strings/generate/", {
    method: "POST",
    body: JSON.stringify({
      submission_id: 5,
      field_id: 2,
      dimension_values: {
        environment: "production",
        region: "us-east-1",
        service: "api",
      },
    }),
  });
}
```

### **Rule Configuration & Preview**

```javascript
// 1. Validate rule configuration
const validation = await fetch("/api/rules/1/validate_configuration/");

// 2. Preview with sample values
const preview = await fetch("/api/rules/1/preview/", {
  method: "POST",
  body: JSON.stringify({
    field_id: 2,
    sample_values: {
      environment: "test",
      region: "us-west-2",
    },
  }),
});

// 3. Set as default if valid
if (validation.configuration_errors.length === 0) {
  await fetch("/api/rules/1/set_default/", { method: "POST" });
}
```

### **Bulk Operations**

```javascript
// Bulk generate multiple strings
const bulkResponse = await fetch("/api/strings/bulk_generate/", {
  method: "POST",
  body: JSON.stringify({
    submission_id: 1,
    generation_requests: [
      {
        field_id: 1,
        dimension_values: { env: "prod", region: "us-east-1" },
      },
      {
        field_id: 2,
        dimension_values: { env: "prod", region: "us-east-1", service: "api" },
      },
    ],
  }),
});

console.log(`Generated ${bulkResponse.success_count} strings`);
```

---

## 🎯 **Key Benefits**

### **1. Intelligent Automation**

- Automatic string generation with validation
- Conflict detection and prevention
- Rule-based consistency enforcement

### **2. Enhanced Validation**

- Real-time configuration validation
- Preview generation for testing
- Comprehensive error reporting

### **3. Scalable Operations**

- Bulk generation for efficiency
- Atomic transactions for data integrity
- Performance-optimized queries

### **4. Business Logic Integration**

- Hierarchical string relationships
- Metadata tracking and audit trails
- Extensible rule system

### **5. Developer Experience**

- Clear error messages and validation
- Comprehensive API documentation
- Consistent response formats

This enhanced API provides a robust foundation for enterprise-grade naming convention management with intelligent automation and comprehensive business logic support! 🚀
